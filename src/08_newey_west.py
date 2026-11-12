"""Newey-West (HAC) standard errors for the macro regression in 03_cycle_index.py (post-hoc check, see PREREGISTRATION.md)."""
from pathlib import Path
import contextlib
import io
import runpy
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

ROOT = Path(__file__).resolve().parents[1]
with contextlib.redirect_stdout(io.StringIO()):
    m = runpy.run_path(str(ROOT / "src" / "03_cycle_index.py"))
ols, z, X, est_years = m["ols"], m["z"], m["X"], m["est_years"]
y, x = z.loc[est_years], X.loc[est_years]

resid = ols.resid
rows = {"OLS": ols.tvalues}
for lag in (1, 2, 3):
    rows[f"Newey-West, {lag} lag{'s' if lag > 1 else ''}"] = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": lag}).tvalues
table = pd.DataFrame(rows).T[["const", "d_unrate", "gdp_growth", "baa_spread"]]

ac1 = resid.autocorr(1)
assert (sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 2}).params - ols.params).abs().max() < 1e-12

table.round(2).to_csv(ROOT / "results" / "regression_tstats_hac.csv")
print(f"n = {int(ols.nobs)} | residual lag-1 autocorrelation {ac1:+.2f} | Durbin-Watson {durbin_watson(resid):.2f}")
print("t-statistics (coefficients unchanged):")
print(table.round(2).to_string())
