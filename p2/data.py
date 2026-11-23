"""Load the frozen data files and enforce the point-in-time boundary.

Everything downstream asks this module for data "as known at" a month or a date, so no
function can see a price or yield that was not yet published at the decision time.
"""

import csv
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config" / "mandate.json"


def load_config(path=CONFIG):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Prices:
    """Monthly adjusted closes. Month label 'YYYY-MM' = the close of that month's last trading day.

    Yahoo labels a monthly bar by its first day; the bar's adjusted close is the month-end
    close, so the 2026-10 value is known after the close on 2026-10-30.
    """

    def __init__(self, months, series):
        self.months = months                  # sorted list of 'YYYY-MM'
        self.series = series                  # ticker -> list[float | None], aligned to months

    @classmethod
    def load(cls, path=DATA / "prices_monthly.csv", assets=None):
        with Path(path).open(newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        header, body = rows[0], rows[1:]
        tickers = header[1:]
        months = [row[0] for row in body]
        if months != sorted(months) or len(set(months)) != len(months):
            raise ValueError("Price months must be unique and in ascending order.")
        series = {}
        for col, ticker in enumerate(tickers, start=1):
            first_valid = (assets or {}).get(ticker, {}).get("first_valid_month")
            values = []
            for month, row in zip(months, body):
                text = row[col].strip()
                value = float(text) if text else None
                if value is not None and value <= 0:
                    raise ValueError(f"{ticker} {month}: price must be positive.")
                if first_valid and month < first_valid:
                    value = None              # documented exclusion (pre-listing SPAC prices)
                values.append(value)
            series[ticker] = values
        return cls(months, series)

    def returns(self, ticker):
        """Monthly simple returns keyed by the month in which they are earned."""
        out = {}
        values = self.series[ticker]
        for i in range(1, len(self.months)):
            if values[i - 1] is not None and values[i] is not None:
                out[self.months[i]] = values[i] / values[i - 1] - 1
        return out

    def window(self, tickers, end_month, n_months):
        """The last n monthly returns ending at end_month (inclusive), for tickers with a full window.

        Returns (months, {ticker: [returns]}) and silently drops a ticker without n returns -
        the caller reports which tickers were available.
        """
        if end_month not in self.months:
            raise ValueError(f"{end_month} is not in the price file.")
        end = self.months.index(end_month)
        months = self.months[max(1, end - n_months + 1): end + 1]
        if len(months) < n_months:
            raise ValueError(f"Only {len(months)} months of returns end at {end_month}; need {n_months}.")
        out = {}
        for ticker in tickers:
            rets = self.returns(ticker)
            if all(m in rets for m in months):
                out[ticker] = [rets[m] for m in months]
        return months, out


class TreasuryCurve:
    """Daily U.S. Treasury par yields (percent). value_known_on() applies the publication lag."""

    def __init__(self, rows):
        self.rows = rows                     # sorted list of (date, y3m, y10)

    @classmethod
    def load(cls, path=DATA / "treasury_curve_daily.csv"):
        with Path(path).open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = [(date.fromisoformat(r["date"]), float(r["y3m_pct"]), float(r["y10_pct"]))
                    for r in reader]
        rows.sort()
        return cls(rows)

    def value_known_on(self, decision_date, lag_business_days=1):
        """Latest observation dated strictly before the decision date, minus extra lag days.

        lag_business_days=1 means a decision on day D uses the curve of the last business day
        before D (the Lab 17 finding: DGS10 for D-1 was the last value known on D).
        """
        if isinstance(decision_date, str):
            decision_date = date.fromisoformat(decision_date)
        eligible = [row for row in self.rows if row[0] < decision_date]
        if len(eligible) < lag_business_days:
            raise ValueError(f"No Treasury curve observation is known before {decision_date}.")
        obs_date, y3m, y10 = eligible[-lag_business_days]
        return {"observation_date": obs_date.isoformat(), "y3m_pct": y3m, "y10_pct": y10,
                "spread_pct": round(y10 - y3m, 4)}


def month_end_decision_date(month):
    """Last weekday of a 'YYYY-MM' month: the rebalance date for a month-end decision."""
    year, mon = (int(x) for x in month.split("-"))
    nxt = date(year + (mon == 12), mon % 12 + 1, 1)
    day = nxt - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def next_day(d):
    return d + timedelta(days=1)
