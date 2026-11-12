"""Duration (hazard-rate) estimate of the one-year transition matrix from monthly ratings (step 2 of PREREGISTRATION.md)."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
FIRST, LAST = pd.Timestamp(1985, 12, 31), pd.Timestamp(2016, 12, 31)   # same window as the cohort matrix


def to_grade(r):
    if r in ("D", "SD"):
        return "D"
    if r in ("N.M.", "Suspended"):
        return "NR"
    letter = r.rstrip("+-")
    return "CCC" if letter in ("CCC", "CC", "C") else letter


df = pd.read_parquet(ROOT / "data" / "sp_ratings.parquet")
df["grade"] = df["splticrm"].map(to_grade)
df = df[(df["grade"] != "NR") & (df["datadate"] >= FIRST) & (df["datadate"] <= LAST)]
df = df.sort_values(["gvkey", "datadate"])

# default is absorbing: keep nothing after an issuer's first D
first_d = df[df["grade"] == "D"].groupby("gvkey")["datadate"].min()
df = df[df["datadate"] <= df["gvkey"].map(first_d).fillna(LAST)]

# month-to-month steps; a gap in the monthly record (NR) is treated as censoring
df["m"] = df["datadate"].dt.year * 12 + df["datadate"].dt.month
nxt = df.groupby("gvkey")[["grade", "m"]].shift(-1)
step = df.assign(to=nxt["grade"], gap=nxt["m"] - df["m"])
step = step[(step["gap"] == 1) & (step["grade"] != "D")]

moves = pd.crosstab(step["grade"], step["to"]).reindex(index=GRADES[:-1], columns=GRADES, fill_value=0)
years_at_risk = step.groupby("grade").size().reindex(GRADES[:-1]) / 12

# generator: off-diagonal intensity = transitions / years at risk; D row is zero
gen = np.zeros((8, 8))
gen[:7, :] = moves.values / years_at_risk.values[:, None]
for i in range(7):
    gen[i, i] = 0
    gen[i, i] = -gen[i].sum()
dur = pd.DataFrame(expm(gen), index=GRADES, columns=GRADES).iloc[:7]

assert np.allclose(gen.sum(axis=1), 0) and np.allclose(dur.sum(axis=1), 1) and (dur.values >= 0).all()
assert (dur["D"].diff().dropna() >= 0).all(), "default rate not monotone in grade"

cohort = pd.read_csv(OUT / "avg_matrix_nr_adjusted_pct.csv", index_col=0)
compare = pd.DataFrame({"cohort_pd_pct": cohort["D"], "duration_pd_pct": 100 * dur["D"]})
compare["ratio"] = compare["duration_pd_pct"] / compare["cohort_pd_pct"].replace(0, np.nan)

(100 * dur).round(3).to_csv(OUT / "duration_matrix_pct.csv")
compare.round(4).to_csv(OUT / "cohort_vs_duration_pd.csv")

print("issuer-years at risk:", round(years_at_risk.sum()), "| monthly grade changes:",
      int(moves.values.sum() - np.trace(moves.values[:, :7])))
print("\nDuration one-year matrix (%):")
print((100 * dur).round(2).to_string())
print("\nOne-year default probability, cohort vs duration (%):")
print(compare.round(4).to_string())
print("\nLargest absolute cell difference, duration minus cohort (pct points):",
      round(float((100 * dur - cohort).abs().values.max()), 2))
