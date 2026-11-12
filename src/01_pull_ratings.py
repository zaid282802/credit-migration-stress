"""One WRDS pull (2026-11-12): S&P long-term issuer ratings, Compustat adsprate.

Single connection, single query, three columns. Do not re-run if data/sp_ratings.parquet exists.
"""
import os, sys
from pathlib import Path
import pandas as pd
import psycopg2

OUT = Path(__file__).resolve().parents[1] / "data" / "sp_ratings.parquet"
if OUT.exists():
    sys.exit(f"{OUT} already exists; not pulling again")

# username from pgpass (the password is read by libpq itself, never by this script)
pgpass = Path(os.environ["APPDATA"]) / "postgresql" / "pgpass.conf"
user = next(l.split(":")[3] for l in pgpass.read_text().splitlines() if "wrds" in l)

con = psycopg2.connect(host="wrds-pgdata.wharton.upenn.edu", port=9737, dbname="wrds",
                       user=user, sslmode="require", connect_timeout=120)
try:
    df = pd.read_sql(
        "select gvkey, datadate, splticrm from comp.adsprate where splticrm is not null", con)
finally:
    con.close()

df["datadate"] = pd.to_datetime(df["datadate"])
df.to_parquet(OUT, index=False)
print(len(df), "rows |", df.gvkey.nunique(), "issuers |", df.datadate.min().date(), "to", df.datadate.max().date())
print(df.splticrm.value_counts().head(25).to_string())
