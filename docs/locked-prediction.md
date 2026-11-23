# Locked prediction - AI OFF

**Who writes this:** Tobey Uhm, by hand, with every AI tool closed. Nothing below may be drafted,
edited or checked by an AI before the run. This file was created as an empty template; the
template text is not the prediction.

**Steps:** close AI tools -> fill every `TO BE WRITTEN` field -> `git add docs/locked-prediction.md`
-> `git commit -m "Locked prediction (AI off)"` -> `git push` -> `python locked_test.py`.
The runner refuses to run until the file is filled, committed and pushed. After the run, do not
edit this file; write the reconciliation in `docs/validation-and-ai-use.md`.

## 1. The one input I change

Pick one load-bearing input. Allowed names (copy one exactly into `LOCKED-INPUT`):
`window_months` (months), `cost_multiplier` (x base costs), `issuer_limit` (%), `reserve_min` (%),
`loss_limit` (%), `cpi_pct` (%), `mu_shift:ACWI` / `mu_shift:AGG` / `mu_shift:LQD` (percentage
points added to the historical estimate; old value 0), `mu_override:JOBY` (% a year).
Base values: window 36, cost multiplier 1, issuer limit 8, reserve minimum 3, loss limit 10, CPI 2.5.

LOCKED-INPUT: TO_BE_WRITTEN
OLD: TO_BE_WRITTEN
NEW: TO_BE_WRITTEN

Why this input is load-bearing (one or two sentences): TO BE WRITTEN

## 2. My prediction (before the run)

| Output | Before (from output/report.md) | Expected direction (up / down / unchanged) | Expected size or level |
|---|---|---|---|
| Constrained portfolio: ACWI weight | 15% | TO BE WRITTEN | TO BE WRITTEN |
| Constrained portfolio: BIL weight | 85% | TO BE WRITTEN | TO BE WRITTEN |
| Constrained net expected return | 6.77% | TO BE WRITTEN | TO BE WRITTEN |
| Constrained volatility | 1.76% | TO BE WRITTEN | TO BE WRITTEN |
| Equal-weight verdict | FAIL - M5, R1 | TO BE WRITTEN | TO BE WRITTEN |
| Stop test S2 (stress shift) | TRIPPED (60-month window 30%) | TO BE WRITTEN | TO BE WRITTEN |
| Stop test S3 (walk-forward worst year) | TRIPPED (2022: -10.8%) | TO BE WRITTEN | TO BE WRITTEN |
| Walk-forward annual return | 6.33% | TO BE WRITTEN | TO BE WRITTEN |

## 3. Expected decision effect

Does REJECT (0% to the process; reserve ACWI 55-60 / AGG 35-40 / BIL 3-5) change? To what, and why?

TO BE WRITTEN

## 4. The finance reasoning behind my prediction

TO BE WRITTEN

## 5. What I will check first if the result disagrees

TO BE WRITTEN

Signed (typed name and date/time): TO BE WRITTEN
