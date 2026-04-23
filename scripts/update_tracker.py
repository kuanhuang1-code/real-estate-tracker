#!/usr/bin/env python3
import csv
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

ZILLOW_URL = "https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
TARGET_MARKETS = {
    "san-mateo": {"region_name": "San Mateo", "state": "CA", "medianSqft": 1650, "pricePerSqft": 970},
    "albany": {"region_name": "Albany", "state": "CA", "medianSqft": 1450, "pricePerSqft": 815},
}


def build_market_data(csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    history = {}
    area_data = {}
    latest_month = None
    last_data_date = None

    for row in reader:
        for slug, config in TARGET_MARKETS.items():
            if row["RegionName"] == config["region_name"] and row["State"] == config["state"]:
                date_columns = [col for col, value in row.items() if re.match(r"\d{4}-\d{2}-\d{2}", col) and value]
                market_history = [
                    {"date": col[:7], "price": round(float(row[col]))}
                    for col in date_columns[-36:]
                ]
                history[slug] = market_history
                area_data[slug] = {
                    "medianSqft": config["medianSqft"],
                    "pricePerSqft": config["pricePerSqft"],
                    "basePrice": market_history[-1]["price"],
                }
                if latest_month is None or date_columns[-1][:7] > latest_month:
                    latest_month = date_columns[-1][:7]
                    last_data_date = date_columns[-1]
                break

    missing = sorted(set(TARGET_MARKETS) - set(history))
    if missing:
        raise ValueError(f"Missing target markets in Zillow feed: {', '.join(missing)}")

    return {
        "latest_month": latest_month,
        "last_data_date": last_data_date,
        "area_data": area_data,
        "history": history,
    }


def _replace_once(pattern: str, replacement: str, text: str) -> str:
    updated, count = re.subn(pattern, replacement, text, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Expected one match for pattern: {pattern}")
    return updated


def update_html(html: str, market_data: dict) -> str:
    updated = html
    updated = _replace_once(
        r"<span id='last-update'>[^<]+</span>",
        f"<span id='last-update'>{market_data['latest_month']}</span>",
        updated,
    )
    updated = _replace_once(
        r"const AREA_DATA = .*?;",
        "const AREA_DATA = " + json.dumps(market_data["area_data"], separators=(",", ": ")) + ";",
        updated,
    )
    updated = _replace_once(
        r"const HISTORY = .*?;",
        "const HISTORY = " + json.dumps(market_data["history"], separators=(",", ": ")) + ";",
        updated,
    )
    updated = _replace_once(
        r"var lastDataDate = new Date\('[0-9\-]+'\);",
        f"var lastDataDate = new Date('{market_data['last_data_date']}');",
        updated,
    )
    return updated


def fetch_csv(url: str = ZILLOW_URL) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    index_path = repo_root / "index.html"
    html = index_path.read_text()
    market_data = build_market_data(fetch_csv())
    updated_html = update_html(html, market_data)
    index_path.write_text(updated_html)
    print(f"Updated {index_path} through {market_data['latest_month']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
