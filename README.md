# Meridian Reserve: Process Review App (FIN 43900 Project 2)

**AI use.** I used Claude (Anthropic; Claude Code desktop app, model Claude Opus 5.5, Nov. 23, 2026) to build this app's code, tests and documents and to draft the video scripts. I used OpenAI Codex (GPT-5) for the Lab 13-17 code this project grows from. The analysis and the decision are mine. Full record: [`docs/validation-and-ai-use.md`](docs/validation-and-ai-use.md).
**Education, not investment advice.** A course project on a fictional client (Lab 13's Meridian Foundation Reserve). Nothing here recommends a security to anyone.

Tobey Uhm · Investment Management Application · decision as of **Oct. 30, 2026**

## The decision

The **investment committee of the Meridian Foundation's $100M reserve** must decide whether to adopt, allocate to, rebalance, pilot or reject a **constrained minimum-volatility optimizer** for the reserve. The process runs under the Lab 13 mandate: CPI + 4% net of costs, a $3M payout reserve, long-only, an 8% single-company limit, 25% turnover, 90% liquid in five days, and a 10% loss limit. Horizon: seven years, rebalanced each December.

**Result (frozen): REJECT. Allocate 0% to the process.** Rebalance the existing 60/40 to **ACWI 55-60% / AGG 35-40% / BIL 3-5%** to fund the payout reserve.

- The process trips 2 of its 3 pre-set stop conditions. A 60-month window moves it 30 points (limit 25%), and it lost 10.8% in 2022 (limit 10%).
- Out of sample (Jan 2012 - Oct 2026) it returned **6.33%/yr against 7.68%** for the benchmark.
- Committee ask 3 goes to the CIO: the CPI + 4% objective and the 10% loss limit cannot both be met on this evidence.

## See the result without running anything

- [`output/report.md`](output/report.md): mandate, estimates, both baselines and my portfolio with verdicts, signal and data card, stress run, stop conditions, walk-forward, reserve-range check, triggers.
- [`docs/decision-memo.md`](docs/decision-memo.md): the committee memo.
- [`output/visible_output.json`](output/visible_output.json): every number the app's frozen panel reads.

## Run it (clean Windows/macOS/Linux machine, about 2 minutes)

Needs Python 3.10 or newer. **No third-party packages**: the engine and the web app use only the standard library, so there is no `pip install`.

```bash
git clone https://github.com/tobeyuhm/Tobey-Uhm-Project-2.git
cd Tobey-Uhm-Project-2
python analysis.py                         # rebuilds output/ from the frozen data (about 10 s)
python -m unittest discover -s tests -v    # 24 validation tests
python app.py                              # opens http://localhost:8502
```

On macOS/Linux, use `python3` if `python` is Python 2. To use another port: `PORT=8600 python app.py` (PowerShell: `$env:PORT=8600; python app.py`). Stop the app with Ctrl+C.

**Using the app.** The red banner is the frozen recommendation. Under **Change an input and rerun** you can set the estimation window, shift an expected return, override JOBY, scale trading costs, or change the single-company limit, payout reserve, loss limit or CPI. You can also turn the signal off. Press **Run**. The stop conditions, every portfolio's mandate verdict (with the failing rule), the stress table and the walk-forward all recompute through the same engine, in about 5 seconds. **Reset to base case** returns to the frozen inputs. `/api/run?window=60` returns the same run as JSON.

Optional, needs internet: `python tools/download_data.py` re-downloads the data. This **changes** the frozen files (new months, restated adjusted closes), and `analysis.py` will then refuse to run until you accept the new snapshot. Do not run it to reproduce the submitted result.

## Repository map

| Path | Role |
|---|---|
| `config/mandate.json` | The mandate as data: assets, limits, objective, benchmark, signal rule, stop conditions |
| `config/recommendation.json` | My committee recommendation, ranges and triggers (analyst judgment; the engine does not write it) |
| `data/prices_monthly.csv` | Monthly adjusted closes, BIL IEF AGG LQD ACWI JOBY, 2008-04 to 2026-10 (Yahoo Finance) |
| `data/treasury_curve_daily.csv` | U.S. Treasury 3-month and 10-year par yields, daily 2008-2026 |
| `data/data_snapshot.json`, `data/source_ledger.csv` | Download time, SHA-256 hashes; source, definition, units, as-of and exclusion for every input |
| `p2/data.py` | Loads frozen data; point-in-time access (`window`, `value_known_on`) |
| `p2/estimates.py` | Historical mean, volatility, covariance (Lab 15 conventions); portfolio stats and 95% loss |
| `p2/mandate.py` | The mandate rules M1-M5, O1, R1, G1 and the verdict ("FAIL - M5") |
| `p2/optimizer.py` | Exhaustive 5-point long-only grid search (53,130 mixes): lowest volatility that passes every rule; equal-weight and inverse-volatility baselines |
| `p2/pipeline.py` | One decision run, the stress run, stop conditions, walk-forward holdout, signal test |
| `p2/report.py` | Writes `output/report.md` and `output/growth.svg` |
| `analysis.py` | Runs everything and writes `output/` |
| `app.py` | The committee web app (standard-library HTTP server) |
| `locked_test.py` | Runs the Locked Changed-Input Record. It refuses until `docs/locked-prediction.md` is filled, committed and pushed |
| `tests/test_engine.py` | Known answers (Labs 13, 15, 17), point-in-time and no-look-ahead tests, mandate and optimizer tests, frozen-output check |
| `tools/download_data.py` | The only code that touches the network |
| `docs/` | Decision memo, validation and AI-use record, mandate, data card, locked prediction, video scripts and transcripts, submission manifest |
| `prior-work/` | The Lab 13, 15 and 17 files this project grows from, unchanged |

Flow: **data/ (frozen, hashed) -> p2/data.py (point-in-time) -> estimates -> optimizer + mandate rules -> stress, stop conditions, walk-forward -> output/ -> app.py**.

## Data sources and as-of boundary

- **Prices:** Yahoo Finance monthly adjusted closes, downloaded 2026-11-23, through the October 2026 month-end.
- **Rates:** U.S. Treasury daily par yield curve. The decision uses the curve dated Oct. 29, 2026, the last business day before the Oct. 30 decision.
- **Point-in-time:** the walk-forward never reads a price or yield dated after each December decision. A test deletes later data and gets the same answer.
- **Exclusion:** JOBY prices before Aug. 2021 are SPAC prices and are not used.
- **Full detail:** [`docs/data-card.md`](docs/data-card.md) and [`data/source_ledger.csv`](data/source_ledger.csv).

## Known limitations

- Expected returns are historical means. They are the main source of instability, which is the finding, not a hidden flaw.
- The S9 loss rule is my interpretation (95% parametric one-year loss <= 10%). It understated 2022 for every strategy.
- The objective uses a fixed 2.5% CPI (stressed at 1.5% and 3.5%), not realised CPI.
- The 5-point grid cannot hold JOBY at exactly 8% (the closest step is 5%).
- Trading costs are assumptions (stressed x4 and x20). Taxes are ignored (S10: no tax preference).
- The walk-forward has 15 annual decisions: low statistical power for any signal.
- Yahoo adjusted closes are restated after distributions. The hashes pin this download.
- No credentials are needed. `.env.example` is intentionally empty.
