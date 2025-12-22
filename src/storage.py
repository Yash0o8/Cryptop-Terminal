from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd


def init_db(db_path: str = "data/crypto.db") -> str:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshots (
                ts TEXT NOT NULL,
                coin_id TEXT,
                coin_name TEXT,
                coin_symbol TEXT,
                price REAL,
                pct_1h REAL,
                pct_24h REAL,
                pct_7d REAL,
                volume_24h REAL,
                market_cap REAL,
                circulating_supply REAL
            )
            """
        )
        con.commit()
    return db_path


def append_snapshot(df: pd.DataFrame, ts: str, db_path: str = "data/crypto.db") -> None:
    init_db(db_path)
    cols = ["id", "coin_name", "coin_symbol", "price", "pct_1h", "pct_24h", "pct_7d", "volume_24h", "market_cap", "circulating_supply"]
    x = df.copy()
    x = x[cols].rename(columns={"id": "coin_id"})
    x.insert(0, "ts", ts)
    with sqlite3.connect(db_path) as con:
        x.to_sql("market_snapshots", con, if_exists="append", index=False)


def load_recent(db_path: str = "data/crypto.db", limit: int = 2000) -> pd.DataFrame:
    init_db(db_path)
    with sqlite3.connect(db_path) as con:
        q = f"SELECT * FROM market_snapshots ORDER BY ts DESC LIMIT {int(limit)}"
        return pd.read_sql_query(q, con)
