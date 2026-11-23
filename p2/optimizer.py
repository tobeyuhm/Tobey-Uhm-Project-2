"""Constrained portfolio: an exhaustive long-only grid search (Lab 15), now mandate-aware.

No solver black box: every whole-portfolio mix in `step` increments is tried, every mandate
rule is applied, and the lowest-volatility survivor wins. Infeasible returns None plus a
diagnosis, because "no mix passes" is a decision-relevant answer, not an error.
"""

from functools import lru_cache
from math import sqrt


@lru_cache(maxsize=16)
def _grid(n_assets, units):
    """All tuples of n non-negative integers summing to units."""
    out = []

    def rec(prefix, remaining, left):
        if left == 1:
            out.append(prefix + (remaining,))
            return
        for k in range(remaining + 1):
            rec(prefix + (k,), remaining - k, left - 1)

    rec((), units, n_assets)
    return tuple(out)


def optimize(est, *, min_return, reserve_eligible=(), reserve_min=0.0, caps=None,
             loss_limit=None, z=1.645, step=0.05, current=None, cost_bps=None,
             cost_multiplier=1.0):
    """Minimise volatility subject to: long-only, sum = 1, reserve >= reserve_min,
    weight <= cap per capped asset, expected return net of one-time trading cost >= min_return,
    and (optionally) one-year 95% loss <= loss_limit.
    """
    names = est["tickers"]
    units = round(1 / step)
    if abs(units * step - 1) > 1e-9:
        raise ValueError("Grid step must divide 100% evenly.")
    caps = caps or {}
    current = current or {}
    cost_bps = cost_bps or {}
    mu = [est["mu"][n] for n in names]
    cov = [[est["cov"][a][b] for b in names] for a in names]
    cap_units = [caps.get(n, 1.0) / step + 1e-9 for n in names]
    reserve_idx = [i for i, n in enumerate(names) if n in reserve_eligible]
    cur = [current.get(n, 0.0) for n in names]
    # Current holdings outside the estimated universe are sold in full.
    sold_outside = sum(abs(w) * cost_bps.get(n, 0) / 1e4 for n, w in current.items() if n not in names)
    bps = [cost_bps.get(n, 0) / 1e4 for n in names]
    n = len(names)

    best, best_var, tried, passed_rules = None, None, 0, 0
    max_net_return = None
    for combo in _grid(n, units):
        tried += 1
        if any(combo[i] > cap_units[i] for i in range(n)):
            continue
        w = [c * step for c in combo]
        if sum(w[i] for i in reserve_idx) < reserve_min - 1e-9:
            continue
        cost = cost_multiplier * (sold_outside + sum(abs(w[i] - cur[i]) * bps[i] for i in range(n)))
        net = sum(w[i] * mu[i] for i in range(n)) - cost
        if max_net_return is None or net > max_net_return:
            max_net_return = net
        if net < min_return - 1e-12:
            continue
        var = 0.0
        for i in range(n):
            if w[i]:
                row = cov[i]
                var += w[i] * sum(row[j] * w[j] for j in range(n) if w[j])
        if loss_limit is not None and -(net - z * sqrt(max(var, 0))) > loss_limit + 1e-12:
            continue
        passed_rules += 1
        if best_var is None or var < best_var - 1e-15:
            best, best_var, best_net, best_cost = w, var, net, cost

    diagnosis = {"mixes_tried": tried, "mixes_passing": passed_rules,
                 "max_net_return_within_hard_rules": max_net_return}
    if best is None:
        return None, diagnosis
    weights = {name: round(wt, 10) for name, wt in zip(names, best)}
    gross = sum(weights[nm] * est["mu"][nm] for nm in names)
    vol = sqrt(max(best_var, 0))
    return ({"weights": weights, "expected_return": gross, "net_return": best_net,
             "trading_cost": best_cost, "volatility": vol, "loss_95": -(best_net - z * vol)},
            diagnosis)


def equal_weight(names):
    return {n: 1 / len(names) for n in names}


def inverse_volatility(est):
    raw = {n: 1 / est["vol"][n] for n in est["tickers"]}
    total = sum(raw.values())
    return {n: v / total for n, v in raw.items()}
