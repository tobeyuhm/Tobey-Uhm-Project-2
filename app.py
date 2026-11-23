"""Meridian Reserve process review - the committee web app (Python standard library only).

    python app.py            then open http://localhost:8502

The page shows the frozen decision (output/visible_output.json) and a live panel: change the
estimation window, an estimate, costs or a constraint, press Run, and every number - the
mandate verdicts, the stress run, the stop conditions and the walk-forward test - is
recomputed by the same engine (p2/) that produced the frozen output.
Set PORT to use another port. Ctrl+C stops the server.
"""

import html
import json
import os
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from p2 import pipeline as P
from p2.data import Prices, TreasuryCurve, load_config
from p2.report import STRAT_LABEL, growth_svg

ROOT = Path(__file__).resolve().parent
CFG = load_config()
PRICES = Prices.load(assets=CFG["assets"])
CURVE = TreasuryCurve.load()
REC = json.loads((ROOT / "config" / "recommendation.json").read_text(encoding="utf-8"))
FROZEN_PATH = ROOT / "output" / "visible_output.json"
CACHE, LOCK = {}, threading.Lock()

CONTROLS = [
    # name, label, kind, choices/default
    ("window", "Estimation window (months)", "select", ["36", "24", "60", "120"]),
    ("acwi_shift", "ACWI expected return shift (pts)", "number", "0"),
    ("bond_shift", "AGG and LQD expected return shift (pts)", "number", "0"),
    ("joby_mu", "JOBY expected return override (%; blank = historical)", "number", ""),
    ("cost_mult", "Trading cost multiplier (x)", "number", "1"),
    ("issuer", "Single-company limit (%)", "number", "8"),
    ("reserve", "Payout reserve minimum (%)", "number", "3"),
    ("loss", "One-year 95% loss limit (%)", "number", "10"),
    ("cpi", "CPI assumption (%; objective = CPI + 4)", "number", "2.5"),
    ("signal", "Term-spread signal", "select", ["on", "off"]),
]

E = html.escape


def pct(x, d=1):
    return "n/a" if x is None else f"{x * 100:.{d}f}%"


def wtext(w):
    return ", ".join(f"{t} {v * 100:.0f}%" for t, v in (w or {}).items() if v > 1e-9) or "-"


def parse_controls(query):
    q = {k: v[0].strip() for k, v in parse_qs(query).items() if v and v[0].strip() != ""}
    values = {name: q.get(name, (default[0] if kind == "select" else default))
              for name, _, kind, default in CONTROLS}
    errors = []

    def num(name, lo, hi):
        text = values[name]
        if text == "":
            return None
        try:
            x = float(text)
        except ValueError:
            errors.append(f"{name}: '{text}' is not a number")
            return None
        if not lo <= x <= hi:
            errors.append(f"{name}: {x} is outside {lo} to {hi}")
            return None
        return x

    ov = {}
    if values["window"] not in ("24", "36", "60", "120"):
        errors.append("window must be 24, 36, 60 or 120")
    else:
        ov["window_months"] = int(values["window"])
    shifts = {}
    a = num("acwi_shift", -20, 20)
    b = num("bond_shift", -20, 20)
    if a:
        shifts["ACWI"] = a
    if b:
        shifts["AGG"] = shifts["LQD"] = b
    ov["mu_shift_pts"] = shifts
    j = num("joby_mu", -100, 100)
    ov["mu_override_pct"] = {} if j is None else {"JOBY": j}
    c = num("cost_mult", 0, 100)
    ov["cost_multiplier"] = 1.0 if c is None else c
    i = num("issuer", 0, 100)
    ov["issuer_limit"] = None if i is None else i / 100
    r = num("reserve", 0, 100)
    ov["reserve_min"] = None if r is None else r / 100
    lo = num("loss", 0, 100)
    ov["loss_limit"] = None if lo is None else lo / 100
    cp = num("cpi", -5, 20)
    ov["cpi_pct"] = cp
    ov["signal_on"] = values["signal"] != "off"
    # A control left at the mandate's own value is not an override (keeps the base-case cache key).
    base = {"window_months": CFG["estimation"]["window_months"], "cost_multiplier": 1.0,
            "issuer_limit": CFG["limits"]["issuer_limit"], "loss_limit": CFG["limits"]["loss_limit_95"],
            "cpi_pct": CFG["objective"]["cpi_assumption_pct"],
            "reserve_min": round(CFG["quarters_to_cover"] * CFG["quarterly_distribution_usd_m"] / CFG["reserve_usd_m"], 6)}
    for k, v in base.items():
        if ov.get(k) is not None and abs(ov[k] - v) < 1e-12:
            ov[k] = None if k != "cost_multiplier" else 1.0
    if ov.get("window_months") is None:
        ov.pop("window_months", None)
    return values, ov, errors


def compute(ov):
    key = json.dumps(ov, sort_keys=True)
    with LOCK:
        if key in CACHE:
            return CACHE[key]
    stress = P.stress_run(CFG, PRICES, CURVE, ov)
    wf = P.walk_forward(CFG, PRICES, CURVE, ov)
    stop = P.stop_status(CFG, stress, wf)
    result = {"decision": stress["base"], "stress": stress["rows"], "wf": wf, "stop": stop}
    with LOCK:
        CACHE[key] = result
    return result


CSS = """
:root{--bg:#f6f8fa;--card:#fff;--ink:#1f2328;--muted:#59636e;--line:#d1d9e0;--accent:#1f6feb;
--pass:#1a7f37;--fail:#cf222e;--warn:#9a6700}
@media (prefers-color-scheme: dark){:root{--bg:#0d1117;--card:#151b23;--ink:#e6edf3;--muted:#9198a1;
--line:#3d444d;--accent:#4493f8;--pass:#3fb950;--fail:#f85149;--warn:#d29922}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI",system-ui,sans-serif}
header{background:var(--card);border-bottom:1px solid var(--line);padding:16px 24px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:0 0 10px}main{max-width:1200px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:0 0 16px}
.statements{font-size:13px;color:var(--muted);margin-top:6px}.muted{color:var(--muted);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums}
.pass{color:var(--pass);font-weight:600}.fail{color:var(--fail);font-weight:600}.warn{color:var(--warn);font-weight:600}
.banner{border-left:6px solid var(--fail);}.banner .act{font-size:26px;font-weight:700;color:var(--fail)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px 16px}
label{display:block;font-size:12.5px;color:var(--muted)}input,select{width:100%;padding:6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
button{background:var(--accent);color:#fff;border:0;border-radius:6px;padding:8px 18px;font-weight:600;cursor:pointer}
.scroll{overflow-x:auto}svg{max-width:100%;height:auto;background:#fff;border-radius:6px}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;border:1px solid var(--line);font-size:12px}
a{color:var(--accent)}
"""


def verdict_html(v):
    cls = "pass" if v["passed"] else "fail"
    return f'<span class="{cls}">{E(v["text"])}</span>'


def page(values, ov, errors, res, frozen):
    d, stop, wf = res["decision"], res["stop"], res["wf"]
    changed = bool(d["overrides"])
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
           f"content='width=device-width,initial-scale=1'><title>Meridian Reserve Review</title><style>{CSS}</style></head><body>"]
    out.append("<header><h1>Meridian Reserve - Process Review App</h1>"
               f"<div class='muted'>FIN 43900 Project 2 · Tobey Uhm · decision as of {E(CFG['decision_as_of'])} "
               f"(prices through {E(CFG['last_price_month'])})</div>"
               "<div class='statements'><b>AI use:</b> I used Claude (Anthropic; Claude Code, Claude Opus 5.5) to build this "
               "app's code, tests and documents and to draft video scripts, and OpenAI Codex (GPT-5) for the Lab 13-17 code it grows "
               "from. The analysis and the decision are mine. <b>Education, not investment advice:</b> a course project on a "
               "fictional client.</div></header><main>")

    # Frozen decision
    out.append("<section class='card banner'><div class='muted'>Committee recommendation (frozen, analyst judgment)</div>"
               f"<div class='act'>{E(REC['action'])}</div><p>{E(REC['headline'])}</p>"
               f"<p><b>Allocation to the process:</b> {E(REC['process_allocation_range'])}<br>"
               f"<b>Reserve allocation range:</b> {E(REC['reserve_allocation_text'])}<br>"
               f"<b>Reverses if:</b> {E(REC['reverse_if'])}</p><b>Committee ask</b><ol>"
               + "".join(f"<li>{E(x)}</li>" for x in REC["committee_ask"]) + "</ol></section>")

    # Controls
    out.append("<section class='card'><h2>Change an input and rerun</h2><form method='get' action='/'><div class='grid'>")
    for name, label, kind, default in CONTROLS:
        if kind == "select":
            opts = "".join(f"<option{' selected' if values[name] == o else ''}>{o}</option>" for o in default)
            out.append(f"<div><label for='{name}'>{E(label)}</label><select id='{name}' name='{name}'>{opts}</select></div>")
        else:
            out.append(f"<div><label for='{name}'>{E(label)}</label><input id='{name}' name='{name}' "
                       f"inputmode='decimal' value='{E(values[name])}'></div>")
    out.append("</div><p><button type='submit'>Run</button> <a href='/'>Reset to base case</a> · "
               "<a href='/api/run'>JSON</a> · <a href='/report'>Frozen report</a></p></form>")
    for e in errors:
        out.append(f"<p class='fail'>Input ignored - {E(e)}</p>")
    out.append(f"<p class='muted'>{'Showing a <b>changed-input</b> run: ' + E(json.dumps(d['overrides'])) if changed else 'Showing the base case.'} "
               "Every number below is recomputed live by the same engine as the frozen output (about 5 seconds).</p></section>")

    # Stop status
    status = "<span class='fail'>STOP - hold the benchmark, report to the committee</span>" if stop["stop"] else \
             "<span class='pass'>Process may proceed</span>"
    out.append(f"<section class='card'><h2>The condition that stops the process: {status}</h2><table>"
               "<tr><th>Test</th><th>Result</th><th>Evidence</th></tr>")
    for c in stop["conditions"]:
        out.append(f"<tr><td>{E(c['id'])}: {E(c['test'])}</td><td class='{'pass' if c['ok'] else 'fail'}'>"
                   f"{'ok' if c['ok'] else 'TRIPPED'}</td><td>{E(c['evidence'])}</td></tr>")
    out.append("</table></section>")

    # Mandate verdicts
    pf = d["portfolios"]
    keys = [k for k in ("equal_weight", "inverse_vol", "constrained", "benchmark") if k in pf]
    out.append("<section class='card'><h2>Two baselines, my constrained portfolio and the benchmark: mandate verdicts</h2>"
               f"<p class='muted'>Estimates from {E(d['window_first_month'])} to {E(d['window_last_month'])} "
               f"({d['window_months']} monthly returns). Objective {pct(d['objective_return'])} net; payout reserve "
               f"&gt;= {pct(d['reserve_minimum'])}; single company &lt;= {pct(d['issuer_limit'], 0)}; "
               f"95% one-year loss &lt;= {pct(d['loss_limit'], 0)}.</p>")
    if not d["feasible"]:
        out.append(f"<p class='fail'>No long-only mix passes every rule (highest net return inside the hard rules: "
                   f"{pct(d['optimizer_diagnosis']['max_net_return_within_hard_rules'], 2)}). The constrained portfolio does not exist under these inputs.</p>")
    out.append("<div class='scroll'><table><tr><th>Portfolio</th><th>Weights</th><th>Net exp. return</th><th>Volatility</th>"
               "<th>95% 1-yr loss</th><th>Verdict</th></tr>")
    for k in keys:
        p = pf[k]
        out.append(f"<tr><td>{E(p['name'])}</td><td>{E(wtext(p['weights']))}</td><td class='n'>{pct(p['net_return'], 2)}</td>"
                   f"<td class='n'>{pct(p['volatility'], 2)}</td><td class='n'>{pct(p['loss_95'], 2)}</td><td>{verdict_html(p['verdict'])}"
                   f"{'<br><span class=muted>' + E(p['note']) + '</span>' if p.get('note') else ''}</td></tr>")
    out.append("</table></div><details><summary>Rule-by-rule detail</summary><div class='scroll'><table><tr><th>Rule</th><th>Limit</th>"
               + "".join(f"<th>{E(pf[k]['name'].split(' (')[0])}</th>" for k in keys) + "</tr>")
    for i, rule in enumerate(pf[keys[0]]["rules"]):
        cells = ""
        for k in keys:
            rr = pf[k]["rules"][i]
            cls = "pass" if rr["passed"] else ("warn" if rr["kind"] == "governance" else "fail")
            word = "pass" if rr["passed"] else ("needs approval" if rr["kind"] == "governance" else "FAIL")
            cells += f"<td class='{cls}'>{pct(rr['measured'])} {word}</td>"
        out.append(f"<tr><td>{E(rule['id'])} {E(rule['rule'])}</td><td>{E(rule['limit'])}</td>{cells}</tr>")
    out.append("</table></div></details>")
    out.append("<details><summary>Estimates used</summary><table><tr><th>Asset</th><th>Expected return</th><th>Volatility</th><th>Role</th></tr>"
               + "".join(f"<tr><td>{t}</td><td class='n'>{pct(e['mu'], 2)}</td><td class='n'>{pct(e['vol'], 2)}</td>"
                         f"<td>{E(CFG['assets'][t]['role'])}</td></tr>" for t, e in d["estimates"].items())
               + "</table></details></section>")

    # Signal
    s = d["signal_reading"]
    st = frozen["signal_test"]["groups"]
    out.append("<section class='card'><h2>Point-in-time signal: Treasury term spread</h2>"
               f"<p>Known on {E(d['decision_date'])}: 10-year {s['y10_pct']:.2f}% - 3-month {s['y3m_pct']:.2f}% = "
               f"<b>{s['spread_pct']:+.2f} pts</b> (observation dated {E(s['observation_date'])}; rule uses the last business day "
               f"before the decision). Action: {E(d['signal_action'])}.</p>"
               "<table><tr><th>Data card</th><th></th></tr>"
               "<tr><td>Source</td><td>U.S. Treasury daily par yield curve (the source of FRED DGS10 / DGS3MO, H.15)</td></tr>"
               "<tr><td>Units / frequency</td><td>Percent, bond-equivalent basis; daily (business days)</td></tr>"
               "<tr><td>Known when</td><td>Published the same evening; the app uses only observations dated strictly before the decision date (1-business-day lag, as found for DGS10 in Lab 17)</td></tr>"
               "<tr><td>Revisions</td><td>Not revised in normal practice; Lab 17 found 0 revised DGS10 values 2020-2026 in ALFRED</td></tr>"
               "<tr><td>Full card</td><td><code>docs/data-card.md</code></td></tr></table>"
               "<p class='muted'>Monthly test 2008-05 to 2026-10 (IEF minus BIL next month): "
               f"positive curve {pct(st['positive']['mean_annualised'], 2)}/yr, t = {st['positive']['t_stat']:.2f} ({st['positive']['months']} months); "
               f"inverted {pct(st['inverted']['mean_annualised'], 2)}/yr, t = {st['inverted']['t_stat']:.2f} ({st['inverted']['months']} months). "
               "No reliable edge: the signal is kept as a monitored rule, not a reason to adopt.</p></section>")

    # Stress
    out.append("<section class='card'><h2>Stress run: estimates, window, costs, constraints</h2><div class='scroll'><table>"
               "<tr><th>Group</th><th>Scenario</th><th>Adjacent</th><th>Portfolio</th><th>Net return</th><th>Vol.</th><th>Shift vs base</th><th>Verdict</th></tr>")
    for r in res["stress"]:
        shift = r["shift_vs_base"]
        cls = "fail" if (r["adjacent"] and (shift is None or shift > CFG["stop_conditions"]["max_stress_shift"] + 1e-9)) else ""
        out.append(f"<tr><td>{E(r['group'])}</td><td>{E(r['scenario'])}</td><td>{'yes' if r['adjacent'] else 'no'}</td>"
                   f"<td>{E(wtext(r['weights']))}</td><td class='n'>{pct(r.get('net_return'), 2)}</td>"
                   f"<td class='n'>{pct(r.get('volatility'), 2)}</td><td class='n {cls}'>{pct(shift, 0)}</td><td>{E(r['verdict'])}</td></tr>")
    out.append("</table></div><p class='muted'>Stress rows apply on top of the controls above. 'Shift' is one-way turnover "
               "between the stressed and the base portfolio; above 25% on an adjacent stress trips stop test S2.</p></section>")

    # Walk-forward
    perf = wf["performance"]
    out.append(f"<section class='card'><h2>Walk-forward holdout: {E(wf['first_month'])} to {E(wf['last_month'])}</h2>"
               f"<p class='muted'>Each December the process sees only data to that month, rebalances, then drifts for a year; "
               f"trading costs charged. Stops (benchmark held): <b>{wf['stops']}</b> of {len(wf['rebalances'])}. "
               f"Turnover above 25%: <b>{wf['turnover_breaches']}</b> of {len(wf['rebalances']) - 1} later rebalances.</p>")
    out.append(growth_svg(wf))
    out.append("<div class='scroll'><table><tr><th>Strategy</th><th>Annual return</th><th>Volatility</th><th>Max drawdown</th>"
               "<th>Worst calendar year</th><th>Tracking error</th></tr>")
    for k, p in perf.items():
        out.append(f"<tr><td>{E(STRAT_LABEL[k])}</td><td class='n'>{pct(p['annual_return'], 2)}</td><td class='n'>{pct(p['volatility'], 2)}</td>"
                   f"<td class='n'>{pct(p['max_drawdown'])}</td><td class='n'>{p['worst_calendar_year']}: {pct(p['worst_calendar_year_return'])}</td>"
                   f"<td class='n'>{pct(p['tracking_error'])}</td></tr>")
    out.append("</table></div><details><summary>Rebalance log</summary><table><tr><th>December</th><th>Feasible</th><th>Spread</th>"
               "<th>Target</th><th>Turnover</th></tr>"
               + "".join(f"<tr><td>{x['rebalance']}</td><td>{'yes' if x['feasible'] else '<span class=fail>STOP</span>'}</td>"
                         f"<td class='n'>{x['spread_pct']:+.2f}</td><td>{E(wtext(x['weights']))}</td><td class='n'>{pct(x['turnover'], 0)}</td></tr>"
                         for x in wf["rebalances"]) + "</table></details></section>")

    # Triggers
    out.append("<section class='card'><h2>Monitoring triggers</h2><table><tr><th>Monitor</th><th>Trigger</th><th>Action</th></tr>"
               + "".join(f"<tr><td>{E(t['monitor'])}</td><td>{E(t['trigger'])}</td><td>{E(t['action'])}</td></tr>" for t in REC["triggers"])
               + "</table></section>")
    snap = frozen["data_snapshot"]
    out.append("<section class='card muted'>Data: " + "; ".join(
        f"{E(n)} ({E(m['source'])}, {m['rows']} rows, SHA-256 {m['sha256'][:12]}...)" for n, m in snap["files"].items())
        + f"; downloaded {E(snap['downloaded_utc'])}. JOBY prices before 2021-08 (pre-merger SPAC) excluded. "
          "Sources and lineage: docs/data-card.md, data/source_ledger.csv.</section>")
    out.append("</main></body></html>")
    return "".join(out)


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/healthz":
                return self.send(200, "ok", "text/plain")
            if url.path == "/report":
                text = (ROOT / "output" / "report.md").read_text(encoding="utf-8")
                return self.send(200, text, "text/plain; charset=utf-8")
            if url.path == "/growth.svg":
                return self.send(200, (ROOT / "output" / "growth.svg").read_text(encoding="utf-8"), "image/svg+xml")
            if url.path not in ("/", "/api/run"):
                return self.send(404, "Not found", "text/plain")
            values, ov, errors = parse_controls(url.query)
            res = compute(ov)
            if url.path == "/api/run":
                body = {"controls": values, "errors": errors, "stop": res["stop"], "decision": res["decision"],
                        "stress": res["stress"], "walk_forward": {k: v for k, v in res["wf"].items() if k != "months"}}
                return self.send(200, json.dumps(body, default=str, indent=1), "application/json")
            frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
            return self.send(200, page(values, ov, errors, res, frozen))
        except Exception as error:  # show the error instead of a blank page; details stay local
            traceback.print_exc()
            return self.send(500, f"<h1>Error</h1><pre>{E(str(error))}</pre><p><a href='/'>Back to base case</a></p>")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))


def main():
    if not FROZEN_PATH.exists():
        print("output/visible_output.json is missing - run: python analysis.py")
        sys.exit(1)
    port = int(os.environ.get("PORT", "8502"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print(f"Meridian Reserve app running at {url}  (Ctrl+C to stop)")
    print("Computing the base case (about 5 seconds)...")
    compute(parse_controls("")[1])
    if os.environ.get("NO_BROWSER") != "1" and "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
