"""Run the Locked Changed-Input Record - only after the AI-off prediction is committed and pushed.

    python locked_test.py              # the real, recorded run
    python locked_test.py --dry-run    # practice only: writes output/locked_test_DRYRUN.md, never the record

The runner refuses to execute the recorded run unless docs/locked-prediction.md
  1. has every field filled (no "TO BE WRITTEN" left),
  2. has no uncommitted edits, and
  3. its last commit is already on a remote branch (pushed to GitHub).
It then runs the base case and the changed input through the same engine, AI closed, and
writes output/locked_test_result.md and .json with the prediction's commit and SHA-256.
"""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from p2 import pipeline as P
from p2.data import Prices, TreasuryCurve, load_config

ROOT = Path(__file__).resolve().parent
PRED = ROOT / "docs" / "locked-prediction.md"
OUT = ROOT / "output"

# name in the prediction file -> (override builder, unit shown in the record)
INPUTS = {
    "window_months": (lambda v: {"window_months": int(v)}, "months"),
    "cost_multiplier": (lambda v: {"cost_multiplier": float(v)}, "x base costs"),
    "issuer_limit": (lambda v: {"issuer_limit": float(v) / 100}, "% of reserve"),
    "reserve_min": (lambda v: {"reserve_min": float(v) / 100}, "% of reserve"),
    "loss_limit": (lambda v: {"loss_limit": float(v) / 100}, "% one-year 95% loss"),
    "cpi_pct": (lambda v: {"cpi_pct": float(v)}, "% a year"),
    "mu_shift:ACWI": (lambda v: {"mu_shift_pts": {"ACWI": float(v)}}, "pts added to ACWI expected return"),
    "mu_shift:AGG": (lambda v: {"mu_shift_pts": {"AGG": float(v)}}, "pts added to AGG expected return"),
    "mu_shift:LQD": (lambda v: {"mu_shift_pts": {"LQD": float(v)}}, "pts added to LQD expected return"),
    "mu_override:JOBY": (lambda v: {"mu_override_pct": {"JOBY": float(v)}}, "% JOBY expected return"),
}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def read_prediction():
    text = PRED.read_text(encoding="utf-8")
    if "TO BE WRITTEN" in text:
        raise SystemExit("docs/locked-prediction.md still has 'TO BE WRITTEN' fields. Write the prediction "
                         "yourself with AI closed, commit and push it, then run this again.")
    fields = {}
    for key in ("LOCKED-INPUT", "OLD", "NEW"):
        m = re.search(rf"^{key}:\s*(\S+)\s*$", text, re.M)
        if not m:
            raise SystemExit(f"docs/locked-prediction.md needs a line '{key}: <value>'.")
        fields[key] = m.group(1)
    if fields["LOCKED-INPUT"] not in INPUTS:
        raise SystemExit(f"LOCKED-INPUT must be one of: {', '.join(INPUTS)}")
    return text, fields


def check_git():
    if git("status", "--porcelain", "--", str(PRED.relative_to(ROOT))):
        raise SystemExit("docs/locked-prediction.md has uncommitted changes. Commit and push before the run.")
    line = git("log", "-1", "--format=%H %cI", "--", str(PRED.relative_to(ROOT)))
    if not line:
        raise SystemExit("docs/locked-prediction.md is not committed.")
    commit, when = line.split(" ", 1)
    remotes = git("branch", "-r", "--contains", commit)
    if not remotes:
        raise SystemExit(f"Commit {commit[:7]} is not on any remote branch. Push to GitHub first (git push), "
                         "so the prediction is public before the run.")
    return {"commit": commit, "committed_at": when, "on_remote": remotes.split()[0],
            "remote_url": git("remote", "get-url", "origin")}


def summarise(cfg, prices, curve, ov):
    stress = P.stress_run(cfg, prices, curve, ov)
    wf = P.walk_forward(cfg, prices, curve, ov)
    stop = P.stop_status(cfg, stress, wf)
    d = stress["base"]
    c = d["portfolios"].get("constrained")
    perf = wf["performance"]["constrained"]
    return {
        "feasible": d["feasible"],
        "constrained_weights": {t: w for t, w in c["weights"].items() if w > 1e-9} if c else None,
        "constrained_net_return": c["net_return"] if c else None,
        "constrained_volatility": c["volatility"] if c else None,
        "constrained_loss_95": c["loss_95"] if c else None,
        "verdicts": {k: p["verdict"]["text"] for k, p in d["portfolios"].items()},
        "stop_conditions": {s["id"]: ("ok" if s["ok"] else "TRIPPED") + f" ({s['evidence']})" for s in stop["conditions"]},
        "process_status": "STOP" if stop["stop"] else "may proceed",
        "rule_implied_action": "REJECT (stop rule fires)" if stop["stop"] else "eligible for PILOT review",
        "walk_forward_annual_return": perf["annual_return"],
        "walk_forward_worst_year": f"{perf['worst_calendar_year']}: {perf['worst_calendar_year_return']:.1%}",
        "walk_forward_stops": wf["stops"], "walk_forward_turnover_breaches": wf["turnover_breaches"],
    }


def fmt(v):
    if isinstance(v, float):
        return f"{v:.2%}"
    if isinstance(v, dict):
        return ", ".join(f"{k} {x:.0%}" if isinstance(x, float) else f"{k}: {x}" for k, x in v.items())
    return str(v)


def main():
    dry = "--dry-run" in sys.argv
    text, fields = read_prediction() if not dry else (PRED.read_text(encoding="utf-8"), None)
    if dry:
        fields = {"LOCKED-INPUT": "window_months", "OLD": "36", "NEW": "60"}
        m = re.search(r"^LOCKED-INPUT:\s*(\S+)\s*$", text, re.M)
        if m and m.group(1) in INPUTS:
            fields = {k: re.search(rf"^{k}:\s*(\S+)\s*$", text, re.M).group(1) for k in ("LOCKED-INPUT", "OLD", "NEW")}
        lock = {"commit": "DRY RUN - not a record", "committed_at": None, "on_remote": None, "remote_url": None}
    else:
        lock = check_git()
    build, unit = INPUTS[fields["LOCKED-INPUT"]]
    cfg = load_config()
    prices, curve = Prices.load(assets=cfg["assets"]), TreasuryCurve.load()
    before = summarise(cfg, prices, curve, build(fields["OLD"]))
    after = summarise(cfg, prices, curve, build(fields["NEW"]))
    record = {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dry_run": dry, "prediction_file": "docs/locked-prediction.md",
        "prediction_sha256": hashlib.sha256(PRED.read_bytes()).hexdigest(), **lock,
        "input": fields["LOCKED-INPUT"], "unit": unit, "old": fields["OLD"], "new": fields["NEW"],
        "before": before, "after": after,
    }
    stem = "locked_test_DRYRUN" if dry else "locked_test_result"
    OUT.mkdir(exist_ok=True)
    (OUT / f"{stem}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    lines = [f"# Locked Changed-Input Record - run output{' (DRY RUN, NOT THE RECORD)' if dry else ''}\n",
             f"- Prediction: `docs/locked-prediction.md`, commit `{lock['commit']}` committed {lock['committed_at']} "
             f"(on {lock['on_remote']}); SHA-256 `{record['prediction_sha256']}`",
             f"- Run (AI closed): {record['run_utc']} by `python locked_test.py`",
             f"- Input: **{fields['LOCKED-INPUT']}** ({unit}): old **{fields['OLD']}** -> new **{fields['NEW']}**\n",
             "| Output | Before (old value) | After (new value) |", "|---|---|---|"]
    for key in before:
        if key == "verdicts":
            for p in before["verdicts"]:
                lines.append(f"| Verdict: {p} | {before['verdicts'][p]} | {after['verdicts'].get(p, 'n/a')} |")
        elif key == "stop_conditions":
            for s in before["stop_conditions"]:
                lines.append(f"| Stop test {s} | {before['stop_conditions'][s]} | {after['stop_conditions'][s]} |")
        else:
            lines.append(f"| {key.replace('_', ' ')} | {fmt(before[key])} | {fmt(after[key])} |")
    lines += ["", "## Reconciliation (the student writes this after the run, in docs/validation-and-ai-use.md)",
              "Expected vs actual direction, actual decision effect, and the diagnosis where they differ."]
    (OUT / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
