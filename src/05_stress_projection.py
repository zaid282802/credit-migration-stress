"""Default and downgrade probabilities under the Fed's severely adverse scenario (step 6 of PREREGISTRATION.md)."""
from pathlib import Path
import contextlib
import io
import runpy
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BRIDGE = 0.64            # Baa spread minus the Fed's BBB spread, 1988-2007 average
COHORT = 2015            # grade mix used for portfolio-level rates

with contextlib.redirect_stdout(io.StringIO()):
    m = runpy.run_path(str(ROOT / "src" / "03_cycle_index.py"))
ols, macro, probs, thresholds, matrix = m["ols"], m["macro"], m["probs"], m["thresholds"], m["matrix"]
TAG, EST = m["TAG"], m["EST"]
rho, z, counts, GRADES, START, SPEC, DEF_EST = m["rho"], m["z"], m["counts"], m["GRADES"], m["START"], m["SPEC"], m["DEF_EST"]

# ---------- scenario -> regressors ----------
sc = pd.read_csv(ROOT / "data" / "fed_2025_severely_adverse.csv")
hist = pd.read_csv(ROOT / "data" / "fed_2025_historic.csv")
sc["year"] = sc["Date"].str[:4].astype(int)
sc["q"] = sc["Date"].str[-1].astype(int)
sc = sc[sc["year"].isin([2025, 2026, 2027])]
q4_unemp = sc[sc["q"] == 4].set_index("year")["Unemployment rate"]
q4_unemp.loc[2024] = hist.loc[hist["Date"] == "2024 Q4", "Unemployment rate"].iloc[0]
X = pd.DataFrame({
    "const": 1.0,
    "d_unrate": q4_unemp.sort_index().diff().dropna(),
    "gdp_growth": 100 * ((1 + sc["Real GDP growth"] / 100) ** 0.25).groupby(sc["year"]).prod() - 100,
    "baa_spread": (sc["BBB corporate yield"] - sc["10-year Treasury yield"]).groupby(sc["year"]).mean() + BRIDGE,
})
z_scen = ols.predict(X[ols.params.index])

# ---------- conditional matrices ----------
p_def, _ = matrix(DEF_EST, merge_default=False)          # 1998-2006 average, defaults recorded
x_all = thresholds(p_def)
w_spec = counts[COHORT][GRADES].loc[SPEC].sum(axis=1)
w_spec = (w_spec / w_spec.sum()).values


def conditional(zval):
    """One-year matrix given the cycle value; None returns the through-the-cycle average."""
    if zval is None:
        return p_def
    return pd.DataFrame(probs(x_all, zval, rho)[:, ::-1], index=START, columns=GRADES)


def summary(zval):
    p = conditional(zval)
    return pd.Series({
        "Z": np.nan if zval is None else zval,
        "pd_BBB": 100 * p.loc["BBB", "D"], "pd_BB": 100 * p.loc["BB", "D"],
        "pd_B": 100 * p.loc["B", "D"], "pd_CCC": 100 * p.loc["CCC", "D"],
        "spec_default_rate": 100 * float(w_spec @ p.loc[SPEC, "D"].values),
        "BBB_to_spec_or_default": 100 * p.loc["BBB", ["BB", "B", "CCC", "D"]].sum(),
        "A_downgrade": 100 * p.loc["A", ["BBB", "BB", "B", "CCC", "D"]].sum(),
    })


z_worst = z.loc[EST[0] + 1:2007].min()
rows = {"through_the_cycle": summary(None), f"worst_fitted_year_{z.loc[EST[0] + 1:2007].idxmin()}": summary(z_worst)}
rows.update({f"severely_adverse_{y}": summary(z_scen.loc[y]) for y in z_scen.index})
table = pd.DataFrame(rows).T

# ---------- checks ----------
for zz in (None, z_worst, *z_scen):
    assert np.allclose(conditional(zz).sum(axis=1), 1)
assert table.loc[f"worst_fitted_year_{z.loc[EST[0] + 1:2007].idxmin()}", "spec_default_rate"] > table.loc["through_the_cycle", "spec_default_rate"]
in_sample = macro.loc[EST[0] + 1:2007, "baa_spread"]

X.round(2).to_csv(OUT / f"scenario_regressors{TAG}.csv")
table.round(2).to_csv(OUT / f"stress_projection{TAG}.csv")

print("Scenario regressors:")
print(X.round(2).to_string())
print(f"\nBaa spread in the estimation window: {in_sample.min():.2f} to {in_sample.max():.2f}")
print(f"Fitted Z in the estimation window: {z.loc[EST[0] + 1:2007].min():.2f} to {z.loc[EST[0] + 1:2007].max():.2f}")
print("\nProjection (%; grade mix of the 2015 cohort):")
print(table.round(2).to_string())
ttc = table.loc["through_the_cycle", "spec_default_rate"]
print(f"\nH3 ratio, peak scenario year over through-the-cycle: {table.filter(like='severely', axis=0)['spec_default_rate'].max() / ttc:.2f}")
print(f"Worst fitted year over through-the-cycle: {table.iloc[1]['spec_default_rate'] / ttc:.2f}")
