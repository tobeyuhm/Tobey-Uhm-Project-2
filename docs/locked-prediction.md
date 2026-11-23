# Locked prediction - AI OFF

**Who writes this:** Tobey Uhm, by hand, with every AI tool closed. Nothing below may be drafted,
edited or checked by an AI before the run. This file was created as an empty template; the
template text is not the prediction.

**Transcription note:** the student wrote the answers below and pasted them into a Claude Code
session (Claude Opus 5.5, 2026-11-23). Claude copied them into this file word for word. It added no
content and gave no review or feedback on them. The table layout was adapted to hold the student's
sentences; the wording is unchanged.

**Read first (before closing AI):** [`locked-prediction-instructions.md`](locked-prediction-instructions.md)
has the project context, the base-case numbers, how each input enters the code, and the commands.

**Steps:** close AI tools -> fill every placeholder field -> `git add docs/locked-prediction.md`
-> `git commit -m "Locked prediction (AI off)"` -> `git push` -> `python locked_test.py`.
The runner refuses to run until the file is filled, committed and pushed. After the run, do not
edit this file; write the reconciliation in `docs/validation-and-ai-use.md`.

## 1. The one input I change

Pick one load-bearing input. Allowed names (copy one exactly into `LOCKED-INPUT`):
`window_months` (months), `cost_multiplier` (x base costs), `issuer_limit` (%), `reserve_min` (%),
`loss_limit` (%), `cpi_pct` (%), `mu_shift:ACWI` / `mu_shift:AGG` / `mu_shift:LQD` (percentage
points added to the historical estimate; old value 0), `mu_override:JOBY` (% a year).
Base values: window 36, cost multiplier 1, issuer limit 8, reserve minimum 3, loss limit 10, CPI 2.5.

LOCKED-INPUT: cpi_pct
OLD: 2.5
NEW: 3.0

Why does this input matter?

The reserve needs to earn 4 percentage points above inflation. Raising inflation from 2.5% to 3.0% raises the required return from 6.5% to 7.0%. The current portfolio earns an estimated 6.77%, so it falls short.

## 2. My prediction (before the run)

| | Output | Before (from output/report.md) | Predicted (student's words) |
|---|---|---|---|
| 5a | Constrained portfolio: ACWI weight | 15% | Up from 15% to 20%. |
| 5b | Constrained portfolio: BIL weight | 85% | Down from 85% to 80%. |
| 5c | Constrained net expected return | 6.77% | Up from 6.77% to about 7.6%. |
| 5d | Constrained volatility | 1.76% | Up from 1.76% to about 2.3%. |
| 5e | Equal-weight verdict | FAIL - M5, R1 | Unchanged. It still fails the JOBY limit (M5) and the risk limit (R1). |
| 5f | Stop test S2 (stress shift) | TRIPPED (60-month window 30%) | Stays TRIPPED. I expect at least one stress test to shift more than 25% of the portfolio. |
| 5g | Stop test S3 (walk-forward worst year) | TRIPPED (2022: -10.8%) | Stays TRIPPED. I expect the worst year to lose about 11%, above the 10% loss limit. |
| 5h | Walk-forward annual return | 6.33% | Up slightly from 6.33% to about 6.5%. This is my least certain prediction. |

## 3. Expected decision effect

Does REJECT (0% to the process; reserve ACWI 55-60 / AGG 35-40 / BIL 3-5) change? To what, and why?

I expect REJECT to stay in place. The new mix should pass S1, but I expect S2 and S3 to stay tripped. Either one is enough to reject the process. I would keep 0% in the process and keep the reserve ranges at 55–60% ACWI, 35–40% AGG, and 3–5% BIL.

## 4. The finance reasoning behind my prediction

ACWI has a higher estimated return than BIL. Moving 5% of the portfolio from BIL to ACWI should add about 0.82 percentage points to expected return. That would clear the new 7.0% target in one step, with slightly higher volatility.

The higher target also applies at each yearly rebalance. In some years, the model may hold more stocks. In others, no mix may qualify, so it would hold the benchmark. That makes the historical return harder to predict than today's weights.

## 5. What I will check first if the result disagrees

I would check whether a mix with 15% ACWI and more bonds could reach 7.0% with less risk than my predicted mix. If my worst-year estimate is off, I would check what the model actually held going into that year.

Signed (typed name and date/time): Tobey Uhm, 2026-11-23 15:32 EST (UTC-0500). I confirm I wrote these answers myself with AI off.
