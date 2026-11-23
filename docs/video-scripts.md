# Video scripts: Project 2 (Meridian Reserve process review)

Scripts drafted with Claude Opus 5.5 (disclosed in `docs/validation-and-ai-use.md`). I read, adapt and deliver them, and I own every spoken claim. Each video opens with the two required statements. Keep a small webcam view on screen. Upload to YouTube as **Unlisted** with captions on, then correct the auto-captions against the transcript files in `docs/`.

Timing: about 130 spoken words a minute. The `[0:00]` marks are targets. **Bold = on screen.**

---

## Video 1: How my system and my thinking changed, plus one AI output I checked (limit 3:00; target 2:30)

**Screen: README top, the two statements highlighted.**

[0:00] I'm Tobey Uhm, FIN 439 Project 2. Two statements first. I used Claude, Opus 5.5 in Claude Code, to build this app's code, tests and documents and to draft my scripts, and OpenAI Codex, GPT-5, for the Lab 13 to 17 code it grows from. The analysis and the decision are mine. This is education, not investment advice.

**Screen: `prior-work/lab13/lab13_meridian.md`, S1-S10 table.**

[0:22] My system started in Lab 13 as a rule checker. S9, "no calendar-year loss over 10%", was an unverifiable promise. My thinking then was: if a portfolio passes every rule, it's acceptable.

**Screen: `prior-work/lab15/lab15_portfolio_stability.md`, window table.**

[0:38] Lab 15 added an optimizer. Changing the window from 60 to 36 months moved the answer 60 points. So I started asking whether the process is stable enough to trust.

**Screen: `docs/mandate.md`.**

[0:52] Project 2 changed three things. I gave S9 a measure, a 95% one-year loss of at most 10%, pending CIO confirmation. I wrote stop conditions before seeing results. And I added a walk-forward test: fifteen Decembers, each seeing only data up to that date. That test moved my call from Lab 15's "pilot" to "reject".

**Screen: Lab 15 table row "All 60 months: 80 / 0 / 0 / 20", then `p2/mandate.py` rule M5, then the test `test_issuer_cap_binds_when_return_needs_joby`.**

[1:15] Now one AI output I checked. In Lab 15, Codex wrote my optimizer, and on all 60 months it returned 80% T-bills and 20% JOBY. I ran that through my Lab 13 logic. JOBY is one company, and S6 caps any single issuer at 8%. The AI's optimizer had no issuer rule, so its answer broke my own mandate. I rejected it and fixed the code: Project 2 caps every non-exempt issuer, and this test proves the cap binds.

**Screen: `docs/data-card.md`, the reconciliation row.**

[1:45] A second check. Claude said Treasury's par yield curve is the same series as FRED's DGS10, which mattered because FRED was blocking my machine. In Lab 17 I'd recorded DGS10 at 5.24, 5.26 and 5.29 for late September. The Treasury file matches all three exactly, so I accepted it, and that's now a test.

**Screen: `output/report.md`, stop-condition table.**

[2:10] The biggest change in my thinking: passing the rules is the start, not the answer. Today the process passes every rule and still fails its own stop tests. I defend that in Video 3.

---

## Video 2: Code walkthrough (limit 5:00; target 4:40)

**Screen: README top.**

[0:00] Tobey Uhm, Project 2, code walkthrough. I used Claude Opus 5.5 to build this code and draft this script, and Codex GPT-5 for the earlier lab code. The analysis and decision are mine. Education, not investment advice.

**Screen: README repository map and flow line.**

[0:15] The architecture is one engine package, `p2`, with three entry points: `analysis.py` writes the frozen output, `app.py` is the web app, and `locked_test.py` runs my locked record. Everything is standard-library Python, so there's no install. The flow is data, then point-in-time loading, estimates, the optimizer plus the mandate rules, then stress, stop conditions and walk-forward, then output, then the app.

**Screen: `data/data_snapshot.json`, then `p2/data.py` `window` and `value_known_on`.**

[0:45] Data first. Two frozen files, Yahoo monthly adjusted closes and Treasury daily yields, each SHA-256 hashed. `analysis.py` refuses to run if a hash changes. In `data.py`, `window` returns the last N monthly returns ending at the decision month, and drops any ticker without a full window, which is how JOBY's SPAC history stays out. `value_known_on` takes the latest curve observation dated strictly before the decision date, the one-day lag I found in Lab 17.

**Screen: `config/mandate.json`, then `p2/mandate.py` `check`.**

[1:20] The mandate lives in a config file. `mandate.py` turns it into rules. Each returns the measured value, the limit, pass or fail, and an ID: M3 is the payout reserve, 4 times 0.75 over 100 = 3%. M5 groups weights by issuer, so a company's bond and stock count together. O1 is the CPI + 4 objective net of trading costs, R1 is my 95% loss, and G1 is turnover, which flags "needs approval" rather than failing.

**Screen: `p2/optimizer.py` `optimize`.**

[1:55] The optimizer is an exhaustive grid: every long-only mix of six assets in 5-point steps, 53,130 of them. It skips any mix over the issuer cap or under the reserve. It subtracts the trading cost of getting there from the expected return. Then it keeps the lowest-volatility mix that clears the objective and the loss limit. If nothing passes, it returns None with a diagnosis. That's a real answer, not an error.

**Screen: `p2/pipeline.py` `run_decision`, `walk_forward`, `stop_status`.**

[2:25] `run_decision` estimates on the window, builds both baselines, equal weight and inverse volatility, runs the optimizer, applies the term-spread signal, and checks every portfolio against the mandate. `walk_forward` repeats that every December from 2011, holds the weights for a year as they drift, and charges costs. If no mix passes, the process stops and holds the benchmark. `stop_status` applies my three pre-set stop tests.

**Screen: terminal: `python -m unittest discover -s tests -v` (23 OK).**

[2:55] Validation. I'm running the 23 tests. The key ones are known answers. The Lab 13 answer key: B fails three rules, with Acme at 9%. The Lab 15 answer key: 0, 20, 25, 55 at 6.51%. The Lab 17 DGS10 values. The highest-risk technical claim is no look-ahead. This test deletes every price and yield after December 2016, 2019 and 2024, reruns, and gets identical weights. All 23 pass.

**Screen: GitHub commit `066734f` (docs/locked-prediction.md), then `output/locked_test_result.md` (committed in `a458ecc`). For a live run on camera use `python locked_test.py --dry-run`; do NOT rerun the real runner, which would overwrite the recorded run time.**

[3:25] The locked changed-input test. My AI-off prediction was committed and pushed at 3:32 PM on November 23rd, commit 066734f, two minutes before the run. The runner refuses to run otherwise. I raised the CPI assumption from 2.5 to 3%, so the target goes from 6.5 to 7%. I predicted one step from T-bills to ACWI: 20% equity, about 7.6%, and REJECT holds. That matched exactly: 7.59%. Where I missed was 2022, minus 12.3%, not about 11. Going into that year, the higher target swapped 10% of T-bills for AGG, and bonds fell 13%. I expected equity risk; the miss was duration risk. The decision stays REJECT.

**Screen: README "Run it", then report stress table row "60-month window 30%".**

[4:05] To reproduce: clone, `python analysis.py`, which rewrites the output byte-for-byte, then `python app.py`. One limitation: expected returns are trailing historical means. The 60-month window moves the portfolio 30 points, and that's the failure mode the stop rule catches. Another: my S9 measure, a parametric 95% loss, didn't foresee 2022.

[4:35] That's the code. Thanks.

---

## Video 3: Committee presentation, opening with the app live (limit 5:00; target 4:45)

**Screen: the app running at localhost:8502, header with statements visible.**

[0:00] Tobey Uhm, portfolio analyst, Meridian Foundation Reserve. I used Claude Opus 5.5 to build this app and draft my script, and Codex GPT-5 for earlier lab code. The analysis and decision are mine. Education, not investment advice.

**Screen (live): scroll from the red REJECT banner to the stop-condition table; then set the window to 60 and press Run; show the verdict table and stop tests update; press Reset.**

[0:15] This is the app running live. My recommendation, in red: reject the optimizer process, 0% of the reserve. Below it are the stop conditions the app computes. Two of three are tripped. Let me change one input live: estimation window to 60 months, Run. The portfolio jumps from 85% T-bills to 55% T-bills and 45% equities. Every verdict and stop test recomputes from the same engine. Reset.

**Screen: decision-memo section 1.**

[0:50] My decision. Reject adopting the process. Put 0% of the $100 million into it. Instead, rebalance the current 60/40 to 55 to 60% ACWI, 35 to 40% AGG, and 3 to 5% T-bills. That funds the $3 million payout reserve the portfolio doesn't have today. It's 3 to 5% turnover, inside the 25% limit.

**Screen: app verdict table.**

[1:15] The baselines first. Equal weight fails rule M5: 16.7% in JOBY, one company, against an 8% limit. Inverse volatility fails the objective at 4.7%. The benchmark itself fails M3: no payout reserve. My constrained portfolio passes every rule: 85% BIL, 15% ACWI, 6.77% expected. But it passes only because global equities returned 20.8% a year over the last 36 months. An 85% cash portfolio for a seven-year CPI + 4 mandate is the Lab 13 trap: compliant, and still wrong.

**Screen: app walk-forward chart and table.**

[1:55] The evidence. Walk-forward from 2012 to October 2026: each December the process saw only the data available then. It earned 6.33% a year against 7.68% for the benchmark, below the 6.5% hurdle. It found no feasible portfolio in 3 of 15 years. It broke the 25% turnover limit in 12 of 14 rebalances. And it lost 10.8% in 2022, beyond the 10% limit. Shorter or longer windows don't fix it.

**Screen: app stress table, then signal card.**

[2:30] The stress run. Costs, constraints and a 1-point equity haircut barely move it. The window does: 30 points at 60 months. My point-in-time signal, the Treasury 10-year minus 3-month spread known the day before, never changed a rebalance, and its monthly t-stats are 1.07 and 0.08. Today it reads +0.80. I don't count it as evidence for anything.

**Screen: report "recommended reserve range" table.**

[2:55] I'm not claiming the fallback is perfect. The reserve range returned 7.2 to 7.7% over the same period, but it lost about 15% in 2022. No strategy I tested met both CPI + 4 and a 10% loss limit. So the real issue is the mandate, not the optimizer.

**Screen: app triggers table.**

[3:20] What I'll monitor:
- Payout reserve below 3%: top up T-bills.
- Year-to-date loss worse than 7%: report to you.
- Each December I rerun the optimizer on paper. If the 36- versus 60-month shift is 25 points or less, and no walk-forward year is below -10% under a measure the CIO confirms, I'll bring back a pilot of at most 10%.
- If the curve inverts at a rebalance, I log the signal's first live test.

**Screen: memo committee ask.**

[3:55] Three asks. One: vote to reject the optimizer process. Two: approve the rebalance to 55-60 ACWI, 35-40 AGG, 3-5 BIL. Three: CIO, tell us which gives way, the CPI + 4 objective or the 10% loss limit, because this evidence says you can't have both. Until then, no optimizer should run this reserve. Thank you.

**Prepared answers (not part of the timed script; for the partner rehearsal):**
- *"Isn't 85% T-bills safer?"* Safer this year, yes. But over seven years it needs 20%-a-year equity returns to hit CPI + 4. That's the estimate the 60-month window contradicts.
- *"Why not just use the 60-month window?"* It returned 6.65% against 7.00% for the benchmark over its holdout, with a -13.6% year. Picking the window that looks best is the overfitting I'm rejecting.
- *"What can't your system establish?"* Forward-looking returns, and whether 2022 was a one-off. That's why the answer is a paper track with triggers, not "never".
