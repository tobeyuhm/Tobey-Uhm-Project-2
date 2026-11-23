"""Download and freeze the two Project 2 data sets (standard library only).

    python tools/download_data.py

Writes, then never changes on its own:
  data/prices_monthly.csv      Yahoo Finance monthly adjusted closes (dividends reinvested,
                               net of fund expense ratios), first trading day label per month
  data/treasury_curve_daily.csv U.S. Treasury daily par yield curve: 3-month and 10-year
  data/data_snapshot.json      download time, row counts, SHA-256 of each file

The app and the analysis read only the frozen files, so a rerun of this script is the only
way the inputs change. Rerunning on a later date will change the files (new months, and
Yahoo restates adjusted closes after each distribution) - record that as a new snapshot.
"""

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TICKERS = ("BIL", "IEF", "AGG", "LQD", "ACWI", "JOBY")
START = int(datetime(2008, 4, 1, tzinfo=timezone.utc).timestamp())   # ACWI's first full month
END = int(datetime(2026, 11, 1, tzinfo=timezone.utc).timestamp())    # excludes incomplete Nov 2026
TREASURY_YEARS = range(2008, 2027)
TREASURY_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
    "&field_tdr_date_value={year}&page&_format=csv"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (FIN43900 Project 2 data download)"}


def fetch(url):
    with urlopen(Request(url, headers=HEADERS), timeout=60) as response:
        return response.read()


def monthly_adjusted_closes(ticker):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={START}&period2={END}&interval=1mo&events=history")
    result = json.loads(fetch(url))["chart"]["result"][0]
    closes = result["indicators"]["adjclose"][0]["adjclose"]
    values = {}
    for stamp, close in zip(result["timestamp"], closes):
        if close is None:
            continue
        month = datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m")
        values[month] = close
    return values


def download_prices():
    data = {ticker: monthly_adjusted_closes(ticker) for ticker in TICKERS}
    months = sorted(set().union(*data.values()))
    path = DATA / "prices_monthly.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["month", *TICKERS])
        for month in months:
            row = [month]
            for ticker in TICKERS:
                value = data[ticker].get(month)
                row.append("" if value is None else f"{value:.6f}")
            writer.writerow(row)
    return path, len(months)


def download_treasury():
    rows = []
    for year in TREASURY_YEARS:
        text = fetch(TREASURY_URL.format(year=year)).decode("utf-8-sig")
        for record in csv.DictReader(StringIO(text)):
            month, day, yr = record["Date"].split("/")
            three = record.get("3 Mo", "").strip()
            ten = record.get("10 Yr", "").strip()
            if three and ten:
                rows.append((f"{yr}-{month}-{day}", three, ten))
    rows.sort()
    path = DATA / "treasury_curve_daily.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "y3m_pct", "y10_pct"])
        writer.writerows(rows)
    return path, len(rows)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    DATA.mkdir(exist_ok=True)
    prices, price_rows = download_prices()
    treasury, treasury_rows = download_treasury()
    snapshot = {
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": {
            prices.name: {"rows": price_rows, "sha256": sha256(prices),
                          "source": "Yahoo Finance chart API, interval=1mo, adjclose"},
            treasury.name: {"rows": treasury_rows, "sha256": sha256(treasury),
                            "source": "U.S. Treasury daily par yield curve CSV"},
        },
    }
    (DATA / "data_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # network failures should say what to do, not crash silently
        print(f"Download failed: {error}\nThe frozen files in data/ are unchanged only if this "
              "failed before writing; check git status.", file=sys.stderr)
        sys.exit(1)
