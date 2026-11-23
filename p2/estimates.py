"""Historical estimates: the Lab 15 conventions, unchanged.

Expected return = arithmetic mean monthly return x 12. Volatility = sample standard
deviation x sqrt(12). Covariance = sample covariance x 12. These are estimates of the past,
not forecasts - the stress run exists because they are unstable.
"""

from math import sqrt


def estimate(returns_by_ticker):
    """returns_by_ticker: {ticker: [monthly returns, same months]} -> dict of mu, vol, cov, corr."""
    tickers = list(returns_by_ticker)
    if not tickers:
        raise ValueError("No asset has a full estimation window.")
    n = len(next(iter(returns_by_ticker.values())))
    if n < 3:
        raise ValueError("At least three monthly returns are needed.")
    if any(len(v) != n for v in returns_by_ticker.values()):
        raise ValueError("Every asset must have the same months.")
    means = {t: sum(v) / n for t, v in returns_by_ticker.items()}
    cov = {a: {} for a in tickers}
    for i, a in enumerate(tickers):
        for b in tickers[i:]:
            c = sum((x - means[a]) * (y - means[b])
                    for x, y in zip(returns_by_ticker[a], returns_by_ticker[b])) / (n - 1) * 12
            cov[a][b] = cov[b][a] = c
    vol = {t: sqrt(cov[t][t]) for t in tickers}
    corr = {a: {b: (cov[a][b] / (vol[a] * vol[b]) if vol[a] and vol[b] else 0.0)
                for b in tickers} for a in tickers}
    return {"tickers": tickers, "n_months": n, "mu": {t: means[t] * 12 for t in tickers},
            "vol": vol, "cov": cov, "corr": corr}


def from_inputs(mu, vol, corr):
    """Build the same structure from typed-in assumptions (used for the Lab 15 known answer)."""
    tickers = list(mu)
    cov = {a: {b: corr[a][b] * vol[a] * vol[b] for b in tickers} for a in tickers}
    return {"tickers": tickers, "n_months": None, "mu": dict(mu), "vol": dict(vol),
            "cov": cov, "corr": corr}


def portfolio_stats(weights, est, z=1.645):
    tickers = est["tickers"]
    mu = sum(weights.get(t, 0.0) * est["mu"][t] for t in tickers)
    var = sum(weights.get(a, 0.0) * weights.get(b, 0.0) * est["cov"][a][b]
              for a in tickers for b in tickers)
    vol = sqrt(max(var, 0.0))
    return {"expected_return": mu, "volatility": vol, "loss_95": -(mu - z * vol)}
