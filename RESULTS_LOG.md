# Results log

Every number here is printed by the script named beside it. Nothing goes on a resume until this file and a claims file agree.

## 2026-11-12

**Data** (`src/01_pull_ratings.py`): 702,168 monthly S&P issuer ratings, 5,972 issuers, 1981-01 to 2017-02. Usable from the December 1985 cohort. Defaults are under-recorded before 1999.

**Average one-year transition matrix, 1985 to 2015 cohorts** (`src/02_cohort_matrices.py`, `results/avg_matrix_nr_adjusted_pct.csv`): 56,869 issuer-years. One-year default rates: BBB 0.16%, BB 0.58%, B 3.55%, CCC 23.70%. Rows sum to 1; default rate is monotone in grade.

**Speculative-grade default rate by year** (`results/yearly_default_rates.csv`): peaks of 10.16% in 2001 and 6.75% in 2009.

**Credit-cycle index** (`src/03_cycle_index.py`, `results/cycle_index.csv`): asset correlation rho = 0.027. Lowest values: 2002 (-2.08), 2001 (-1.92), 2009 (-1.79). H1 holds for 2001-02 and 2009; it cannot be tested for 1990-91.

**Macro regression, transition years 1986 to 2007** (`results/model_summary.csv`): R2 = 0.82, n = 22. Only the Baa spread is significant (coefficient -1.78, t = -7.8). Unemployment change and GDP growth are not.

**Out-of-time test, default years 2008 to 2016** (`results/out_of_time_default_rates.csv`), mean absolute error in percentage points:

| Model | Error |
|---|---|
| Macro model (Z predicted from macro data) | 4.97 |
| Through-the-cycle average | 2.34 |
| Fitted Z (uses that year's actual migrations; not a forecast) | 1.55 |

**H2 fails.** The macro model is worse out of time than the simple average. It over-predicts defaults in every year from 2008, because credit spreads stayed wide after the crisis while defaults fell quickly. The cycle factor itself is real (the fitted-Z row beats the average), but the spread-based link to macro data did not hold out of sample.

**Duration-method matrix** (`src/04_duration_matrix.py`, `results/duration_matrix_pct.csv`, `results/cohort_vs_duration_pd.csv`): 55,590 issuer-years at risk, 7,470 monthly grade changes, December 1985 to December 2016. One-year default probability, cohort against duration:

| Grade | Cohort | Duration |
|---|---|---|
| AAA | 0.00% | 0.0005% |
| AA | 0.00% | 0.003% |
| A | 0.06% | 0.05% |
| BBB | 0.16% | 0.05% |
| BB | 0.58% | 0.31% |
| B | 3.55% | 2.77% |
| CCC | 23.70% | 31.99% |

The two methods count almost the same defaults (706 and 705), so the gap is not missing data. The duration method assumes the next move depends only on the current grade. It gives lower default rates for BBB to B and a higher one for CCC, which is what you would see if recently downgraded issuers default faster than their grade alone implies. That reading is an interpretation; it has not been tested here.

**Stress projection** (`src/05_stress_projection.py`, `results/stress_projection.csv`, `results/scenario_regressors.csv`): Fed 2025 severely adverse scenario, grade mix of the December 2015 cohort.

| Case | Z | Speculative-grade default rate | BBB to speculative grade or default |
|---|---|---|---|
| Through-the-cycle average (1998 to 2006 cohorts) | n/a | 4.42% | 6.29% |
| Worst fitted year (2002) | -2.08 | 7.69% | 11.37% |
| Severely adverse, 2025 | -7.21 | 24.94% | 36.12% |
| Severely adverse, 2026 | -5.30 | 16.91% | 25.11% |
| Severely adverse, 2027 | -2.04 | 7.62% | 11.26% |

**H3 holds on paper (ratio 5.65) but the number is not credible.** The scenario's spread (5.24 after the 0.64 bridge) is far outside the 1.51 to 3.19 range the regression was fitted on, so Z = -7.2 is an extrapolation more than three times past the worst fitted year, from a model that already failed out of time (H2). The defensible stress is the worst-fitted-year row: 1.74 times the average. Even that row understates the real peak: the actual rate was 10.16% in 2001 and 8.39% in 2002, so a single factor fitted on all migrations does not capture default peaks fully.

**Robustness: estimation window cut to 1998 to 2006 cohorts** (`EST_START=1998`, files ending `_est1998`). rho = 0.033. Regression R2 = 0.89, n = 9; the Baa spread is still the only significant regressor (coefficient -1.74, t = -5.1).

| | Full window (1985 to 2006) | 1998 to 2006 only |
|---|---|---|
| Out-of-time error, macro model | 4.97 | 4.19 |
| Out-of-time error, through-the-cycle | 2.34 | 2.34 |
| Out-of-time error, fitted Z | 1.55 | 1.02 |
| Severely adverse peak default rate | 24.94% | 20.11% |
| H3 ratio | 5.65 | 4.55 |
| Worst fitted year over average | 1.74 | 1.53 |

Both conclusions survive: H2 still fails, and the severely adverse number is still an extrapolation (scenario spread 5.24 against a fitted range of 1.69 to 3.19).

**Newey-West check on the macro regression** (`src/08_newey_west.py`, `results/regression_tstats_hac.csv`; added after the results, not preregistered). Residual lag-1 autocorrelation is +0.24 (Durbin-Watson 1.49). Baa spread t-statistic: OLS -7.8, Newey-West -12.4 / -13.9 / -14.5 with 1 / 2 / 3 lags. Unemployment change and GDP growth stay insignificant at every lag (|t| at most 1.1). The HAC errors are smaller than the OLS errors here, so the plain t-statistic was not overstated. With 22 observations HAC errors are themselves imprecise, so the conclusion is only that the Baa spread is the one significant regressor under both methods.

**External check against S&P** (`src/06_external_check.py`, `results/external_check_sp.csv`, `results/external_check_summary.csv`). Source: S&P's 2025 Annual Global Corporate Default And Rating Transition Study, Table 5, U.S. speculative-grade default rate by year. The PDF is in `references/` and is not published.

| Years | Correlation with S&P | Our mean | S&P mean | Median ratio, ours over S&P |
|---|---|---|---|---|
| 1986 to 1998 | 0.25 | 1.80% | 4.41% | 0.31 |
| 1999 to 2016 | 0.90 | 3.77% | 4.40% | 0.92 |
| 2008 to 2016 | 0.90 | 2.73% | 4.02% | 0.57 |

- 1999 to 2007 matches S&P closely (2001: 10.16% against 10.54%; 2003: 5.69% against 5.60%).
- Before 1999 the file under-records defaults, as logged in the preregistration. S&P has a 10.71% peak in 1991; the file shows 1.25%.
- 2009 to 2014 is also low: 6.75% against 11.79% in 2009, and about half of S&P's rate in 2010, 2012, 2013 and 2014. The yearly pattern is right but the level is low, so the file also misses some defaults after 2008. This was not known before the check.

**Is H2 still a failure if S&P's rates are the "actual"?** Yes. This scoring was not preregistered; it was run because of the 2009-2014 gap. Mean absolute error, 2008 to 2016, against S&P's U.S. rates: macro model 3.68, through-the-cycle 2.24, fitted Z 1.19. The ranking is the same as before.
