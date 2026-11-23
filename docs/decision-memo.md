# Decision Memo: Meridian Foundation Reserve, optimizer process review

**AI use.** I used Claude (Anthropic; Claude Code desktop app, model Claude Opus 5.5, Nov. 23, 2026) to build the app's code and tests, and to draft this memo, the validation record and the video scripts. I used OpenAI Codex (GPT-5) for the Lab 13-17 code this project grows from. The analysis and the decision are mine. Full record: `docs/validation-and-ai-use.md`.
**Education, not investment advice.** A FIN 43900 course project on a fictional client.

To: Meridian Foundation investment committee and CIO · From: Tobey Uhm, portfolio analyst · Decision as of **Oct. 30, 2026** (prices through October 2026 month-end; Treasury curve known Oct. 29) · App: `python app.py` · Visible output: `output/report.md`

## 1. Recommendation: REJECT the process; rebalance only to fund the payout reserve

- **Allocation to the optimizer process: 0%** of the $100M reserve. I keep it on a paper track and rerun it each December.
- **Reserve allocation range: ACWI 55-60%, AGG 35-40%, BIL 3-5%.** This means moving $3-5M from the current 60/40 into T-bills, which covers the $3.0M twelve-month payout reserve the current holdings lack (rule M3). One-way turnover is 3-5%, inside the 25% limit.
- **Committee ask:**
  1. Vote to reject the optimizer process.
  2. Approve the compliance rebalance.
  3. Direct the CIO to say which gives way, the CPI + 4% objective (S2) or the 10% loss limit (S9). On this evidence, both cannot be met.
- **What reverses it (REJECT -> PILOT, max 10% of the reserve):** the CIO confirms the loss measure, **and** a December rerun shows the 36- vs 60-month allocation shift is <= 25%, **and** no walk-forward calendar year is below -10%.

## 2. The mandate and what each portfolio does under it

The mandate is the Lab 13 common case encoded as rules (`docs/mandate.md`): objective O1 (expected return net of costs >= 6.5%), payout reserve M3 (BIL + IEF >= 3.0%), liquidity M4, single company <= 8% M5 (JOBY is the only non-exempt holding), long-only M1/M2, risk R1 (95% one-year loss <= 10%, my operationalisation of S9), and turnover G1 (<= 25% without approval). The 36-month window is Nov 2023 to Oct 2026.

| Portfolio (Oct. 30, 2026) | Weights | Net expected return | Volatility | Verdict |
|---|---|---:|---:|---|
| Equal weight (baseline 1) | 16.7% each of six | 10.67% | 15.42% | **FAIL M5** (JOBY 16.7% > 8%), **R1** (14.7% loss) |
| Inverse volatility (baseline 2) | BIL 90%, rest 10% | 4.71% | 0.82% | **FAIL O1** (4.7% < 6.5%) |
| **Constrained (my process)** | **BIL 85%, ACWI 15%** | **6.77%** | **1.76%** | **PASS every rule** (85% turnover needs approval) |
| Benchmark 60/40 (reference) | ACWI 60%, AGG 40% | 14.64% | 8.28% | **FAIL M3** (0% payout reserve) |

The constrained portfolio passes, but only because ACWI's trailing 36-month mean is **20.8% a year**. Fifteen percent equity clears 6.5% on that estimate. This is the Lab 13 lesson: a portfolio that passes every checkable rule (85% T-bills) can still be wrong for a seven-year CPI + 4% client.

## 3. Evidence the process is not adoptable

**Stop conditions (set before the results, `config/mandate.json`):** S1, a feasible portfolio exists: **ok**. S2, no adjacent stress moves the portfolio more than the 25% turnover limit: **TRIPPED**, because a 60-month window moves it 30 points (to BIL 55% / ACWI 45%). S3, walk-forward worst calendar year >= -10%: **TRIPPED** at 2022, -10.8%. Two of three trip, so the process stops.

**Walk-forward holdout, Jan 2012 - Oct 2026** (each December the process sees only data to that date; costs charged):

| Strategy | Annual return | Volatility | Max drawdown | Worst year |
|---|---:|---:|---:|---:|
| Constrained (my process) | 6.33% | 7.07% | -13.1% | 2022: -10.8% |
| Benchmark 60/40 | 7.68% | 9.00% | -21.2% | 2022: -16.2% |
| Equal weight | 3.67% | 6.98% | -15.4% | 2022: -12.6% |
| Inverse volatility | 1.68% | 0.98% | -2.6% | 2022: -1.4% |

The process trailed the benchmark by 1.35 points a year and missed the 6.5% hurdle. It was infeasible (stopped) in 3 of 15 Decembers. Its turnover broke the 25% limit in **12 of 14** later rebalances, so the allocation follows the trailing window, not the client. No window rescues it. With 24, 60 and 120 months it returned 5.06%, 6.65% and 8.09%, against 7.06%, 7.00% and 9.10% for the benchmark over each window's holdout, and every window lost more than 10% in 2022.

**Signal.** I used the Treasury 10-year minus 3-month spread, known one business day before each rebalance (data card: `docs/data-card.md`). Rule: an inverted curve moves IEF into BIL. It never changed a rebalance, because it was inverted only in Dec 2022 and Dec 2023, when the process had already stopped. Monthly, it shows no reliable edge (t = 1.07 positive, 0.08 inverted). Today it reads +0.80 points: keep IEF (none is held).

**Stress at the decision date** (estimates, window, costs, constraints; `output/report.md`):

- ACWI -1 pt, bonds -1 pt, JOBY at 0%, costs x4, issuer limit 0%, a 10% reserve, and an 8% loss limit each leave the mix unchanged.
- ACWI -2 pts, costs x20 and CPI +/-1 pt move it 5 points.
- The window moves it most: 24 months shifts it 10 points, 60 months 30 points, 120 months 25 points.
- Trading costs are not the risk. Estimation is.

## 4. Why the fallback is the 60/40 plus a T-bill reserve, and its limits

The reserve range passes every hard rule. Over the same holdout it returned 7.20-7.67% a year, above the 6.5% hurdle. It also lost 15.3-15.8% in 2022. No strategy I tested met both S2 and S9 on realised data, which is why ask 3 goes to the CIO rather than to an optimizer. The ex-ante R1 measure did not anticipate 2022: the benchmark showed a 95% loss of only -1.0% (a gain) on today's estimates. That parametric measure understates tail loss, and it is the main limitation of my mandate encoding.

## 5. Risks, assumptions and monitoring triggers

**Assumptions:**

- CPI is 2.5%; stressed at 1.5% and 3.5%, the decision is unchanged.
- Trading costs are 2-3 bps for ETFs and 25 bps for JOBY.
- Current holdings equal the benchmark.
- Historical means are estimates, not forecasts.
- The realised test uses a fixed 6.5% hurdle, not realised CPI.

**Data:** Yahoo adjusted closes (restated after distributions; returns verified unchanged against Lab 15) and Treasury par yields (matching Lab 17's DGS10 to the tick).

| Monitor | Trigger | Action |
|---|---|---|
| Payout reserve (BIL + IEF) | below 3.0% at any month-end | top up BIL from AGG |
| Year-to-date reserve return | worse than -7% | report to committee (early warning on the 10% limit) |
| Optimizer paper track, each December | window shift <= 25% and no adjacent stress infeasible | re-open a pilot proposal (max 10%) |
| Walk-forward worst year under a CIO-confirmed measure | no full year below -10% | re-open a pilot proposal |
| Term spread (known T-1) | negative at a December rebalance | log the signal's first live test; no capital moves |
| JOBY (Project 1) | FAA type certificate and price <= 75% of my Project 1 base value | re-review as a satellite (<= 8%) in Project 1's framework |

**Locked Changed-Input Record** (`docs/validation-and-ai-use.md`, section 5). I raised CPI from 2.5% to 3.0% (target 7.0%), predicted with AI off, locked in commit `066734f` before the run. Today's mix moved exactly as predicted, to BIL 80 / ACWI 20 at 7.59%, and REJECT held. The walk-forward was worse than I expected: 2022 fell 12.3% and there were 4 stops. The higher target swapped T-bills for AGG before the 2022 bond sell-off, so a higher inflation assumption adds duration risk and strengthens REJECT.
