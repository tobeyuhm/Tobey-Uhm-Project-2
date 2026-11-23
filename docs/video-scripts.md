# Video scripts: Project 2 (Meridian Reserve process review)

Scripts drafted with Claude Opus 5.5 (disclosed in `docs/validation-and-ai-use.md`). I read, adapt and deliver them, and I own every spoken claim. Rehearse each section until you can say it without reading. Graders look for ownership, and "my system cannot establish that" is an acceptable answer.

Timing: about 130 spoken words a minute. The `[0:00]` marks are targets. **Bold = what is on screen.**

---

## What every video needs (the course's grading rules)

| Requirement | Video 1 (3:00 max) | Video 2 (5:00 max) | Video 3 (5:00 max) |
|---|---|---|---|
| Opens with the two statements (which AI and for what, analysis and decision mine; education, not investment advice) | 0:00 | 0:00 | 0:00, spoken over the live app |
| Small webcam view the whole time | yes | yes | yes |
| Its one unique job | How the system and your thinking changed, who or what drove each change, and one AI output you checked with its disposition | Architecture, data flow, key functions, financial logic, how to reproduce, one test aimed at the highest-risk claim run on screen, one failure mode | Opens with the app running live, then the decision first, range, evidence, assumptions, risks, triggers, ending with a committee ask |
| Not this | Reading the README or a change table | Showing only the app UI, or reading the README | Repeating the code walkthrough |
| Graders stop at | 3:00 | 5:00 | 5:00 |

## Filming checklist

**Before you record (all videos):**
- Run `python app.py` in the project folder and leave it open at http://localhost:8502. Use the local app on camera: it reruns in about 5 s, while Render's free tier takes about 15 s. Mention the public link in Video 3.
- Open these as tabs or windows, in script order:
  - the GitHub repo;
  - `README.md`;
  - `docs/mandate.md`;
  - `prior-work/lab13/lab13_meridian.md` and `prior-work/lab15/lab15_portfolio_stability.md`;
  - `docs/data-card.md`;
  - `output/report.md`;
  - `docs/decision-memo.md`;
  - VS Code with `p2/`;
  - a terminal in the project folder.
- Screen recorder with a webcam inset (OBS, Zoom or Loom). Clear audio matters; polish doesn't.
- Close notifications, and any AI chat windows on screen.
- Zoom the editor and browser to about 125% so code and numbers are readable.

**After recording:**
- Upload each video to YouTube as **Unlisted**, with a descriptive title: "Tobey Uhm Project 2 Video 1: How my system changed", "... Video 2: Code walkthrough", "... Video 3: Committee presentation".
- Check each duration is under its limit.
- Open YouTube's auto-transcript. Fix tickers (BIL, IEF, AGG, LQD, ACWI, JOBY), names and every number, then paste the corrected text into `docs/transcript-video-N.txt`, replacing the draft.
- Fill the manifest with the URL, YouTube ID, duration and the timestamp list (use the `[m:ss]` marks below, adjusted to your recording). Then open each link while logged out and tick the access check.

---

## Video 1: How my system and my thinking changed, plus one AI output I checked (limit 3:00; target 2:40)

**Screen: README top, the two statements visible. Webcam on.**

[0:00] I'm Tobey Uhm, FIN 439 Project 2. Two statements first. I used Claude, Opus 5.5 in Claude Code, to build this app's code, tests and documents and to draft my scripts, and OpenAI Codex, GPT-5, for the Lab 13 to 17 code it grows from. The analysis and the decision are mine. This is education, not investment advice.

**Screen: `prior-work/lab13/lab13_meridian.md`, the S1-S10 table.**

[0:22] My system started in Lab 13 as a rule checker. My thinking then was: if a portfolio passes every rule, it's acceptable.

**Screen: `prior-work/lab15/lab15_portfolio_stability.md`, the window table, then the partner-attack section.**

[0:32] Two things changed that. Course instruction in Lab 15: switching the window from 60 to 36 months moved my optimizer 60 points. And a peer challenge: my partner Eric cut JOBY's expected return to 10%, and the optimizer *raised* JOBY to 45%. So I stopped asking "what's the best mix" and started asking "is this process stable enough to trust".

**Screen: `docs/mandate.md`, then the stop-condition table in `output/report.md`.**

[0:58] That drove three changes in Project 2, from my own analysis. I gave S9 a measure, a 95% one-year loss of at most 10%. I wrote stop conditions before seeing results. And I added a walk-forward test, where each December sees only past data. That evidence was enough to move me from Lab 15's "pilot" to "reject": out of sample, the process lost to the 60/40 and tripped its own stop tests, so it isn't a single bad estimate.

**Screen: Lab 15 table row "All 60 months: 80 / 0 / 0 / 20", then `p2/mandate.py` rule M5, then `tests/test_engine.py::test_issuer_cap_binds_when_return_needs_joby`.**

[1:30] One AI output I checked. In Lab 15, Codex wrote my optimizer, and on all 60 months it returned 80% T-bills and 20% JOBY. I ran that through my Lab 13 logic. JOBY is one company, and S6 caps any single issuer at 8%. Codex's optimizer had no issuer rule. Disposition: corrected. Project 2 caps every non-exempt issuer, and this test proves the cap binds.

**Screen: `docs/data-card.md`, the reconciliation row.**

[1:58] A second check, from this build. Claude said Treasury's par yield curve is the same series as FRED's DGS10. In Lab 17 I'd recorded DGS10 at 5.24, 5.26 and 5.29. The Treasury file matches all three exactly. Disposition: accepted, and it's now a test.

**Screen: `output/report.md`, the stop-condition table.**

[2:18] The biggest change in my thinking: passing the rules is the start, not the answer. Today the process passes every rule and still fails its own stop tests.

---

## Video 2: Code walkthrough (limit 5:00; target 4:20)

**Screen: README top. Webcam on.**

[0:00] Tobey Uhm, Project 2, code walkthrough. I used Claude Opus 5.5 to build this code and draft this script, and Codex GPT-5 for the earlier lab code. The analysis and decision are mine. Education, not investment advice.

**Screen: README repository map and flow line.**

[0:14] The architecture is one engine package, `p2`, with three entry points: `analysis.py` writes the frozen output, `app.py` is the web app, and `locked_test.py` runs my locked record. It's standard-library Python, so there's nothing to install. The flow is: frozen data, point-in-time loading, estimates, optimizer and mandate rules, then stress, stop tests and walk-forward, then output and the app.

**Screen: `data/data_snapshot.json`, then `p2/data.py` `window` and `value_known_on`.**

[0:40] Data. Two frozen files, Yahoo monthly adjusted closes and Treasury daily yields, both SHA-256 hashed; `analysis.py` refuses to run if a hash changes. `window` returns the last N monthly returns ending at the decision month, which keeps out the future and JOBY's pre-merger SPAC prices. `value_known_on` only returns a yield dated before the decision: the one-day lag from Lab 17.

**Screen: `config/mandate.json`, then `p2/mandate.py` `check`.**

[1:08] The mandate is a config file, and `mandate.py` turns it into rules that return the measured value, the limit, pass or fail, and an ID. M3 is the payout reserve: 4 times 0.75 over 100 is 3%. M5 groups weights by issuer. O1 is CPI + 4 net of trading costs. R1 is my 95% loss. G1 is turnover, which flags "needs approval" instead of failing.

**Screen: `p2/optimizer.py` `optimize`.**

[1:36] The optimizer tries every long-only mix of six assets in 5-point steps, 53,130 of them. It drops any mix over the issuer cap or under the reserve. It subtracts the trading cost from the expected return, and keeps the lowest-volatility mix that clears the objective and the loss limit. If none passes, it returns None with a diagnosis. That's a real answer, not an error.

**Screen: `p2/pipeline.py` `run_decision`, `walk_forward`, `stop_status`.**

[2:02] `run_decision` estimates, builds both baselines, equal weight and inverse volatility, runs the optimizer, applies the term-spread signal and checks every portfolio. `walk_forward` repeats that each December from 2011, lets the weights drift for a year and charges costs; if nothing passes, it holds the benchmark. `stop_status` applies my three pre-set stop tests.

**Screen: terminal, run `python -m unittest discover -s tests -v` live and let it finish (23 OK).**

[2:28] Validation, run live. The key tests are known answers: the Lab 13 answer key, the Lab 15 answer key at 6.51%, and the Lab 17 DGS10 values. The highest-risk technical claim is no look-ahead. This test deletes every price and yield after December 2016, 2019 and 2024, reruns, and gets identical weights. All 23 pass.

**Screen: GitHub commit `066734f` (docs/locked-prediction.md), then `output/locked_test_result.md`. If you show a live run, use `python locked_test.py --dry-run`; never rerun the real runner, which would overwrite the recorded run time.**

[2:55] The locked changed-input test. My AI-off prediction was committed and pushed at 3:32 PM on November 23rd, commit 066734f, before the run; the runner refuses otherwise. I raised CPI from 2.5 to 3%, so the target goes from 6.5 to 7%. I predicted one grid step from T-bills to ACWI, about 7.6%, and REJECT holding. Today's weights matched exactly, because the next 5-point step is the only way to clear 7%. I missed on 2022: minus 12.3%, not about 11. Going into that year the higher target swapped 10% of T-bills for AGG, and bonds fell 13%. I expected equity risk; it was duration risk. REJECT holds.

**Screen: README "Run it" section, then the report's stress-table row "60-month window 30%".**

[3:40] To reproduce: clone or download the ZIP, run `python analysis.py`, which rewrites the output byte-for-byte, then `python app.py`. The main failure mode is the estimates: they're trailing historical means, and a 60-month window moves the portfolio 30 points. That's what stop test S2 catches. A second limitation: my parametric loss measure didn't foresee 2022.

[4:05] That's the code.

---

## Video 3: Committee presentation, opening with the app running live (limit 5:00; target 4:30)

**Screen: the app running at localhost:8502, header and statements visible. Webcam on.**

[0:00] Tobey Uhm, portfolio analyst, Meridian Foundation Reserve. I used Claude Opus 5.5 to build this app and draft my script, and Codex GPT-5 for earlier lab code. The analysis and decision are mine. Education, not investment advice.

**Screen (live): scroll from the red REJECT banner to the stop-condition table. Set the window to 60, press Run, and wait. Show the verdict table and stop tests updating, then press Reset.**

[0:14] This is the app, running live. My recommendation, in red: reject the optimizer process, 0% of the reserve. Below it are the stop conditions the app computes, and two of three are tripped. One live change: estimation window to 60 months, Run. The portfolio jumps from 85% T-bills to 55% T-bills and 45% equities, and every verdict and stop test recomputes. Reset.

**Screen: decision memo, section 1.**

[0:48] My decision. Reject adopting the process, with 0% of the $100 million in it. Rebalance the current 60/40 to 55 to 60% ACWI, 35 to 40% AGG, and 3 to 5% T-bills. That funds the $3 million payout reserve the portfolio lacks today, with 3 to 5% turnover, inside the 25% limit.

**Screen: app verdict table.**

[1:10] The baselines. Equal weight fails M5: 16.7% in JOBY, one company, against an 8% limit. Inverse volatility fails the objective at 4.7%. The benchmark fails M3, with no payout reserve. My constrained portfolio passes every rule: 85% BIL, 15% ACWI, 6.77% expected. But it passes only because global equities returned 20.8% a year over the last 36 months. An 85% cash portfolio for a seven-year CPI + 4 mandate is compliant, and still wrong.

**Screen: app walk-forward chart and table.**

[1:48] The evidence. Walk-forward from 2012 to October 2026, each December seeing only the data available then. It earned 6.33% a year against 7.68% for the benchmark, below the 6.5% hurdle. It had no feasible portfolio in 3 of 15 years and broke the turnover limit in 12 of 14. It lost 10.8% in 2022, past the 10% limit. Other windows don't fix it.

**Screen: app stress table, then signal card.**

[2:20] Stress. Costs, constraints and a 1-point equity haircut barely move it; the window moves it 30 points. My point-in-time signal, the 10-year minus 3-month Treasury spread known the day before, never changed a rebalance, with monthly t-stats of 1.07 and 0.08. Today it reads +0.80. I give it no weight.

**Screen: report, "recommended reserve range" table.**

[2:45] Assumptions and limits. CPI at 2.5%; my locked test at 3% kept REJECT, but deepened 2022 to minus 12.3%. The fallback isn't perfect either: the reserve range earned 7.2 to 7.7%, but lost about 15% in 2022. No strategy I tested met both CPI + 4 and a 10% loss limit.

**Screen: app triggers table.**

[3:10] What I'll monitor:
- Payout reserve below 3%: top up T-bills.
- Year-to-date loss worse than 7%: report to you.
- Each December I rerun the optimizer on paper. If the window shift is 25 points or less, and no walk-forward year is below minus 10% under a measure the CIO confirms, I'll bring back a pilot of at most 10%. That's what reverses REJECT.

**Screen: memo committee ask; the public link visible in the browser.**

[3:40] Three asks. One: vote to reject the optimizer process. Two: approve the rebalance to 55-60 ACWI, 35-40 AGG, 3-5 BIL. Three: CIO, tell us which gives way, the CPI + 4 objective or the 10% loss limit, because this evidence says you can't have both. Anyone on the committee can rerun this at meridian-reserve-review.onrender.com. Thank you.

**Prepared answers (not part of the timed script; for rehearsal):**
- *"Isn't 85% T-bills safer?"* Safer this year, yes. But over seven years it needs 20%-a-year equity returns to hit CPI + 4. That's the estimate the 60-month window contradicts.
- *"Why not just use the 60-month window?"* It returned 6.65% against 7.00% for the benchmark over its holdout, with a -13.6% year. Picking the window that looks best is the overfitting I'm rejecting.
- *Partner's question: "The 60/40 doesn't hold the $3M reserve. How much of its 1.35-point lead survives if it must?"* Most of it, depending on the T-bill share. Over the same holdout, the reserve-compliant mixes returned:
  - ACWI 60 / AGG 37 / BIL 3: 7.67%, a lead of 1.34 pts over my process.
  - The 57.5 / 37.5 / 5 midpoint: 7.44%, a lead of 1.11 pts.
  - ACWI 55 / AGG 40 / BIL 5: 7.20%, a lead of 0.87 pts.

  The reserve costs 0.01-0.48 pts a year, but every version still lost about 15% in 2022. That's why the CIO question stands.
- *"What can't your system establish?"* Forward-looking returns, and whether 2022 was a one-off. That's why the answer is a paper track with triggers, not "never".
