# Instructions for an AI assistant working on this repository

These instructions are for any AI coding or writing assistant: OpenAI Codex (which reads `AGENTS.md` automatically), ChatGPT, Gemini, Copilot, Cursor, or another. If your tool does not read this file automatically, paste it in as the first message.

**AI use.** This repository was built with Claude (Anthropic; Claude Code, Claude Opus 5.5) and, for the earlier labs, OpenAI Codex (GPT-5). The analysis and the decision belong to the student, Tobey Uhm.
**Education, not investment advice.**

---

## 1. Who you are working for and what this is

You are assisting **Tobey Uhm**, an undergraduate in FIN 43900 (AI in Finance, Purdue, Fall 2026), on **Project 2: Investment Management Application**. The student plays a portfolio analyst who must recommend that an investment committee **adopt, allocate to, rebalance, pilot or reject** a portfolio process under a written mandate.

- **Client:** the Meridian Foundation Reserve. This is the fictional Lab 13 common case: a $100M reserve that pays out $0.75M a quarter, has a seven-year horizon and rebalances annually.
- **Mandate** (`config/mandate.json`, explained in `docs/mandate.md`):
  - O1 objective: expected return net of costs >= CPI 2.5% + 4% = 6.5%.
  - M3 payout reserve: BIL + IEF >= 3.0%.
  - M5 single company: JOBY <= 8%.
  - M1/M2: long-only, weights sum to 100%.
  - M4 liquidity: >= 90% redeemable in 5 business days.
  - R1 risk: one-year 95% loss <= 10%.
  - G1 turnover: <= 25% one-way without approval.
- **Universe:** BIL, IEF, AGG, LQD, ACWI and JOBY. **Benchmark** and assumed current holdings: 60% ACWI / 40% AGG.
- **Process judged:** a minimum-volatility, long-only grid search (5-point steps) that must pass every rule. A point-in-time Treasury term-spread signal (10y minus 3m, known one business day before) moves IEF to BIL when the curve is inverted.
- **Frozen result (decision as of 2026-10-30):** **REJECT.** The process gets 0% of the reserve, and the reserve is rebalanced to ACWI 55-60 / AGG 35-40 / BIL 3-5. Two of three stop tests trip:
  - S2: a 60-month window moves the portfolio 30% one-way.
  - S3: the walk-forward 2022 loss was -10.8%.
  - Walk-forward 2012-2026: 6.33% a year against 7.68% for the benchmark.
- **Grading:** a 300-point analytic rubric across six criteria. The largest is Validation, sensitivity and reproducibility (75). Decision-ready requires an app a committee could adopt, traceable data, known-answer tests, a stress run, a complete Locked Changed-Input Record, cold-run evidence, and consistency across the memo, README, output, transcripts and videos.

## 2. Hard rules (do not break these)

1. **Never write, draft, suggest, edit or review `docs/locked-prediction.md` before its run.** Do not predict, hint at or "sanity-check" what changing any input will do before the student's prediction is committed and pushed. The course requires a human-authored AI-off prediction. If asked, refuse and point to `docs/locked-prediction-instructions.md`.
2. **Never run `python locked_test.py` or `python locked_test.py --dry-run`**, and never open the app with the student's chosen value, before the prediction is pushed. Running it would leak the answer. After the run, you may help trace why the result happened. The student must disclose that help.
3. **Never edit `docs/locked-prediction.md` after its run.** It is locked by its commit hash and SHA-256.
4. **Do not change the frozen data** (`data/prices_monthly.csv`, `data/treasury_curve_daily.csv`, `data/data_snapshot.json`). Do not run `python tools/download_data.py` unless the student explicitly asks for a new data vintage. That changes every number and the hashes.
5. **Do not change the decision or its numbers on your own.** The recommendation lives in `config/recommendation.json` and is the student's judgment. If you find an error, explain it and let the student decide.
6. **Keep the numbers consistent everywhere.** Any change that moves a result means you must:
   - run `python analysis.py`;
   - run `python -m unittest discover -s tests -v` (all must pass; there are 23 now);
   - update every place the number appears: `docs/decision-memo.md`, `README.md`, `docs/validation-and-ai-use.md`, `docs/video-scripts.md`, the `docs/transcript-video-*.txt` files and `config/recommendation.json`.
7. **Standard library only.** No pandas, numpy, Streamlit or other packages. Pandas and Streamlit DLLs are blocked on the student's Windows machine by an Application Control policy, and the zero-install design is part of the reproducibility claim.
8. **Every README, the memo and each video must open with the two statements:** which AI was used and for what, plus "the analysis and decision are mine"; and "education, not investment advice". If you are a new AI tool doing material work, add yourself to the statements and to the AI table (rule 9).
9. **Disclose yourself.** Add a row to the table in `docs/validation-and-ai-use.md`, section 6:
   - your tool and model/version as shown to the student, and the date;
   - the task;
   - your material output or claim;
   - how the student checked it;
   - the disposition (accepted / qualified / corrected / rejected) and its effect on the decision.

   No chat logs, credentials or private data.
10. **No secrets in the repo.** No `.env`, API keys or tokens. `.env.example` is intentionally empty.
11. **Do not invent evidence.** Do not fill cold-run partner details, video URLs, durations, YouTube IDs or the student's dispositions. Leave `[ ]` placeholders for the student.
12. **Git:** commit with clear messages. Push only when the student asks. Never force-push, rewrite history or delete the `project2-submission` tag once it exists.

## 3. How the code works (read before editing)

| Path | Role |
|---|---|
| `p2/data.py` | Loads frozen data. `Prices.window(tickers, end_month, n)` returns the last n monthly returns (the point-in-time boundary). `TreasuryCurve.value_known_on(date)` returns only the curve dated before the decision date. JOBY before 2021-08 (SPAC prices) is excluded. |
| `p2/estimates.py` | Mean x 12, sd x sqrt(12), covariance x 12 (the Lab 15 conventions); `portfolio_stats` and the 95% loss |
| `p2/mandate.py` | Rules M1-M5, O1, R1, G1; `verdict()` names the failing rule |
| `p2/optimizer.py` | Exhaustive grid (53,130 mixes for six assets) giving the lowest volatility that passes every rule, or `None` with a diagnosis; baselines `equal_weight` and `inverse_volatility` |
| `p2/pipeline.py` | `run_decision`, `stress_run` (15 scenarios), `stop_status` (S1-S3), `walk_forward` (December rebalances, drift, costs, stop means hold the benchmark), `signal_test`, `fixed_mix_history` |
| `p2/report.py` | Builds `output/report.md` and `output/growth.svg` |
| `analysis.py` | Checks the data hashes, runs everything, writes `output/` |
| `app.py` | `http.server` web app on port 8502 (`PORT` overrides; `--no-browser`). Live controls recompute through the same engine. `/api/run` returns JSON |
| `locked_test.py` | The locked-record runner. Refuses unless the prediction is filled, committed and pushed (see rules 1-3) |
| `tests/test_engine.py` | Lab 13, 15 and 17 known answers; point-in-time and no-look-ahead; mandate and optimizer; signal; data hash; frozen output equals the engine |
| `docs/` | Memo, validation and AI-use record, mandate, data card, locked prediction and its instructions, video scripts, transcripts, manifest, human to-do list |
| `prior-work/` | Byte-for-byte copies of the Lab 13, 15 and 17 files. Never edit them |

Commands (from the repo root, Python 3.10+):

```bash
python analysis.py
python -m unittest discover -s tests -v
python app.py            # http://localhost:8502
```

Known conventions:
- ETF adjusted closes are already net of expense ratios; do not subtract them again.
- Trading costs are charged on turnover.
- Data files are hashed with CRLF normalised to LF, and `.gitattributes` marks `data/*` as `-text`. Keep both.

## 4. What is still open (the student's to-do: `docs/HUMAN-ACTIONS-REQUIRED.md`)

| Task | Can you help? |
|---|---|
| Locked prediction, lock, run | **No**, until it is pushed. Afterwards, yes: tracing the cause and drafting the reconciliation wording in `docs/validation-and-ai-use.md` section 5 for the student to check. Disclose it. |
| Fill the Video 2 [3:25] placeholders | Yes, after the run, from `output/locked_test_result.md` |
| Correct the transcripts after recording | Yes: compare the YouTube captions with the script and fix tickers, names and numbers. Keep the student's actual words. |
| Verify the AI table (Labs 13-17 tool and model) | Only the student knows; ask them |
| Partner cold run (validation section 7, row 3) | No; the student records it |
| Manifest URLs, durations, timestamps | Format only; the student supplies the values |
| Freeze: `git tag project2-submission` and `git push --tags` | Only when the student says it is final |

## 5. How to answer the student

- Be direct. Cite files as `path:line`. Show the command and its output when you claim something passed.
- If a request would break a rule in section 2, say which rule and offer the allowed alternative.
- If tests fail, say so and show the failure; do not hide or skip tests.
- When unsure whether a change affects a graded number, run `python analysis.py` and `git diff output/` to see.
