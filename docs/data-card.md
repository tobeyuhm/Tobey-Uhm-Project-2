# Data cards: the signal and the prices

## 1. Signal: Treasury term spread (10-year minus 3-month), known before the rebalance

| Field | Evidence |
|---|---|
| What it measures | The slope of the U.S. Treasury curve: the 10-year par yield minus the 3-month par yield, in percentage points. When it is negative (inverted), holding duration (IEF) is not paid a term premium over T-bills (BIL). |
| Source | U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates, downloaded as CSV, one file per year, 2008-2026 (`tools/download_data.py`). Treasury publishes these rates; the Federal Reserve's H.15 release and FRED's `DGS10` / `DGS3MO` series carry the same constant-maturity values. |
| Why not FRED this time | Lab 17 used FRED/ALFRED `DGS10`. From this machine on 2026-11-23, `fred.stlouisfed.org/graph/fredgraph.csv` reset every connection (curl error 000, "Connection was reset"), so I went to the upstream publisher. **Reconciliation to Lab 17:** Treasury's 10-year on 2026-09-28 / 09-29 / 09-30 is 5.24% / 5.26% / 5.29%. Those are the exact DGS10 values in my Lab 17 three-value check, so the two sources agree. |
| Units | Percent, bond-equivalent (par) yield; the spread is in percentage points. |
| Frequency | Daily, U.S. government-securities business days. 4,722 days with both tenors from 2008-01-02 to 2026-11-20. |
| When a value is known | Treasury posts a day's curve that same evening. The rule is stricter: a decision dated D uses only observations dated before D (`TreasuryCurve.value_known_on`). The month-end decision on 2026-10-30 therefore uses 2026-10-29 (10-year 4.98%, 3-month 4.18%, spread +0.80). This is the same one-business-day lag Lab 17 found for DGS10. |
| Revisions | Treasury does not revise published par yields in normal practice. Lab 17's ALFRED test found 0 revised same-date DGS10 values over 2020-2026. The frozen file is hashed in `data/data_snapshot.json`, so a later re-download cannot change a result without the hash test failing. |
| Point-in-time test | `tests/test_engine.py::PointInTime` checks three things: (a) the reading for 2026-10-30 is dated 2026-10-29; (b) every reading is dated before its decision date; (c) the decision for each of 2016-12, 2019-12 and 2024-12 is identical whether or not the later prices and yields are deleted from memory. |
| Rule (pre-specified) | At each December rebalance: if the spread is < 0, move the constrained portfolio's IEF weight into BIL. Otherwise, keep IEF. |
| Exclusions | Days missing either tenor are dropped. 1.5-month and 4-month tenors are ignored. |
| Licence | U.S. government work (public domain). |
| Evidence it works | **None that is reliable.** Monthly, 2008-05 to 2026-10, IEF minus BIL in the following month averaged +1.79%/yr when the curve was positive (t = 1.07, 183 months) and +0.34%/yr when inverted (t = 0.08, 39 months). At the 15 annual rebalances the curve was inverted only in Dec 2022 and Dec 2023, and the process had already stopped in both years. In the walk-forward, signal-on and signal-off results are identical. |
| My call | Keep the rule as a monitored, pre-registered test (trigger in the memo). Do not count it as a reason to adopt. |

## 2. Prices: six funds and one stock, monthly adjusted closes

| Field | Evidence |
|---|---|
| Source | Yahoo Finance chart API, `interval=1mo`, `adjclose`, downloaded 2026-11-23 17:47 UTC by `tools/download_data.py` (the Lab 15 `download_prices.py` method, extended). |
| Coverage | 2008-04 (ACWI's first full month) to 2026-10 (last complete month before the download). November 2026 is excluded as incomplete. |
| Definition | Month-end close, adjusted for splits and distributions (dividends reinvested). ETF adjusted closes are already net of each fund's expense ratio, because fees accrue in NAV. I therefore do **not** subtract expense ratios again. I do charge trading costs on turnover (`config/mandate.json`). |
| Transformations | Simple monthly return P_t / P_(t-1) - 1. Expected return = mean x 12. Volatility = sample sd x sqrt(12). Covariance = sample covariance x 12. These are the Lab 15 conventions, and the Lab 15 known answer reproduces through them. |
| Exclusion | JOBY before 2021-08: those are Reinvent Technology Partners SPAC prices (trust value near $10), not Joby's operating company. They are set to missing in `p2/data.py`, so JOBY's first return is 2021-09. JOBY enters an estimation window only once it has the full window (36 months, from late 2024). |
| Revisions (found) | Adjusted closes are **restated** after every distribution. My Lab 15 file (downloaded 2026-10-22) had BIL at 91.377 for 2026-09. This download has 91.070. IEF moved from 89.003 to 88.701 and LQD from 101.741 to 101.351. JOBY, which pays no distributions, is unchanged at 6.05. The monthly **returns**, however, match the Lab 15 file to within 0.0001 percentage points for every month and ticker: the adjustment rescales history, it does not change returns. Rule: never compare price *levels* across downloads. The snapshot hash pins this download. |
| Known when | A month's close is known after its last trading day. A decision at month-end M uses returns through M and trades from M+1. The walk-forward earns month M+1 returns on the new weights. |
| Licence | Yahoo Finance's terms restrict redistribution of its data. The CSV is included, attributed to Yahoo, only so the course's graders can reproduce this educational result. It is not offered for reuse, and it should be replaced with a licensed source or removed if this repository were used beyond the course. |

## 3. Mandate inputs that are assumptions, not data

| Input | Value | Basis | Stressed |
|---|---|---|---|
| CPI assumption | 2.5% a year | The Meridian training estimate from the Lab 15 course case. It is an assumption, not a sourced CPI forecast; FRED's CPI series was unreachable from this machine on 2026-11-23 | 1.5% and 3.5% (stress), 3.0% (locked test) |
| Trading costs | 2-3 bps per unit traded for ETFs, 25 bps for JOBY | Typical half-spread for large ETFs; wider for a volatile single stock | x4 and x20 |
| Current holdings | 60% ACWI / 40% AGG | Assumed equal to the S4 benchmark | n/a (turnover is measured from it) |
| Reserve-eligible | BIL and IEF | S3 allows "cash or daily-liquid government securities"; both funds hold only U.S. Treasuries and trade daily | Reserve minimum 10% stress |
| Loss measure | One-year 95% parametric loss <= 10% | My operationalisation of S9 (Lab 13 left it unverifiable) | 8% stress; realised worst year monitored |

## 4. Checks still to tick by hand before submission

- [x] Treasury 10-year for 2026-09-28/29/30 equals Lab 17 DGS10 (5.24 / 5.26 / 5.29%): matched in the frozen file.
- [x] Treasury 10-year and 3-month for 2026-10-29 equal 4.98% and 4.18% on treasury.gov (checked by hand, 2026-11-23: match).
- [x] Yahoo history page for ACWI shows an October 2026 adjusted close near 156.04 (checked by hand, 2026-11-23: match).
