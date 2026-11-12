# Rating migration and default probability under stress

How do corporate default and downgrade probabilities move with the credit cycle, and what does a severely adverse scenario imply for them? The hypotheses were written down before any model was fitted ([PREREGISTRATION.md](PREREGISTRATION.md)); every result, including the failed one, is in [RESULTS_LOG.md](RESULTS_LOG.md). Four-page write-up: [report/credit_migration_stress.pdf](report/credit_migration_stress.pdf).

## Results

| | |
|---|---|
| Data | 702,168 monthly S&P issuer ratings, 5,972 issuers; 56,869 issuer-years (1985 to 2015 cohorts) |
| One-year default rate (cohort method) | BBB 0.16%, BB 0.58%, B 3.55%, CCC 23.70% |
| Credit-cycle index, worst years | 2002 (-2.08), 2001 (-1.92), 2009 (-1.79) |
| Macro regression, in sample (1986 to 2007) | R2 = 0.82; only the Baa spread is significant (t = -7.8) |
| Out of time (2008 to 2016), mean absolute error | macro model 4.97 vs through-the-cycle average 2.34 percentage points |

**The macro model failed out of time.** It over-predicted defaults in every year after 2008: spreads stayed wide after the crisis while defaults fell. The cycle factor itself is real (fitted Z beats the average), but the link from macro data to the factor did not hold.

**The severely adverse projection is an extrapolation.** The Fed's 2025 scenario implies a 24.9% speculative-grade default rate, but its spread (5.24) is far outside the fitted range (1.51 to 3.19). Repeating the worst fitted year (2002) gives 7.7%, 1.74 times the average. Both conclusions hold when the model is refitted on 1998 to 2006 only.

**Cohort vs duration method.** The monthly hazard-rate estimate gives lower default rates for BBB to B and a higher one for CCC (32.0% vs 23.7%) from almost the same defaults.

## Method

1. Annual cohort transition matrices, NR-adjusted (`src/02_cohort_matrices.py`).
2. Duration (generator) matrix from monthly ratings (`src/04_duration_matrix.py`).
3. One-factor credit-cycle index Z by maximum likelihood, asset correlation set so Z has unit variance (`src/03_cycle_index.py`).
4. Regression of Z on unemployment change, real GDP growth and the Baa spread; out-of-time test on 2007 to 2015 cohorts.
5. Projection under the Fed's 2025 supervisory severely adverse scenario (`src/05_stress_projection.py`).

## Limits

- Defaults are under-recorded in the ratings file before 1999, so 1990-91 cannot be tested and default thresholds use 1998 to 2006 only.
- One systematic factor; no industry or regional factors.
- Checked against S&P's published U.S. speculative-grade default rates: correlation 0.90 over 1999 to 2016, with a median ratio of 0.92. The file under-records defaults before 1999, and partly in 2009 to 2014 (2009: 6.8% against S&P's 11.8%). Scored against S&P's rates instead, the out-of-time ranking is unchanged (macro model 3.68, average 2.24).

## Reproduce

The ratings come from Compustat (`comp.adsprate`) through WRDS and are licensed, so they are not in this repo. With a WRDS account:

```
pip install -r requirements.txt
python src/01_pull_ratings.py
python src/02_cohort_matrices.py
python src/03_cycle_index.py
python src/04_duration_matrix.py
python src/05_stress_projection.py
python src/06_external_check.py
python src/07_figures.py
python src/08_newey_west.py
EST_START=1998 python src/03_cycle_index.py      # robustness run
EST_START=1998 python src/05_stress_projection.py
```

Macro series are downloaded from FRED; the Fed scenario files are in `data/`.
