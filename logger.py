from __future__ import annotations

import argparse
import datetime as dt
import time
import schedule

from src.data import FetchConfig, fetch_markets
from src.analytics import add_derived_columns
from src.storage import append_snapshot


def job(source: str, per_page: int):
    ts = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    cfg = FetchConfig(source=source, per_page=per_page)
    df = fetch_markets(cfg)
    df = add_derived_columns(df)
    append_snapshot(df, ts=ts)
    print(f"[{ts}] Logged {len(df)} coins")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="coingecko", choices=["coingecko", "coinmarketcap_scrape"])
    ap.add_argument("--per_page", type=int, default=200)
    ap.add_argument("--every_minutes", type=int, default=15)
    args = ap.parse_args()

    job(args.source, args.per_page)
    schedule.every(args.every_minutes).minutes.do(job, args.source, args.per_page)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
