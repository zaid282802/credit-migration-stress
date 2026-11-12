"""Credit-cycle index Z_t, macro regression, and the out-of-time default test (see PREREGISTRATION.md)."""
from pathlib import Path
import io
import os
import urllib.request
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar, brentq
from scipy.stats import norm
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
START = GRADES[:-1]
SPEC = ["BB", "B", "CCC"]
EST_START = int(os.environ.get("EST_START", 1985))  # 1998 = robustness run (see PREREGISTRATION.md)
TAG = "" if EST_START == 1985 else f"_est{EST_START}"
EST = range(EST_START, 2007)     # estimation cohorts (the file has 1-2 issuers per year before Dec 1985)
OOT = range(2007, 2016)          # out-of-time cohorts
DEF_EST = range(1998, 2007)      # cohorts with reliable default records, inside the estimation window

counts = pd.read_pickle(OUT / "yearly_counts.pkl")


# ---------- macro data (FRED) ----------
def fred(series):
    path = ROOT / "data" / f"fred_{series}.csv"
    if not path.exists():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
        path.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    return pd.to_numeric(s, errors="coerce").dropna()


unrate, gdp, baa, gs10 = fred("UNRATE"), fred("GDPC1"), fred("BAA"), fred("GS10")
macro = pd.DataFrame({
    "d_unrate": unrate[unrate.index.month == 12].groupby(lambda d: d.year).last().diff(),
    "gdp_growth": 100 * gdp[gdp.index.month == 10].groupby(lambda d: d.year).last().pct_change(),
    "baa_spread": (baa - gs10).groupby(lambda d: d.year).mean(),
})


# ---------- matrices ----------
def matrix(years, merge_default):
    c = sum(counts[t] for t in years)[GRADES]
    if merge_default:
        c = c.assign(CCC=c["CCC"] + c["D"]).drop(columns="D")
    return c.div(c.sum(axis=1), axis=0), c


def thresholds(p):
    """Upper normal thresholds of each bin, bins ordered worst to best."""
    cum = p.iloc[:, ::-1].cumsum(axis=1).clip(1e-12, 1 - 1e-12)
    return norm.ppf(cum.values)[:, :-1]                      # last upper bound is +inf


def probs(x, z, rho):
    """Transition probabilities given Z = z; columns ordered worst to best. Positive z is a good year."""
    upper = norm.cdf((x - np.sqrt(rho) * z) / np.sqrt(1 - rho))
    upper = np.hstack([upper, np.ones((len(x), 1))])
    return np.diff(np.hstack([np.zeros((len(x), 1)), upper]), axis=1)


p_mig, _ = matrix(EST, merge_default=True)
x_mig = thresholds(p_mig)


def fit_z(t, rho):
    n = counts[t][GRADES]
    n = n.assign(CCC=n["CCC"] + n["D"]).drop(columns="D").iloc[:, ::-1].values
    nll = lambda z: -(n * np.log(probs(x_mig, z, rho).clip(1e-12))).sum()
    return minimize_scalar(nll, bounds=(-6, 6), method="bounded").x


def z_series(rho, years):
    return pd.Series({t: fit_z(t, rho) for t in years})


rho = brentq(lambda r: z_series(r, EST).var() - 1, 0.005, 0.5, xtol=1e-4)
z = z_series(rho, list(EST) + list(OOT))
z.index = z.index + 1                                        # index by the year the transitions happen
z.name = "Z"

# ---------- regression on macro, estimation window only ----------
est_years = [t + 1 for t in EST]
oot_years = [t + 1 for t in OOT]
X = sm.add_constant(macro[["d_unrate", "gdp_growth", "baa_spread"]])
ols = sm.OLS(z.loc[est_years], X.loc[est_years]).fit()
z_hat = ols.predict(X.loc[oot_years])

# ---------- default probabilities ----------
p_def, _ = matrix(DEF_EST, merge_default=False)
x_def = thresholds(p_def.loc[SPEC])                          # thresholds for BB, B, CCC rows; first bin is D


def spec_default_rate(t, zval):
    """Speculative-grade default rate (%) for cohort t, given the cycle value in year t+1."""
    c = counts[t][GRADES].loc[SPEC]
    w = c.sum(axis=1) / c.values.sum()
    pd_g = probs(x_def, zval, rho)[:, 0] if zval is not None else p_def.loc[SPEC, "D"].values
    return 100 * float(w @ pd_g)


def actual(t):
    c = counts[t][GRADES].loc[SPEC]
    return 100 * c["D"].sum() / c.values.sum()


oot = pd.DataFrame({
    "actual": [actual(t) for t in OOT],
    "macro_model": [spec_default_rate(t, z_hat.loc[t + 1]) for t in OOT],
    "fitted_z": [spec_default_rate(t, z.loc[t + 1]) for t in OOT],
    "through_the_cycle": [spec_default_rate(t, None) for t in OOT],
}, index=oot_years)
mae = (oot[["macro_model", "fitted_z", "through_the_cycle"]].sub(oot["actual"], axis=0)).abs().mean()

# ---------- checks ----------
# averaging the conditional matrix over Z ~ N(0,1) must return the average matrix
nodes, wts = np.polynomial.hermite_e.hermegauss(64)
integrated = sum(w * probs(x_mig, zz, rho) for zz, w in zip(nodes, wts)) / wts.sum()
assert np.allclose(integrated, p_mig.iloc[:, ::-1].values, atol=1e-6), "E[P(Z)] must equal the average matrix"
assert abs(z.loc[est_years].var() - 1) < 1e-2
assert spec_default_rate(2008, -2) > spec_default_rate(2008, 0) > spec_default_rate(2008, 2)

z.round(3).to_csv(OUT / f"cycle_index{TAG}.csv", header=True)
oot.round(2).to_csv(OUT / f"out_of_time_default_rates{TAG}.csv")
pd.Series({"rho": rho, **ols.params.add_prefix("coef_"), **ols.tvalues.add_prefix("t_"),
           "r2": ols.rsquared, "n_obs": ols.nobs, **mae.add_prefix("oot_mae_")}).round(4).to_csv(OUT / f"model_summary{TAG}.csv", header=False)

print(f"rho = {rho:.4f}")
print("\nCycle index Z by transition year (negative = bad year):")
print(z.round(2).to_string())
print("\nRegression of Z on macro, transition years 1986-2007:")
print(ols.summary().tables[1])
print(f"R2 = {ols.rsquared:.3f}, n = {int(ols.nobs)}")
print("\nOut-of-time speculative-grade default rates (%):")
print(oot.round(2).to_string())
print("\nMean absolute error, 2008-2016 (pct points):")
print(mae.round(3).to_string())
