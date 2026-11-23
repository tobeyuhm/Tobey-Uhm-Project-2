# How to write the Locked Changed-Input Record (`docs/locked-prediction.md`)

**AI use.** Claude (Opus 5.5) wrote these instructions. It did not choose your input and did not predict any result. The prediction itself must be written by you with every AI tool closed.
**Education, not investment advice.**

Read this page, the base-case numbers and the code it points to **before** you close your AI tools. Then close them, and write the prediction on your own.

---

## 1. What this record is and why it is graded

Project 2 requirement 6 asks for **one Locked Changed-Input Record**: your AI-off prediction, committed to GitHub before the run, then the result. It counts under **Validation, sensitivity and reproducibility** (75 points, the largest rubric criterion). "Decision-ready" there needs "a complete Locked Changed-Input Record with a human-authored AI-off prediction plus predicted and actual decision effect".

The course's architecture document adds three points:

- Complete fields are **necessary but not sufficient**.
- Credit depends on a **finance-grounded prediction**, a **faithful run** and a **diagnosis supported by the preserved evidence**.
- A wrong prediction with a good diagnosis can earn full credit. A right prediction with no reasoning cannot.

This is the Lab 11 and Lab 20 habit, done once more on your Project 2 system: predict, lock, run, reconcile.

## 2. The project in one page (what you are predicting about)

**Client and mandate (Lab 13, encoded in `config/mandate.json`).** The client is the Meridian Foundation's $100M reserve, which pays out $0.75M a quarter. The rules are:

| Rule | What it checks |
|---|---|
| O1 objective | Expected return net of trading costs >= CPI (2.5%) + 4% = 6.5% |
| M3 payout reserve | BIL + IEF >= 4 x 0.75 / 100 = 3.0% |
| M5 single company | JOBY <= 8% |
| M1/M2 | Long-only; weights sum to 100% |
| M4 liquidity | >= 90% redeemable in 5 business days |
| R1 risk (my S9 measure) | One-year 95% loss, -(mu - 1.645 x sigma), <= 10% |
| G1 turnover | <= 25% one-way without committee approval (a flag, not a failure) |

**Universe.** BIL (T-bills), IEF (7-10y Treasuries), AGG (U.S. aggregate bonds), LQD (IG corporates), ACWI (global equities) and JOBY (your Project 1 company). The benchmark and the assumed current holdings are 60% ACWI / 40% AGG.

**The process being judged.** Each decision date, `p2/pipeline.py::run_decision` does five things:

1. Estimates each asset's expected return (mean monthly return x 12) and covariance from the last *N* months (`window_months`, base 36).
2. Tries all 53,130 long-only mixes in 5-point steps (`p2/optimizer.py::optimize`).
3. Throws out any mix that breaks the issuer cap or the reserve minimum, that misses the objective after subtracting trading costs, or that breaks the loss limit.
4. Keeps the mix with the **lowest volatility** among the survivors. If none survive, it returns "no feasible mix".
5. Applies the term-spread signal: if the 10y-3m spread is negative, IEF moves to BIL.

**The three stop tests** (`p2/pipeline.py::stop_status`) decide whether the process may proceed:

| Test | Passes when | Base result |
|---|---|---|
| S1 | A mix passes every base-mandate rule | ok |
| S2 | No "adjacent" stress moves the portfolio more than 25% one-way, and none makes it infeasible | **TRIPPED** (60-month window = 30%) |
| S3 | Walk-forward worst calendar year >= -10% | **TRIPPED** (2022: -10.8%) |

The rule-implied action is **REJECT whenever any stop test trips**. Your committee decision is REJECT: 0% to the process, and the reserve rebalanced to ACWI 55-60 / AGG 35-40 / BIL 3-5.

**Base-case numbers you are predicting changes from** (from `output/report.md`; copy them into your table):

| Output | Base value |
|---|---|
| Constrained portfolio | BIL 85%, ACWI 15% |
| Net expected return / volatility / 95% loss | 6.77% / 1.76% / -3.87% |
| Equal-weight verdict | FAIL - M5, R1 |
| Inverse-volatility verdict | FAIL - O1 |
| Benchmark verdict | FAIL - M3 |
| Stop tests S1 / S2 / S3 | ok / TRIPPED / TRIPPED |
| Walk-forward (Jan 2012 - Oct 2026) annual return | 6.33% (benchmark 7.68%) |
| Walk-forward worst year / stops / turnover breaches | 2022: -10.8% / 3 of 15 / 12 of 14 |
| 36-month estimates (expected return, volatility) | BIL 4.34%, 0.21% · IEF 4.74%, 6.73% · AGG 5.43%, 5.61% · LQD 6.48%, 7.73% · ACWI 20.78%, 11.44% · JOBY 22.68%, 79.55% |

**Important:** the runner applies your changed input **everywhere**. That covers the decision-date portfolio, the stress table (each stress is stacked on your change) and the whole walk-forward. So a change can move S2 and S3, not only today's weights.

## 3. Choose the one input

Pick an input you believe is **load-bearing**: one where a plausible change could alter the decision or a stop test. Copy its name exactly.

| `LOCKED-INPUT` | Unit (write values in this unit) | Base `OLD` | Where it enters the code |
|---|---|---|---|
| `window_months` | months (any whole number from 12 to 120; the app's dropdown offers only 24/36/60/120, but the runner accepts any) | 36 | `Prices.window` estimation window, today and at every December in the walk-forward. A longer window also starts the walk-forward later |
| `mu_shift:ACWI` | percentage points added to ACWI's estimated return | 0 | `run_decision`, after estimation, every decision date |
| `mu_shift:AGG`, `mu_shift:LQD` | percentage points added | 0 | same |
| `mu_override:JOBY` | % a year, replacing JOBY's estimate | 22.68 (historical, rounded; the run uses 22.68 exactly as OLD) | same; matters only once JOBY has a full window (from late 2024) |
| `cost_multiplier` | x base costs (2-3 bps ETFs, 25 bps JOBY) | 1 | `optimize` (cost subtracted from return) and the walk-forward (cost charged at each rebalance) |
| `issuer_limit` | % of reserve | 8 | M5 cap on JOBY in `optimize` and `mandate.check` |
| `reserve_min` | % of reserve | 3 | M3 floor on BIL + IEF |
| `loss_limit` | % (one-year 95% loss) | 10 | R1 filter in `optimize` and `mandate.check` (**not** stop test S3, which stays -10%) |
| `cpi_pct` | % a year | 2.5 | objective O1 = CPI + 4% |

**Make it a real test: choose a NEW value that is not already in the stress table.** You have already seen these results in `output/report.md`:

- window 24, 60 and 120
- ACWI -1 and -2 pts
- AGG and LQD -1 pt together
- JOBY 0%
- costs x4 and x20
- issuer limit 0%
- reserve minimum 10%
- loss limit 8%
- CPI 1.5% and 3.5%

A value you have not seen (for example a 48-month window, or a different size of shift, cost or limit) means your prediction comes from reasoning, not memory. A window longer than 36 months also starts the walk-forward later (it needs a full window before the first December), so the holdout period changes with it. Say so in your reasoning.

Do **not** open the app with your new value before the run. That would be running it before locking the prediction.

## 4. Write the prediction (AI closed)

Fill every `TO BE WRITTEN` field in `docs/locked-prediction.md`:

1. **`LOCKED-INPUT`, `OLD`, `NEW`** on their own lines, exactly as `NAME: value` with no `%` sign. The runner reads these lines.
2. **Why it is load-bearing**, in one or two sentences of finance reasoning.
3. **The prediction table.** For each row give a direction (up / down / unchanged) **and** a size or level, for example "ACWI weight up, to about 25-35%". A range is fine; "it changes" is not.
4. **Expected decision effect.** Does REJECT hold? Say which stop tests you expect to pass or trip, and whether the range, a trigger or the committee ask would change.
5. **The finance reasoning.** Explain the mechanism, step by step, through the code path in section 3: what the input changes, which constraint or estimate that moves, and why the lowest-volatility survivor shifts.
6. **What you will check first if you are wrong.** Name the likeliest reason in advance: a binding constraint, the 5-point grid, the walk-forward start date, the signal, or a cost effect.
7. **Signature:** your typed name and the date and time.

Write in your own words, as you would speak them in Video 2.

## 5. Lock it, then run it (commands)

The repo must be on GitHub first. Right now it is committed locally but not pushed; it still needs your public/private choice. Then, from the project folder:

```powershell
git add docs/locked-prediction.md
```

```powershell
git commit -m "Locked prediction (AI off)"
```

```powershell
git push
```

```powershell
python locked_test.py
```

`locked_test.py` **refuses to run** in any of these cases:
- a `TO BE WRITTEN` field is left;
- the file has uncommitted edits;
- its commit is not yet on GitHub.

When it runs, it records your commit hash, commit time and the file's SHA-256. It then computes before (OLD) and after (NEW) and writes `output/locked_test_result.md` and `output/locked_test_result.json`. Commit and push those two files.

```powershell
git add output/locked_test_result.md output/locked_test_result.json
```

```powershell
git commit -m "Locked changed-input run output"
```

```powershell
git push
```

**Never edit `docs/locked-prediction.md` after the run.** A later edit would show in the Git history and void the lock.

## 6. After the run: the reconciliation

Fill section 5 of `docs/validation-and-ai-use.md` from `output/locked_test_result.md`:

- **Commit, time, SHA-256, input, old and new values with units:** copy them from the result file.
- **Expected vs actual direction:** go row by row, and mark each as match or miss.
- **Predicted vs actual decision effect:** does REJECT hold, and which stop tests changed?
- **Diagnosis.** For every miss, name the mechanism in the code, not "the model is complex". For example: which constraint became binding, why the grid jumped by 5 points, or why the walk-forward changed differently from today's portfolio. If nothing changed, explain why the input was not binding.
- **Decision consequence:** does a trigger, the allocation range or a committee ask change? If yes, update `config/recommendation.json`, rerun `python analysis.py`, and keep the memo consistent.

You may use AI **after** the run to help trace the cause, as in Project 1. Disclose it in a sentence ("post-run tracing done with Claude Opus 5.5, checked against the result files").

Then fill the Video 2 placeholders at [3:25] in `docs/video-scripts.md` with your actual commit, prediction and result.

## 7. Checklist

- [ ] Input chosen and value not already in the stress table
- [ ] Every row has a direction **and** a size
- [ ] Decision effect names the stop tests
- [ ] Reasoning follows the code path
- [ ] Committed **and pushed** before `python locked_test.py`
- [ ] Result files committed and pushed; prediction file untouched after the run
- [ ] Validation section 5 reconciled; memo, report and Video 2 agree
