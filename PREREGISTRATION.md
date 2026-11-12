# Preregistration: rating migration and default probability under stress

Written 2026-11-12, before any transition matrix or model was estimated. Changes after this date go in the log at the bottom with a reason.

## Question

How do corporate default and downgrade probabilities move with the macro cycle, and what does a severely adverse scenario imply for them?

## Data

- S&P long-term issuer credit ratings, Compustat `comp.adsprate`, monthly, 1981-01 to 2017-02 (pulled once from WRDS on 2026-11-12; `data/sp_ratings.parquet`, not published).
- Macro series from FRED: unemployment rate, real GDP growth, BBB corporate spread, VIX.
- The Federal Reserve's published supervisory severely adverse scenario (latest available file).

## Definitions, fixed now

- Grades: AAA, AA, A, BBB, BB, B, CCC (CCC+ to C), D (D and SD). Modifiers (+/-) are merged into the letter grade.
- Not rated (NR): no rating record, or N.M. / Suspended.
- Default is absorbing: an issuer that reaches D stays D.
- Cohort: issuers rated on 31 December of year t. One-year transition: grade on 31 December of year t+1. An issuer that defaults at any point in the year counts as D.
- NR handling: transitions to NR are reported, then removed and rows renormalised (the standard NR-adjusted matrix).
- Investment grade: AAA to BBB. Speculative grade: BB to CCC.

## Method

1. Annual cohort transition matrices, 1981 to 2015 cohorts, and their average.
2. Duration (hazard-rate) estimate of the same matrix from monthly data, for comparison.
3. A one-factor credit-cycle index Z_t: the single shift of the average matrix's normal thresholds that best fits each year's matrix.
4. Regress Z_t on macro variables. Estimation window: 1981 to 2006.
5. Out-of-time test: predict the 2007 to 2015 speculative-grade default rates from macro data only.
6. Project default and downgrade probabilities under the severely adverse scenario.

## Hypotheses

- H1. Speculative-grade default rates peak in 1990-91, 2001-02 and 2009, and Z_t is lowest in those years.
- H2. The macro-linked model predicts 2007 to 2015 speculative-grade default rates with lower mean absolute error than the through-the-cycle average matrix.
- H3. Under the severely adverse scenario the projected speculative-grade default rate is at least double its through-the-cycle average.

## What counts as a null result

- H2 fails if the macro model's out-of-time error is not lower than the average matrix's. That is reported as "macro variables did not add out-of-time information in this sample".
- All results are reported, including the comparisons the model loses.

## Sanity checks before any result is used

- Row sums of every matrix equal 1.
- Default rates rise monotonically from AAA to CCC in the average matrix.
- Yearly speculative-grade default rates are compared with S&P's published annual default study as an external check.

## Change log

- 2026-11-12, after the first sanity check (`src/02_cohort_matrices.py`), before any model was fitted. The data records defaults poorly before 1999: 10 and 6 first defaults in 1990 and 1991, against 69 to 100 a year in 1999 to 2002. S&P's own studies show a default peak in 1990-91, so this is a coverage gap in the Compustat file, not a calm period. Consequences:
  - H1 cannot be tested for 1990-91. It is tested for 2001-02 and 2009 only.
  - The 1981 to 2006 estimation window in step 4 is not usable for defaults. The window and the out-of-time split need to be reset on the 1998 to 2015 cohorts. This is to be decided before step 3 runs.
  - The average matrix is reported for 1981 to 2015 and again for 1998 to 2015.
- 2026-11-12, decided before step 3 ran: fit the cycle index on rating migrations as well as defaults, so all cohorts are usable. Implementation, fixed before running:
  - For the Z_t fit only, D is merged into CCC ("CCC or worse"), so under-recorded early defaults do not drive the index.
  - Z_t is fitted by maximum likelihood, one value per year. The correlation rho is set so that Z_t has unit variance over the estimation window.
  - Estimation window stays 1981 to 2006 cohorts; out-of-time window is 2007 to 2015 cohorts. rho, thresholds and regression coefficients use estimation-window data only.
  - Default thresholds come from the 1998 to 2006 cohorts only (where defaults are recorded), for both the macro model and the through-the-cycle benchmark.
- 2026-11-12, after the first run of step 3: the 1981 to 1984 cohorts hold one or two issuers each (the file effectively starts in December 1985), and one of two issuers changing grade produced a cycle value of -4.1 for 1985. All cohorts now start in 1985. The first-run numbers (rho 0.077, R2 0.17, out-of-time error 3.08 against 2.34) are kept here for the record; the conclusion on H2 was the same in both runs.
- 2026-11-12, before step 6 ran. Choices for the stress projection, fixed now:
  - Scenario file: the Federal Reserve's 2025 supervisory severely adverse scenario (`data/fed_2025_severely_adverse.csv`), the most recent one found at the Fed's file address. Calendar years 2025, 2026 and 2027.
  - The scenario gives a BBB corporate yield, not Moody's Baa. Over 1988 to 2007 the Baa spread averaged 0.64 points above the Fed's BBB spread (standard deviation 0.37), so 0.64 is added to the scenario spread. Unemployment change is Q4 minus the previous Q4; GDP growth is the four quarterly annualised rates compounded.
  - Portfolio: the grade mix of the December 2015 cohort, the last one in the data.
  - Because H2 failed, the macro projection is reported next to a second stress that does not use macro data: the cycle value of the worst fitted year (2002).
- 2026-11-12, robustness check, fixed before running: steps 3 to 6 are rerun with the estimation window cut to the 1998 to 2006 cohorts (transition years 1999 to 2007), where defaults are recorded. Everything else is unchanged. With 9 years and 3 regressors the regression is weak; the point is only whether the H2 and H3 conclusions survive. Outputs carry the suffix `_est1998`.
- 2026-11-12, added after all results were in (not preregistered): the macro regression's standard errors are recomputed with Newey-West (HAC) errors, because the yearly cycle index may be autocorrelated and plain OLS errors would then overstate the t-statistics. Lags 1 to 3 are reported; the rule of thumb floor(4(n/100)^(2/9)) gives 2 for n = 22. Point estimates and the out-of-time test are unchanged.
  - Macro regressors, same year as the transitions: change in the unemployment rate (December to December), real GDP growth (Q4 over Q4), average Baa minus 10-year Treasury spread. VIX is dropped because it starts in 1990.
