# My mandate: Meridian Foundation Reserve (from Lab 13)

**Client:** Meridian Foundation Reserve. This is the fictional Lab 13 common case: a $100 million reserve that pays out $0.75 million every quarter. **User of this app:** the foundation's investment committee and CIO. **Horizon:** seven years, rebalanced annually (S1). **Decision:** adopt, allocate to, rebalance, pilot or reject a constrained-optimizer process for the reserve.

| CIO statement (Lab 13) | My Lab 13 type | How Project 2 encodes it | Rule id in the app |
|---|---|---|---|
| S1 Seven-year horizon, annual rebalancing | Hard constraint | The walk-forward rebalances every December | - |
| S2 CPI + 4% net of costs, rolling five years | Objective | Expected return minus trading cost >= CPI assumption (2.5%) + 4% = 6.5% | O1 |
| S3 Twelve months of payouts in cash or daily-liquid governments | Hard constraint | BIL + IEF >= 4 x 0.75 / 100 = 3.0% | M3 |
| S4 Benchmark 60% global equities / 40% U.S. IG bonds | Preference (comparison) | 60% ACWI / 40% AGG; also assumed to be today's holdings | reference row |
| S5 Long-only | Hard constraint | Weights sum to 100%; none negative | M1, M2 |
| S6 No single issuer above 8% | Hard constraint | JOBY (the only single company) <= 8%; funds and Treasury exempt | M5 |
| S7 Turnover <= 25% a year without approval | Hard constraint (governance) | One-way turnover from current holdings; above 25% = "needs committee approval" | G1 |
| S8 >= 90% redeemable in five business days | Hard constraint | All holdings settle T+1, so this passes by construction (recorded honestly as non-binding) | M4 |
| S9 "No calendar-year loss greater than 10%" | Unverifiable promise in Lab 13 | **My operationalisation:** one-year 95% parametric loss -(mu - 1.645 sigma) <= 10% (ex ante), plus the realised worst calendar year in the walk-forward (ex post, stop test S3). Needs CIO confirmation. | R1 |
| S10 Nothing says what to optimise | Missing | **My choice:** minimise volatility subject to every rule above (Lab 13's question to the CIO, answered with "total variance"). | - |

**Universe:** BIL (T-bills, payout reserve), IEF (7-10y Treasuries), AGG (U.S. aggregate IG, the benchmark bond sleeve), LQD (IG corporates), ACWI (global equities, the benchmark equity sleeve), and JOBY (my Project 1 company, as a capped single-company satellite). Lab 15 used BIL, IEF, LQD and JOBY. I added ACWI and AGG because the S4 benchmark cannot be built without them.

**Risk measure and limits:** volatility (annualised sd of monthly returns) is what the optimiser minimises. The limit is the 95% one-year loss <= 10% (R1). The realised worst calendar year must be no worse than -10% (S3 stop test).

**What Lab 13 taught that still matters:** a portfolio can pass every checkable rule and still be wrong for the client. Lab 13's all-cash candidate D was that case. Today's optimizer answer is a version of it: 85% T-bills, passing only because of a 20.8% trailing equity mean.

**The question for the CIO** (updated from Lab 13): on Jan 2012 - Oct 2026 evidence, none of the four distinct walk-forward strategies (the signal-off variant is identical to the process) met both the CPI + 4% objective and a -10% worst calendar year. Which gives way: the return objective (S2) or the loss limit (S9)?
