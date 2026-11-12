"""Annual cohort transition matrices from S&P issuer ratings (definitions in PREREGISTRATION.md)."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
STATES = GRADES + ["NR"]
SPEC = ["BB", "B", "CCC"]


def to_grade(r):
    if r in ("D", "SD"):
        return "D"
    if r in ("N.M.", "Suspended"):
        return "NR"
    letter = r.rstrip("+-")
    return "CCC" if letter in ("CCC", "CC", "C") else letter


df = pd.read_parquet(ROOT / "data" / "sp_ratings.parquet")
df["grade"] = df["splticrm"].map(to_grade)
assert set(df["grade"]) <= set(STATES), set(df["grade"]) - set(STATES)
df = df[df["grade"] != "NR"].sort_values(["gvkey", "datadate"])
df["year"] = df["datadate"].dt.year
df["month"] = df["datadate"].dt.month

# first default date per issuer (default is absorbing)
first_d = df[df["grade"] == "D"].groupby("gvkey")["datadate"].min()

dec = df[df["month"] == 12].set_index(["gvkey", "year"])["grade"]

counts = {}
for t in range(1985, 2016):
    start = dec.xs(t, level="year")
    start = start[start != "D"]                       # cohort: rated, not in default
    end = dec.xs(t + 1, level="year").reindex(start.index).fillna("NR")
    d = first_d.reindex(start.index)
    defaulted = (d > pd.Timestamp(t, 12, 31)) & (d <= pd.Timestamp(t + 1, 12, 31))
    end = end.where(~defaulted, "D")
    counts[t] = pd.crosstab(start, end).reindex(index=GRADES[:-1], columns=STATES, fill_value=0)

total = sum(counts.values())
raw = total.div(total.sum(axis=1), axis=0)
adj = total[GRADES].div(total[GRADES].sum(axis=1), axis=0)          # NR-adjusted

# checks
assert np.allclose(raw.sum(axis=1), 1) and np.allclose(adj.sum(axis=1), 1)
pd_by_grade = adj["D"]
assert (pd_by_grade.diff().dropna() >= 0).all(), "default rate not monotone in grade"

yearly = pd.DataFrame({
    "cohort_year": list(counts),
    "n_issuers": [c.values.sum() for c in counts.values()],
    "n_spec": [c.loc[SPEC].values.sum() for c in counts.values()],
    "spec_defaults": [c.loc[SPEC, "D"].sum() for c in counts.values()],
    "ig_defaults": [c.loc[["AAA", "AA", "A", "BBB"], "D"].sum() for c in counts.values()],
})
yearly["default_year"] = yearly["cohort_year"] + 1
yearly["spec_default_rate_pct"] = 100 * yearly["spec_defaults"] / (
    yearly["n_spec"] - [c.loc[SPEC, "NR"].sum() for c in counts.values()])

(100 * raw).round(2).to_csv(OUT / "avg_matrix_with_nr_pct.csv")
(100 * adj).round(2).to_csv(OUT / "avg_matrix_nr_adjusted_pct.csv")
total.to_csv(OUT / "transition_counts_1985_2015.csv")
yearly.round(2).to_csv(OUT / "yearly_default_rates.csv", index=False)
pd.to_pickle(counts, OUT / "yearly_counts.pkl")

print("issuer-years:", int(total.values.sum()), "| cohorts 1985-2015")
print("\nAverage 1-year matrix, NR-adjusted (%):")
print((100 * adj).round(2).to_string())
print("\nNR share by starting grade (%):")
print((100 * raw["NR"]).round(1).to_string())
print("\nSpeculative-grade default rate by default year (%):")
print(yearly.set_index("default_year")["spec_default_rate_pct"].round(2).to_string())
