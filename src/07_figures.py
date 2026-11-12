"""Figure for the write-up: cycle index, and yearly default rates against S&P."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
z = pd.read_csv(ROOT / "results" / "cycle_index.csv", index_col=0)["Z"]
chk = pd.read_csv(ROOT / "results" / "external_check_sp.csv", index_col=0)
oot = pd.read_csv(ROOT / "results" / "out_of_time_default_rates.csv", index_col=0)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.1))
ax[0].bar(z.index, z.values, color="#1f4e78")
ax[0].axvline(2007.5, color="grey", ls="--", lw=0.8)
ax[0].set_title("Credit-cycle index Z (negative = bad year)", fontsize=9)
ax[1].plot(chk.index, chk["sp_us"], color="grey", label="S&P, U.S.")
ax[1].plot(chk.index, chk["ours"], color="#1f4e78", label="This study")
ax[1].set_title("Speculative-grade default rate (%)", fontsize=9)
ax[1].legend(fontsize=7, frameon=False)
for col, lab, c, ls in [("actual", "Actual", "black", "-"), ("macro_model", "Macro model", "#963c32", "-"),
                        ("through_the_cycle", "Long-run average", "grey", "--")]:
    ax[2].plot(oot.index, oot[col], color=c, ls=ls, label=lab)
ax[2].set_title("Out of time, 2008 to 2016 (%)", fontsize=9)
ax[2].legend(fontsize=7, frameon=False)
for a in ax:
    a.tick_params(labelsize=7)
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(ROOT / "report" / "figure1.pdf")
