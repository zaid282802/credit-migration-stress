"""External check: yearly speculative-grade default rates against S&P's published study (PREREGISTRATION.md, sanity checks)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

# S&P Global Ratings, "Default, Transition, and Recovery: 2025 Annual Global Corporate Default And
# Rating Transition Study" (18 Mar 2026), Table 5, column "U.S. and tax havens" (%).
SP_US = {
    1986: 5.81, 1987: 2.87, 1988: 3.92, 1989: 4.36, 1990: 7.94, 1991: 10.71, 1992: 6.07, 1993: 2.40,
    1994: 2.22, 1995: 3.66, 1996: 1.86, 1997: 2.18, 1998: 3.26, 1999: 5.34, 2000: 7.39, 2001: 10.54,
    2002: 7.24, 2003: 5.60, 2004: 2.44, 2005: 2.02, 2006: 1.37, 2007: 1.02, 2008: 4.30, 2009: 11.79,
    2010: 3.46, 2011: 2.15, 2012: 2.65, 2013: 2.19, 2014: 1.61, 2015: 2.86, 2016: 5.20,
}

ours = pd.read_csv(OUT / "yearly_default_rates.csv").set_index("default_year")["spec_default_rate_pct"]
cmp = pd.DataFrame({"ours": ours, "sp_us": pd.Series(SP_US)}).dropna()
cmp["diff"] = cmp["ours"] - cmp["sp_us"]
cmp["ratio"] = cmp["ours"] / cmp["sp_us"]


def stats(c):
    return pd.Series({
        "n_years": len(c), "corr": c["ours"].corr(c["sp_us"]), "mean_ours": c["ours"].mean(),
        "mean_sp_us": c["sp_us"].mean(), "mean_abs_diff": c["diff"].abs().mean(), "median_ratio": c["ratio"].median(),
    })


summary = pd.DataFrame({"1986-1998": stats(cmp.loc[:1998]), "1999-2016": stats(cmp.loc[1999:]),
                        "2008-2016 (out-of-time years)": stats(cmp.loc[2008:])}).T

assert len(cmp) == 31
cmp.round(2).to_csv(OUT / "external_check_sp.csv")
summary.round(3).to_csv(OUT / "external_check_summary.csv")
print(cmp.round(2).to_string())
print()
print(summary.round(3).to_string())
