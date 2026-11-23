"""Rebuild every frozen result in output/ from the frozen data in data/.

    python analysis.py

Writes output/visible_output.json (what the app's "frozen decision" panel reads),
output/report.md (readable on GitHub without running anything) and output/growth.svg.
Standard library only.
"""

import hashlib
import json
import sys
from pathlib import Path

from p2 import pipeline as P
from p2.data import DATA, Prices, TreasuryCurve, load_config
from p2.report import growth_svg, render_report

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WINDOW_VARIANTS = [24, 36, 60, 120]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    cfg = load_config()
    rec = json.loads((ROOT / "config" / "recommendation.json").read_text(encoding="utf-8"))
    prices = Prices.load(assets=cfg["assets"])
    curve = TreasuryCurve.load()
    snapshot = json.loads((DATA / "data_snapshot.json").read_text(encoding="utf-8"))
    for name, meta in snapshot["files"].items():
        if sha256(DATA / name) != meta["sha256"]:
            raise SystemExit(f"{name} does not match data_snapshot.json - the frozen data changed.")

    stress = P.stress_run(cfg, prices, curve)
    wf = P.walk_forward(cfg, prices, curve)
    variants = []
    for w in WINDOW_VARIANTS:
        v = wf if w == cfg["estimation"]["window_months"] else P.walk_forward(cfg, prices, curve, {"window_months": w})
        c, b = v["performance"]["constrained"], v["performance"]["benchmark"]
        variants.append({"window_months": w, "first_month": v["first_month"], "stops": v["stops"],
                         "turnover_breaches": v["turnover_breaches"], "annual_return": c["annual_return"],
                         "volatility": c["volatility"], "worst_year": c["worst_calendar_year"],
                         "worst_year_return": c["worst_calendar_year_return"],
                         "benchmark_annual_return": b["annual_return"],
                         "benchmark_worst_year_return": b["worst_calendar_year_return"]})
    rng = rec["reserve_allocation_range"]
    corners = {
        "Top of range: ACWI 60 / AGG 37 / BIL 3": {"ACWI": rng["ACWI"][1], "AGG": 0.37, "BIL": rng["BIL"][0]},
        "Midpoint: ACWI 57.5 / AGG 37.5 / BIL 5": {"ACWI": 0.575, "AGG": 0.375, "BIL": rng["BIL"][1]},
        "Bottom of range: ACWI 55 / AGG 40 / BIL 5": {"ACWI": rng["ACWI"][0], "AGG": rng["AGG"][1], "BIL": rng["BIL"][1]},
    }
    reserve_range = []
    for label, target in corners.items():
        perf = P.fixed_mix_history(cfg, prices, target, wf["first_month"], wf["last_month"])
        rules = P.M.check({t: target.get(t, 0.0) for t in cfg["assets"]}, cfg)
        reserve_range.append({"mix": label, "weights": target, "verdict": P.M.verdict(rules)["text"],
                              **{k: perf[k] for k in ("annual_return", "volatility", "max_drawdown",
                                                      "worst_calendar_year", "worst_calendar_year_return")}})
    sig = P.signal_test(cfg, prices, curve)
    stop = P.stop_status(cfg, stress, wf)
    result = {
        "project": "FIN 43900 Project 2 - Investment Management Application (Tobey Uhm)",
        "decision_as_of": cfg["decision_as_of"], "last_price_month": cfg["last_price_month"],
        "data_snapshot": snapshot, "mandate": cfg, "recommendation": rec,
        "decision": stress["base"], "stress": stress["rows"], "stop_status": stop,
        "walk_forward": {k: v for k, v in wf.items() if k != "months"},
        "walk_forward_months": wf["months"], "window_variants": variants,
        "reserve_range_check": reserve_range,
        "signal_test": {k: v for k, v in sig.items() if k != "rows"},
        "signal_recent": sig["rows"][-6:],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "visible_output.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    (OUT / "growth.svg").write_text(growth_svg(wf), encoding="utf-8")
    (OUT / "report.md").write_text(render_report(result), encoding="utf-8")
    return result


def main():
    result = build()
    d = result["decision"]["portfolios"]
    print(f"As of {result['decision_as_of']} (prices through {result['last_price_month']})")
    for key in ("equal_weight", "inverse_vol", "benchmark", "constrained"):
        if key in d:
            p = d[key]
            print(f"  {p['name']:<45} net {p['net_return']:6.2%}  vol {p['volatility']:6.2%}  {p['verdict']['text']}")
    print("Stop conditions:", "; ".join(f"{c['id']} {'ok' if c['ok'] else 'TRIPPED'} ({c['evidence']})"
                                      for c in result["stop_status"]["conditions"]))
    print("Recommendation:", result["recommendation"]["action"], "-", result["recommendation"]["headline"])
    print("Wrote output/visible_output.json, output/report.md, output/growth.svg")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
