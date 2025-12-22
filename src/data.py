from __future__ import annotations

import pandas as pd
import requests
from dataclasses import dataclass
from typing import Literal
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (CryptoDashboard; +https://streamlit.io)"


@dataclass
class FetchConfig:
    source: Literal["coingecko", "coinmarketcap_scrape"] = "coingecko"
    vs_currency: str = "usd"
    per_page: int = 200
    page: int = 1
    timeout: int = 30


def fetch_coingecko_markets(cfg: FetchConfig) -> pd.DataFrame:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": cfg.vs_currency,
        "order": "market_cap_desc",
        "per_page": cfg.per_page,
        "page": cfg.page,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d",
    }
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, params=params, headers=headers, timeout=cfg.timeout)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data)

    out = pd.DataFrame({
        "coin_name": df.get("name"),
        "coin_symbol": df.get("symbol").str.upper(),
        "price": df.get("current_price").astype(float),
        "pct_1h": df.get("price_change_percentage_1h_in_currency").astype(float),
        "pct_24h": df.get("price_change_percentage_24h_in_currency").astype(float),
        "pct_7d": df.get("price_change_percentage_7d_in_currency").astype(float),
        "volume_24h": df.get("total_volume").astype(float),
        "market_cap": df.get("market_cap").astype(float),
        "circulating_supply": df.get("circulating_supply").astype(float),
        "last_updated": df.get("last_updated"),
        "id": df.get("id"),
    })
    return out


def fetch_coinmarketcap_scrape(limit: int = 200, timeout: int = 30) -> pd.DataFrame:
    url = "https://coinmarketcap.com/"
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    rows = soup.select("table tbody tr")
    records = []
    for tr in rows[:limit]:
        txt = tr.get_text(" ", strip=True)
        if txt:
            records.append({"raw": txt})

    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError("CoinMarketCap HTML did not contain the coins table (likely JS-rendered). Use CoinGecko source.")
    return df


def fetch_markets(cfg: FetchConfig) -> pd.DataFrame:
    if cfg.source == "coinmarketcap_scrape":
        return fetch_coinmarketcap_scrape(limit=cfg.per_page, timeout=cfg.timeout)
    return fetch_coingecko_markets(cfg)
