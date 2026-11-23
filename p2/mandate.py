"""The mandate as rules a computer can check (Lab 13, generalised to any holdings table).

Each rule returns the measured value, the limit, and pass / FAIL, so the app can say
*which* rule a portfolio breaks. Weights are decimals (0.08 = 8%).
"""

TOL = 1e-9


def reserve_minimum(cfg):
    return cfg["quarters_to_cover"] * cfg["quarterly_distribution_usd_m"] / cfg["reserve_usd_m"]


def objective_return(cfg):
    o = cfg["objective"]
    return (o["cpi_assumption_pct"] + o["real_return_pct"]) / 100


def one_way_turnover(new, old):
    names = set(new) | set(old)
    return 0.5 * sum(abs(new.get(n, 0.0) - old.get(n, 0.0)) for n in names)


def trading_cost(new, old, assets, multiplier=1.0):
    """One-time cost of moving from old to new weights, as a decimal of the reserve."""
    names = set(new) | set(old)
    return multiplier * sum(abs(new.get(n, 0.0) - old.get(n, 0.0)) * assets[n]["trade_cost_bps"] / 1e4
                            for n in names)


def company_weights(weights, assets):
    out = {}
    for name, w in weights.items():
        info = assets[name]
        if not info.get("issuer_exempt", False):
            out[info["issuer"]] = out.get(info["issuer"], 0.0) + w
    return out


def check(weights, cfg, stats=None, net_return=None, current=None):
    """Return a list of rule dicts: id, rule, measured, limit, passed, kind.

    kind = 'hard' (mandate constraint), 'objective' (S2), 'risk' (S9 as operationalised),
    'governance' (S7: over the limit means 'needs committee approval', not a breach).
    """
    assets, limits = cfg["assets"], cfg["limits"]
    total = sum(weights.values())
    lowest = min(weights.values()) if weights else 0.0
    reserve = sum(w for n, w in weights.items() if assets[n]["reserve_eligible"])
    liquid = sum(w for n, w in weights.items()
                 if assets[n]["days_to_redeem"] <= limits["liquidity_window_days"])
    companies = company_weights(weights, assets)
    largest_name, largest = max(companies.items(), key=lambda kv: kv[1], default=("none", 0.0))
    r_min = reserve_minimum(cfg)

    rules = [
        dict(id="M1", rule="Weights sum to 100%", measured=total, limit="= 100%",
             passed=abs(total - 1) < 1e-6, kind="hard"),
        dict(id="M2", rule="Long-only (lowest weight)", measured=lowest, limit=">= 0%",
             passed=lowest >= -TOL, kind="hard"),
        dict(id="M3", rule=f"Reserve-eligible (BIL, IEF) >= {r_min:.1%}", measured=reserve,
             limit=f">= {r_min:.1%}", passed=reserve >= r_min - TOL, kind="hard"),
        dict(id="M4", rule=f"Redeemable in {limits['liquidity_window_days']} business days",
             measured=liquid, limit=f">= {limits['min_liquid_share']:.0%}",
             passed=liquid >= limits["min_liquid_share"] - TOL, kind="hard"),
        dict(id="M5", rule=f"Largest single company ({largest_name})", measured=largest,
             limit=f"<= {limits['issuer_limit']:.0%}",
             passed=largest <= limits["issuer_limit"] + TOL, kind="hard"),
    ]
    if stats is not None:
        target = objective_return(cfg)
        ret = stats["expected_return"] if net_return is None else net_return
        rules.append(dict(id="O1", rule="Expected return net of costs >= CPI + 4%", measured=ret,
                          limit=f">= {target:.1%}", passed=ret >= target - TOL, kind="objective"))
        rules.append(dict(id="R1", rule="One-year 95% loss (mu - 1.645 sigma)",
                          measured=stats["loss_95"], limit=f"<= {limits['loss_limit_95']:.0%}",
                          passed=stats["loss_95"] <= limits["loss_limit_95"] + TOL, kind="risk"))
    if current is not None:
        t = one_way_turnover(weights, current)
        rules.append(dict(id="G1", rule="One-way turnover from current holdings", measured=t,
                          limit=f"<= {limits['turnover_limit']:.0%} without committee approval",
                          passed=t <= limits["turnover_limit"] + TOL, kind="governance"))
    return rules


def verdict(rules):
    """'passes every checkable rule' or 'FAILS M5, O1' - governance flags are reported apart."""
    failed = [r["id"] for r in rules if not r["passed"] and r["kind"] != "governance"]
    approval = [r["id"] for r in rules if not r["passed"] and r["kind"] == "governance"]
    text = "PASS - every checkable rule" if not failed else "FAIL - " + ", ".join(failed)
    if approval:
        text += " (turnover needs committee approval)"
    return {"passed": not failed, "failed_rules": failed, "needs_approval": bool(approval),
            "text": text}
