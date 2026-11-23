# Locked Changed-Input Record - run output

- Prediction: `docs/locked-prediction.md`, commit `066734f0b27f4c98522e12e8fcfdfcc0895d7aa8` committed 2026-11-23T15:32:26-05:00 (on origin/main); SHA-256 `d41533da9b8c86bfb36b902a91bd8a892c5ef5c84738d2a8470504002d58a22c`
- Run (AI closed): 2026-11-23T20:34:15+00:00 by `python locked_test.py`
- Input: **cpi_pct** (% a year): old **2.5** -> new **3.0**

| Output | Before (old value) | After (new value) |
|---|---|---|
| feasible | True | True |
| constrained weights | BIL 85%, ACWI 15% | BIL 80%, ACWI 20% |
| constrained net return | 6.77% | 7.59% |
| constrained volatility | 1.76% | 2.33% |
| constrained loss 95 | -3.87% | -3.76% |
| Verdict: equal_weight | FAIL - M5, R1 (turnover needs committee approval) | FAIL - M5, R1 (turnover needs committee approval) |
| Verdict: inverse_vol | FAIL - O1 (turnover needs committee approval) | FAIL - O1 (turnover needs committee approval) |
| Verdict: benchmark | FAIL - M3 | FAIL - M3 |
| Verdict: constrained | PASS - every checkable rule (turnover needs committee approval) | PASS - every checkable rule (turnover needs committee approval) |
| Stop test S1 | ok (feasible) | ok (feasible) |
| Stop test S2 | TRIPPED (largest: 60-month window = 30%) | TRIPPED (largest: 60-month window = 30%) |
| Stop test S3 | TRIPPED (2022: -10.8%) | TRIPPED (2022: -12.3%) |
| process status | STOP | STOP |
| rule implied action | REJECT (stop rule fires) | REJECT (stop rule fires) |
| walk forward annual return | 6.33% | 6.44% |
| walk forward worst year | 2022: -10.8% | 2022: -12.3% |
| walk forward stops | 3 | 4 |
| walk forward turnover breaches | 12 | 11 |

## Reconciliation (the student writes this after the run, in docs/validation-and-ai-use.md)
Expected vs actual direction, actual decision effect, and the diagnosis where they differ.
