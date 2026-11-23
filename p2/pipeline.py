"""One decision run, the walk-forward test, the stress run, and the signal test.

app.py and analysis.py both call these functions; neither computes a finance number itself.
"""

import copy
from math import sqrt

from . import mandate as M
from .data import month_end_decision_date
from .estimates import estimate, portfolio_stats
from .optimizer import equal_weight, inverse_volatility, optimize

DEFAULTS = {
    "window_months": None,        # None -> config estimation.window_months
    "end_month": None,            # None -> config last_price_month
    "mu_shift_pts": {},           # {"ACWI": -1.0} adds -1 percentage point to the estimate
    "mu_override_pct": {},        # {"JOBY": 0.0} replaces the estimate
    "cost_multiplier": 1.0,
    "issuer_limit": None,
    "reserve_min": None,
    "loss_limit": None,
    "cpi_pct": None,
    "signal_on": True,
    "exclude": [],
}


def effective_config(cfg, overrides):
    """Apply app/stress overrides to a copy of the mandate; the file on disk never changes."""
    c = copy.deepcopy(cfg)
    if overrides.get("issuer_limit") is not None:
        c["limits"]["issuer_limit"] = overrides["issuer_limit"]
    if overrides.get("loss_limit") is not None:
        c["limits"]["loss_limit_95"] = overrides["loss_limit"]
    if overrides.get("cpi_pct") is not None:
        c["objective"]["cpi_assumption_pct"] = overrides["cpi_pct"]
    if overrides.get("reserve_min") is not None:
        # Express a reserve-minimum override through the payout inputs it comes from.
        c["quarters_to_cover"] = overrides["reserve_min"] * c["reserve_usd_m"] / c["quarterly_distribution_usd_m"]
    return c


def apply_signal(weights, reading, signal_on):
    """Pre-specified rule: inverted curve -> IEF weight moves to BIL. Returns (weights, action)."""
    w = dict(weights)
    if not signal_on or reading is None:
        return w, "signal off"
    if reading["spread_pct"] < 0 and w.get("IEF", 0) > 0:
        w["BIL"] = w.get("BIL", 0) + w.pop("IEF")
        w["IEF"] = 0.0
        return w, f"inverted ({reading['spread_pct']:+.2f} pts): IEF moved to BIL"
    if reading["spread_pct"] < 0:
        return w, f"inverted ({reading['spread_pct']:+.2f} pts): no IEF held, no change"
    return w, f"positive ({reading['spread_pct']:+.2f} pts): keep IEF"


def _describe(name, weights, est, cfg, current, cost_multiplier, note=""):
    full = {t: weights.get(t, 0.0) for t in cfg["assets"]}
    stats = portfolio_stats(full, est_full(est, cfg), cfg["estimation"]["z_95"])
    cost = M.trading_cost(full, current, cfg["assets"], cost_multiplier)
    net = stats["expected_return"] - cost
    stats = dict(stats, loss_95=-(net - cfg["estimation"]["z_95"] * stats["volatility"]))
    rules = M.check(full, cfg, stats=stats, net_return=net, current=current)
    return {"name": name, "weights": full, "expected_return": stats["expected_return"],
            "trading_cost": cost, "net_return": net, "volatility": stats["volatility"],
            "loss_95": stats["loss_95"], "rules": rules, "verdict": M.verdict(rules), "note": note}


def est_full(est, cfg):
    """Pad the estimate with zero rows for assets outside the window (they carry zero weight)."""
    tickers = list(cfg["assets"])
    mu = {t: est["mu"].get(t, 0.0) for t in tickers}
    cov = {a: {b: est["cov"].get(a, {}).get(b, 0.0) for b in tickers} for a in tickers}
    return {"tickers": tickers, "mu": mu, "cov": cov}


def run_decision(cfg, prices, curve, overrides=None, current=None):
    ov = {**DEFAULTS, **(overrides or {})}
    c = effective_config(cfg, ov)
    window = ov["window_months"] or c["estimation"]["window_months"]
    end_month = ov["end_month"] or c["last_price_month"]
    current = current if current is not None else c["current_holdings"]
    universe = [t for t in c["assets"] if t not in ov["exclude"]]
    months, rets = prices.window(universe, end_month, window)
    est = estimate(rets)
    for t, pts in ov["mu_shift_pts"].items():
        if t in est["mu"]:
            est["mu"][t] += pts / 100
    for t, pct in ov["mu_override_pct"].items():
        if t in est["mu"]:
            est["mu"][t] = pct / 100
    available = est["tickers"]
    excluded = [t for t in universe if t not in available]

    decision_date = month_end_decision_date(end_month)
    reading = curve.value_known_on(decision_date, c["signal"]["lag_business_days"]) if curve else None

    r_min = M.reserve_minimum(c)
    target = M.objective_return(c)
    caps = {t: c["limits"]["issuer_limit"] for t in available if not c["assets"][t]["issuer_exempt"]}
    result, diag = optimize(
        est, min_return=target,
        reserve_eligible={t for t in available if c["assets"][t]["reserve_eligible"]},
        reserve_min=r_min, caps=caps, loss_limit=c["limits"]["loss_limit_95"],
        z=c["estimation"]["z_95"], step=c["estimation"]["grid_step"], current=current,
        cost_bps={t: a["trade_cost_bps"] for t, a in c["assets"].items()},
        cost_multiplier=ov["cost_multiplier"])

    portfolios = {}
    portfolios["equal_weight"] = _describe("Equal weight (baseline 1)", equal_weight(available),
                                           est, c, current, ov["cost_multiplier"])
    portfolios["inverse_vol"] = _describe("Inverse volatility (baseline 2)", inverse_volatility(est),
                                          est, c, current, ov["cost_multiplier"])
    portfolios["benchmark"] = _describe("Benchmark 60% ACWI / 40% AGG (reference)", c["benchmark"],
                                        est, c, current, ov["cost_multiplier"])
    signal_action = "no feasible portfolio"
    if result is not None:
        pre = result["weights"]
        tilted, signal_action = apply_signal(pre, reading, ov["signal_on"])
        portfolios["constrained"] = _describe("Constrained portfolio (my process)", tilted, est, c,
                                              current, ov["cost_multiplier"], note=signal_action)
        portfolios["constrained"]["pre_signal_weights"] = {t: pre.get(t, 0.0) for t in c["assets"]}
    return {
        "end_month": end_month, "decision_date": decision_date.isoformat(),
        "window_months": window, "window_first_month": months[0], "window_last_month": months[-1],
        "available": available, "excluded_for_short_history": excluded,
        "estimates": {t: {"mu": est["mu"][t], "vol": est["vol"][t]} for t in available},
        "corr": est["corr"], "reserve_minimum": r_min, "objective_return": target,
        "issuer_limit": c["limits"]["issuer_limit"], "loss_limit": c["limits"]["loss_limit_95"],
        "signal_reading": reading, "signal_action": signal_action,
        "feasible": result is not None, "optimizer_diagnosis": diag,
        "portfolios": portfolios, "overrides": {k: v for k, v in ov.items() if v not in (None, {}, [], 1.0, True)},
    }


# ---------------------------------------------------------------- walk-forward (holdout) test

def _calendar_years(months, rets):
    years = {}
    for m, r in zip(months, rets):
        years.setdefault(m[:4], []).append(r)
    out = {}
    for y, rs in years.items():
        g = 1.0
        for r in rs:
            g *= 1 + r
        out[y] = {"return": g - 1, "months": len(rs)}
    return out


def performance(months, rets):
    n = len(rets)
    growth, peak, mdd, path = 1.0, 1.0, 0.0, []
    for r in rets:
        growth *= 1 + r
        peak = max(peak, growth)
        mdd = min(mdd, growth / peak - 1)
        path.append(growth)
    mean = sum(rets) / n
    sd = sqrt(sum((r - mean) ** 2 for r in rets) / (n - 1))
    years = _calendar_years(months, rets)
    full_years = {y: v for y, v in years.items() if v["months"] == 12}
    worst_year = min(full_years.items(), key=lambda kv: kv[1]["return"])
    return {"months": n, "annual_return": growth ** (12 / n) - 1, "volatility": sd * sqrt(12),
            "max_drawdown": mdd, "worst_calendar_year": worst_year[0],
            "worst_calendar_year_return": worst_year[1]["return"],
            "years_loss_over_10pct": sum(v["return"] < -0.10 for v in full_years.values()),
            "full_years": len(full_years), "calendar_years": {y: v["return"] for y, v in years.items()},
            "growth_path": path}


def walk_forward(cfg, prices, curve, overrides=None, rebalance_month="12"):
    """Annual rebalance (S1) every December from the first month with a full window.

    At each rebalance the process sees only data through that month and the curve known the
    business day before; weights then drift with realised returns for twelve months. If the
    constrained search finds no feasible mix, the process STOPS for that year and holds the
    benchmark (counted). Trading costs are charged on each rebalance's actual turnover.
    """
    ov = {**DEFAULTS, **(overrides or {})}
    window = ov["window_months"] or cfg["estimation"]["window_months"]
    assets = cfg["assets"]
    ret_by = {t: prices.returns(t) for t in assets}
    first_ok = prices.months[window]          # month index `window` has `window` returns behind it
    rebal_months = [m for m in prices.months if m.endswith("-" + rebalance_month) and m >= first_ok]
    last = cfg["last_price_month"]
    strategies = ["constrained", "constrained_no_signal", "equal_weight", "inverse_vol", "benchmark"]
    holdings = {s: dict(cfg["current_holdings"]) for s in strategies}
    series = {s: [] for s in strategies}
    log, hold_months = [], []
    for k, rm in enumerate(rebal_months):
        targets = {}
        run = run_decision(cfg, prices, curve, {**ov, "end_month": rm}, current=holdings["constrained"])
        run_ns = run_decision(cfg, prices, curve, {**ov, "end_month": rm, "signal_on": False},
                              current=holdings["constrained_no_signal"])
        stopped = not run["feasible"]
        targets["constrained"] = (run["portfolios"]["constrained"]["weights"] if not stopped
                                  else dict(cfg["benchmark"]))
        targets["constrained_no_signal"] = (run_ns["portfolios"]["constrained"]["weights"]
                                            if run_ns["feasible"] else dict(cfg["benchmark"]))
        for s in ("equal_weight", "inverse_vol", "benchmark"):
            targets[s] = run["portfolios"][s]["weights"]
        costs = {s: M.trading_cost(targets[s], holdings[s], assets, ov["cost_multiplier"]) for s in strategies}
        turnover = M.one_way_turnover(targets["constrained"], holdings["constrained"])
        log.append({"rebalance": rm, "feasible": not stopped, "signal": run["signal_action"],
                    "spread_pct": run["signal_reading"]["spread_pct"] if run["signal_reading"] else None,
                    "weights": {t: w for t, w in targets["constrained"].items() if w > 1e-9},
                    "expected_net_return": (run["portfolios"]["constrained"]["net_return"]
                                            if not stopped else None),
                    "turnover": turnover, "turnover_over_limit": turnover > cfg["limits"]["turnover_limit"] + 1e-9})
        nxt = rebal_months[k + 1] if k + 1 < len(rebal_months) else last
        i0, i1 = prices.months.index(rm), prices.months.index(nxt)
        period = prices.months[i0 + 1: i1 + 1]
        w_now = {s: dict(targets[s]) for s in strategies}
        for j, m in enumerate(period):
            hold_months.append(m)
            for s in strategies:
                gross = sum(w * ret_by[t].get(m, 0.0) for t, w in w_now[s].items() if w)
                r = gross - (costs[s] if j == 0 else 0.0)
                series[s].append(r)
                total = sum(w * (1 + ret_by[t].get(m, 0.0)) for t, w in w_now[s].items() if w)
                w_now[s] = {t: w * (1 + ret_by[t].get(m, 0.0)) / total for t, w in w_now[s].items() if w}
        holdings = w_now
    perf = {s: performance(hold_months, series[s]) for s in strategies}
    b = series["benchmark"]
    for s in strategies:
        diff = [x - y for x, y in zip(series[s], b)]
        md = sum(diff) / len(diff)
        perf[s]["tracking_error"] = sqrt(sum((d - md) ** 2 for d in diff) / (len(diff) - 1)) * sqrt(12)
        perf[s]["excess_vs_benchmark"] = perf[s]["annual_return"] - perf["benchmark"]["annual_return"]
    return {"first_month": hold_months[0], "last_month": hold_months[-1], "months": hold_months,
            "window_months": window, "rebalances": log,
            "stops": sum(not r["feasible"] for r in log),
            "turnover_breaches": sum(r["turnover_over_limit"] for r in log[1:]),
            "performance": perf}


def fixed_mix_history(cfg, prices, target, first_month, last_month, cost_multiplier=1.0):
    """A fixed policy mix rebalanced every December over the same holdout (no estimates used)."""
    ret_by = {t: prices.returns(t) for t in target}
    months = [m for m in prices.months if first_month <= m <= last_month]
    w, rets, held = dict(target), [], dict(cfg["current_holdings"])
    for m in months:
        cost = 0.0
        if m == first_month or m.endswith("-01"):
            cost = M.trading_cost(target, held, cfg["assets"], cost_multiplier)
            w = dict(target)
        r = sum(x * ret_by[t][m] for t, x in w.items()) - cost
        rets.append(r)
        total = sum(x * (1 + ret_by[t][m]) for t, x in w.items())
        w = {t: x * (1 + ret_by[t][m]) / total for t, x in w.items()}
        held = w
    perf = performance(months, rets)
    perf.pop("growth_path")
    return perf


# ---------------------------------------------------------------- stress run at the decision date

STRESSES = [
    # (group, label, overrides, adjacent?) - "adjacent" = a plausible one-step change in a single input
    ("Base", "Base case (frozen: 36-month window, historical means, base costs; in the app: the controls set)", {}, False),
    ("Estimates", "ACWI expected return -1 pt", {"mu_shift_pts": {"ACWI": -1.0}}, True),
    ("Estimates", "ACWI expected return -2 pts", {"mu_shift_pts": {"ACWI": -2.0}}, False),
    ("Estimates", "LQD and AGG expected return -1 pt", {"mu_shift_pts": {"LQD": -1.0, "AGG": -1.0}}, True),
    ("Estimates", "JOBY expected return = 0% (Project 1: price above value)", {"mu_override_pct": {"JOBY": 0.0}}, True),
    ("Window", "24-month window", {"window_months": 24}, True),
    ("Window", "60-month window", {"window_months": 60}, True),
    ("Window", "120-month window", {"window_months": 120}, False),
    ("Costs", "Trading costs x4", {"cost_multiplier": 4.0}, True),
    ("Costs", "Trading costs x20 (stressed spreads)", {"cost_multiplier": 20.0}, False),
    ("Constraints", "No single-company holding (issuer limit 0%)", {"issuer_limit": 0.0}, True),
    ("Constraints", "Reserve minimum 10%", {"reserve_min": 0.10}, True),
    ("Constraints", "Loss limit 8% instead of 10%", {"loss_limit": 0.08}, True),
    ("Constraints", "CPI 3.5% (objective 7.5%)", {"cpi_pct": 3.5}, True),
    ("Constraints", "CPI 1.5% (objective 5.5%)", {"cpi_pct": 1.5}, True),
]


def stress_run(cfg, prices, curve, base_overrides=None):
    base_ov = base_overrides or {}
    base = run_decision(cfg, prices, curve, base_ov)
    base_w = base["portfolios"]["constrained"]["weights"] if base["feasible"] else None
    rows = []
    for group, label, ov, adjacent in STRESSES:
        merged = {**base_ov, **ov}
        # Stack a stress on top of the app's controls: shifts add, overrides replace.
        shifts = dict(base_ov.get("mu_shift_pts", {}))
        for t, pts in ov.get("mu_shift_pts", {}).items():
            shifts[t] = shifts.get(t, 0.0) + pts
        merged["mu_shift_pts"] = shifts
        merged["mu_override_pct"] = {**base_ov.get("mu_override_pct", {}), **ov.get("mu_override_pct", {})}
        run = base if not ov else run_decision(cfg, prices, curve, merged)
        row = {"group": group, "scenario": label, "adjacent": adjacent, "feasible": run["feasible"]}
        if run["feasible"]:
            p = run["portfolios"]["constrained"]
            row.update(weights={t: w for t, w in p["weights"].items() if w > 1e-9},
                       net_return=p["net_return"], volatility=p["volatility"], loss_95=p["loss_95"],
                       verdict=p["verdict"]["text"],
                       shift_vs_base=(M.one_way_turnover(p["weights"], base_w) if base_w else None))
        else:
            row.update(weights=None, verdict="NO FEASIBLE MIX",
                       max_net_return=run["optimizer_diagnosis"]["max_net_return_within_hard_rules"],
                       shift_vs_base=None)
        rows.append(row)
    return {"base": base, "rows": rows}


def stop_status(cfg, stress, wf):
    limit = cfg["stop_conditions"]["max_stress_shift"]
    adj = [r for r in stress["rows"] if r["adjacent"]]
    worst = max(adj, key=lambda r: (r["shift_vs_base"] if r["shift_vs_base"] is not None else 9))
    infeasible_adj = [r["scenario"] for r in adj if not r["feasible"]]
    c1 = stress["base"]["feasible"]
    worst_shift = worst["shift_vs_base"] if worst["shift_vs_base"] is not None else float("inf")
    c2 = worst_shift <= limit + 1e-9 and not infeasible_adj
    wy = wf["performance"]["constrained"]["worst_calendar_year_return"]
    c3 = wy >= -cfg["limits"]["loss_limit_95"]
    return {
        "conditions": [
            {"id": "S1", "test": "A portfolio passes every rule of the base mandate", "ok": c1,
             "evidence": "feasible" if c1 else "no feasible mix"},
            {"id": "S2", "test": f"No single adjacent stress moves the portfolio more than {limit:.0%} one-way "
                                 "(the S7 turnover limit) or makes it infeasible", "ok": c2,
             "evidence": (f"largest: {worst['scenario']} = {worst_shift:.0%}" if worst_shift != float('inf')
                          else f"largest: {worst['scenario']} infeasible")
                         + (f"; infeasible: {', '.join(infeasible_adj)}" if infeasible_adj else "")},
            {"id": "S3", "test": "Walk-forward worst calendar year no worse than -10%", "ok": c3,
             "evidence": f"{wf['performance']['constrained']['worst_calendar_year']}: {wy:.1%}"},
        ],
        "stop": not (c1 and c2 and c3),
    }


# ---------------------------------------------------------------- signal test (point-in-time)

def signal_test(cfg, prices, curve):
    """Does the term spread known before month t separate IEF-minus-BIL returns in month t?"""
    ief, bil = prices.returns("IEF"), prices.returns("BIL")
    groups = {"inverted": [], "positive": []}
    rows = []
    for i in range(1, len(prices.months)):
        m, prev = prices.months[i], prices.months[i - 1]
        if m not in ief or m not in bil:
            continue
        reading = curve.value_known_on(month_end_decision_date(prev), cfg["signal"]["lag_business_days"])
        diff = ief[m] - bil[m]
        key = "inverted" if reading["spread_pct"] < 0 else "positive"
        groups[key].append(diff)
        rows.append((m, reading["observation_date"], reading["spread_pct"], diff))
    out = {}
    for k, v in groups.items():
        n = len(v)
        mean = sum(v) / n
        sd = sqrt(sum((x - mean) ** 2 for x in v) / (n - 1))
        out[k] = {"months": n, "mean_annualised": mean * 12, "t_stat": mean / (sd / sqrt(n)),
                  "hit_rate_ief_beats_bil": sum(x > 0 for x in v) / n}
    return {"groups": out, "first_month": rows[0][0], "last_month": rows[-1][0], "rows": rows}
