from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
import pandas as pd


PRICE_BINS = [
    (0.0, 0.05, "$0 - $0.05"),
    (0.05, 0.5, "$0.05 - $0.5"),
    (0.5, 5.0, "$0.5 - $5"),
    (5.0, 50.0, "$5 - $50"),
    (50.0, float("inf"), ">$50"),
]


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["pct_1h", "pct_24h", "pct_7d"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["price"] = pd.to_numeric(out["price"], errors="coerce")

    out["prev_price_1h"] = out["price"] / (1.0 + (out["pct_1h"].fillna(0) / 100.0))
    out["prev_price_7d"] = out["price"] / (1.0 + (out["pct_7d"].fillna(0) / 100.0))
    out["prev_price_24h"] = out["price"] / (1.0 - (out["pct_24h"].abs().fillna(0) / 100.0))

    out["avg_downfall_pct"] = out[["pct_1h", "pct_24h", "pct_7d"]].abs().mean(axis=1)

    def bucket(p):
        if pd.isna(p):
            return None
        for lo, hi, label in PRICE_BINS:
            if lo <= p < hi:
                return label
        return None

    out["price_range"] = out["price"].apply(bucket)
    out["price_category_0_50"] = np.where(out["price"] <= 50, "$0 - $50", ">$50")
    out["price_category_10"] = np.where(out["price"] >= 10, ">= $10", "< $10")
    return out


def filter_by_price_ranges(df: pd.DataFrame, selected_ranges: List[str]) -> pd.DataFrame:
    if not selected_ranges:
        return df.iloc[0:0].copy()
    return df[df["price_range"].isin(selected_ranges)].copy()


def kpi_least_avg_downfall(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"coin_name": None, "coin_symbol": None, "price": None, "avg_downfall_pct": None, "count": 0}
    best = df.sort_values("avg_downfall_pct", ascending=True).iloc[0]
    return {
        "coin_name": best["coin_name"],
        "coin_symbol": best["coin_symbol"],
        "price": float(best["price"]),
        "avg_downfall_pct": float(best["avg_downfall_pct"]),
        "count": int(df.shape[0]),
    }


def top10_for_range_0_5_prev_prices(df: pd.DataFrame) -> pd.DataFrame:
    d = df[(df["price"] >= 0) & (df["price"] <= 5)].copy()
    d = d.sort_values("prev_price_1h", ascending=False).head(10)
    return d[["coin_name", "coin_symbol", "price", "prev_price_24h", "prev_price_7d", "prev_price_1h", "pct_1h", "pct_24h", "pct_7d"]]


def top10_price_increase(df: pd.DataFrame, price_category: str) -> pd.DataFrame:
    d = df.copy()
    if price_category in [">= $10", "< $10"]:
        d = d[d["price_category_10"] == price_category].copy()
    d["price_change_1h"] = d["price"] - d["prev_price_1h"]
    d = d.sort_values("price_change_1h", ascending=False).head(10)
    return d[["coin_name", "coin_symbol", "prev_price_1h", "price", "price_change_1h"]]


def filter_name_prefix(df: pd.DataFrame) -> pd.DataFrame:
    prefixes = tuple(list("AEIOUaeiou") + ["B", "C", "D", "b", "c", "d"])
    return df[df["coin_name"].astype(str).str.startswith(prefixes)].copy()


def top10_by_volume(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values("volume_24h", ascending=False).head(10).copy()
    return d[["coin_name", "coin_symbol", "volume_24h", "price"]]


def compare_two_coins(df: pd.DataFrame, name1: str, name2: str) -> Dict[str, Any]:
    d = df.copy()
    d["coin_name_norm"] = d["coin_name"].astype(str).str.lower().str.strip()
    r1 = d[d["coin_name_norm"] == name1.lower().strip()]
    r2 = d[d["coin_name_norm"] == name2.lower().strip()]
    if r1.empty or r2.empty:
        return {"ok": False, "error": "One or both coin names not found in the current dataset."}

    a = r1.iloc[0]
    b = r2.iloc[0]

    def pack(row):
        return {
            "Coin Name": row["coin_name"],
            "Symbol": row["coin_symbol"],
            "Price": float(row["price"]),
            "Volume(24h)": float(row["volume_24h"]),
            "Market Cap": float(row["market_cap"]),
            "Circulating Supply": float(row["circulating_supply"]),
        }

    diff = {
        "Volume(24h) Diff": float(a["volume_24h"] - b["volume_24h"]),
        "Circulating Supply Diff": float(a["circulating_supply"] - b["circulating_supply"]),
        "Market Cap Diff": float(a["market_cap"] - b["market_cap"]),
    }

    return {"ok": True, "coin1": pack(a), "coin2": pack(b), "diff": diff}


def pie_top5_volume_with_others(df: pd.DataFrame, price_cat: str) -> pd.DataFrame:
    d = df.copy()
    if price_cat in ["$0 - $50", ">$50"]:
        d = d[d["price_category_0_50"] == price_cat].copy()

    d = d.sort_values("volume_24h", ascending=False)
    top5 = d.head(5).copy()
    others = d.iloc[5:].copy()

    rows = [{"coin_name": r["coin_name"], "volume_24h": float(r["volume_24h"])} for _, r in top5.iterrows()]
    if not others.empty:
        rows.append({"coin_name": "Others", "volume_24h": float(others["volume_24h"].sum())})

    return pd.DataFrame(rows)
