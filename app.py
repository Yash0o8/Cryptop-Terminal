from __future__ import annotations

import re
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from src.data import FetchConfig, fetch_markets
from src.analytics import add_derived_columns
from src.storage import load_recent


st.set_page_config(page_title="Crypto Dashboard", page_icon="📈", layout="wide")


COINBASE_CSS = """
<style>
:root{
  --bg:#050A14;          /* deep black-blue */
  --panel:#0B1220;       /* card background */
  --panel2:#0E1A30;      /* slightly brighter panel */
  --stroke:#1C2B45;      /* borders */
  --text:#EAF2FF;        /* main text */
  --muted:#9BB3D3;       /* muted text */
  --blue:#2F81F7;        /* primary blue */
  --blue2:#0B5CFF;       /* strong blue */
  --glow:0 0 22px rgba(47,129,247,.25);
}

/* page background */
html, body, [class*="css"] {
  background: radial-gradient(1100px 520px at 20% 10%, rgba(47,129,247,.12), transparent 55%),
              radial-gradient(900px 420px at 80% 15%, rgba(11,92,255,.10), transparent 55%),
              linear-gradient(180deg, #040812, var(--bg)) !important;
  color: var(--text) !important;
}

.block-container {
  max-width: 1320px;
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}

/* sidebar */
[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(11,18,32,.95), rgba(6,10,20,.98)) !important;
  border-right: 1px solid var(--stroke) !important;
}
[data-testid="stSidebar"] *{
  color: var(--text) !important;
}

/* hide top toolbar/footer */
header, footer {visibility: hidden;}
div[data-testid="stToolbar"] {visibility: hidden; height: 0px;}

/* cards */
.card{
  background: linear-gradient(180deg, rgba(14,26,48,.85), rgba(11,18,32,.88));
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 14px 14px;
  box-shadow: 0 14px 40px rgba(0,0,0,.45);
}
.card-title{ font-size: 14px; font-weight: 800; color: var(--text); margin-bottom: 2px; }
.card-sub{ font-size: 12px; color: var(--muted); }

/* KPI grid */
.kpi-wrap{
  display:grid;
  grid-template-columns: repeat(5, minmax(0,1fr));
  gap: 12px;
  margin-top: 12px;
  margin-bottom: 10px;
}
.kpi{
  background: linear-gradient(180deg, rgba(14,26,48,.85), rgba(11,18,32,.88));
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 12px 12px;
  box-shadow: 0 14px 40px rgba(0,0,0,.45);
}
.kpi .label{ color: var(--muted); font-size: 12px; font-weight: 700; }
.kpi .value{ font-size: 18px; font-weight: 900; margin-top: 4px; color: var(--text); }
.kpi .hint{ color: var(--muted); font-size: 11px; margin-top: 2px; }

/* tabs */
.stTabs [data-baseweb="tab-list"]{ gap: 8px; }
.stTabs [data-baseweb="tab"]{
  background: rgba(11,18,32,.85);
  border: 1px solid var(--stroke);
  border-radius: 999px;
  padding: 8px 12px;
  font-weight: 800;
  color: var(--text);
}
.stTabs [aria-selected="true"]{
  background: rgba(47,129,247,.18) !important;
  border: 1px solid rgba(47,129,247,.55) !important;
  color: var(--text) !important;
  box-shadow: var(--glow);
}

/* buttons */
.stButton button{
  border-radius: 12px !important;
  border: 1px solid rgba(47,129,247,.55) !important;
  background: linear-gradient(180deg, var(--blue), var(--blue2)) !important;
  color: white !important;
  font-weight: 900 !important;
  box-shadow: var(--glow);
}
.stButton button:hover{
  filter: brightness(1.06);
}

/* inputs */
.stTextInput input, .stSelectbox select, .stMultiSelect div, .stSlider{
  border-radius: 12px !important;
}
div[data-baseweb="select"] > div{
  background: rgba(11,18,32,.85) !important;
  border: 1px solid var(--stroke) !important;
  color: var(--text) !important;
}
input{
  background: rgba(11,18,32,.85) !important;
  border: 1px solid var(--stroke) !important;
  color: var(--text) !important;
}

/* dataframe */
[data-testid="stDataFrame"]{
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--stroke);
  box-shadow: 0 14px 40px rgba(0,0,0,.45);
}
[data-testid="stDataFrame"] *{
  color: var(--text) !important;
}

/* badges */
.badge{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:6px 10px;
  border-radius:999px;
  background: rgba(11,18,32,.85);
  border: 1px solid var(--stroke);
  color: var(--text);
  font-size: 12px;
  font-weight: 800;
}
.dot{
  width: 8px; height: 8px; border-radius: 999px;
  background: var(--blue);
  box-shadow: var(--glow);
}

/* plotly background blend */
.js-plotly-plot, .plotly, .plot-container{
  background: transparent !important;
}
</style>
"""

st.markdown(COINBASE_CSS, unsafe_allow_html=True)


def fmt_usd(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"${x:,.6f}" if x < 1 else f"${x:,.2f}"


def fmt_pct(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:.2f}%"


def safe_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    num_cols = [
        "price", "pct_1h", "pct_24h", "pct_7d",
        "market_cap", "volume_24h", "circulating_supply"
    ]
    for c in num_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out["coin_name"] = out.get("coin_name", "").astype(str)
    out["coin_symbol"] = out.get("coin_symbol", "").astype(str)
    return out


def add_price_range_bins(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    bins = [-np.inf, 0.05, 0.5, 5, 50, np.inf]
    labels = ["$0 - $0.05", "$0.05 - $0.5", "$0.5 - $5", "$5 - $50", ">$50"]
    out["price_range"] = pd.cut(out["price"], bins=bins, labels=labels, include_lowest=True)
    return out


def prev_price_from_pct_increase(current_price: float, pct: float) -> float:
    if current_price is None or pct is None:
        return np.nan
    if np.isnan(current_price) or np.isnan(pct):
        return np.nan
    denom = 1.0 + (pct / 100.0)
    if denom == 0:
        return np.nan
    return current_price / denom


def prev_price_from_pct_decrease(current_price: float, pct: float) -> float:
    if current_price is None or pct is None:
        return np.nan
    if np.isnan(current_price) or np.isnan(pct):
        return np.nan
    denom = 1.0 - (pct / 100.0)
    if denom == 0:
        return np.nan
    return current_price / denom


def compute_reconstructed_prev_prices(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["prev_price_1h"] = out.apply(
        lambda r: prev_price_from_pct_increase(r["price"], r.get("pct_1h")), axis=1
    )
    out["prev_price_7d"] = out.apply(
        lambda r: prev_price_from_pct_increase(r["price"], r.get("pct_7d")), axis=1
    )
    out["prev_price_24h"] = out.apply(
        lambda r: prev_price_from_pct_decrease(r["price"], r.get("pct_24h")), axis=1
    )

    out["avg_downfall_pct"] = np.nanmean(
        np.vstack([
            np.abs(out.get("pct_1h").to_numpy()),
            np.abs(out.get("pct_24h").to_numpy()),
            np.abs(out.get("pct_7d").to_numpy()),
        ]),
        axis=0
    )
    return out


@st.cache_data(ttl=120)
def load_live(source: str, per_page: int) -> pd.DataFrame:
    cfg = FetchConfig(source=source, per_page=per_page)
    df = fetch_markets(cfg)
    df = add_derived_columns(df)
    df = safe_df(df)
    df = add_price_range_bins(df)
    df = compute_reconstructed_prev_prices(df)
    return df


def valid_name(s: str) -> bool:
    s = (s or "").strip()
    if len(s) <= 2 or len(s) >= 11:
        return False
    return re.search(r"\d", s) is None


with st.sidebar:
    st.subheader("Controls")
    source = st.selectbox("Data source", ["coingecko", "coinmarketcap_scrape"], index=0)
    per_page = st.slider("Coins to fetch", 50, 250, 200, step=10)
    st.divider()
    export_now = st.button("Export current data to Excel", use_container_width=True)
    show_history = st.checkbox("Show SQLite snapshots", value=False)


st.title("Crypto Dashboard")
st.caption("Clean, investor-ready analytics • 6 modules • live market data")

c1, c2, c3 = st.columns([1.2, 1.2, 1.6])
with c1:
    st.markdown("<span class='badge'><span class='dot'></span> Live feed</span>", unsafe_allow_html=True)
with c2:
    st.markdown("<span class='badge'><span class='dot'></span> KPI + Charts</span>", unsafe_allow_html=True)
with c3:
    st.markdown("<span class='badge'><span class='dot'></span> Focused on 6 investor requirements</span>", unsafe_allow_html=True)

df = load_live(source, per_page)

if df is None or df.empty:
    st.error("No data loaded. Try switching the data source or lowering the coin count.")
    st.stop()


if export_now:
    out_dir = Path("exports")
    out_dir.mkdir(exist_ok=True)
    fname = out_dir / f"crypto_export_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    try:
        import xlsxwriter  # noqa: F401
        engine = "xlsxwriter"
    except Exception:
        engine = "openpyxl"

    with pd.ExcelWriter(fname, engine=engine) as writer:
        df.to_excel(writer, index=False, sheet_name="LiveData")
    st.success(f"Exported: {fname} (engine={engine})")


tabs = st.tabs([
    "1) Budget KPIs",
    "2) $0–$5 Top 10",
    "3) Top Increase (1h)",
    "4) Prefix + Working Hours",
    "5) Compare 2 Coins",
    "6) Liquidity Pie",
])


with tabs[0]:
    st.subheader("1) Budget KPIs (price range slicer)")
    st.caption("Investor wants maximum profit with low budget → show the coin with the least average downfall in the selected price range.")

    ranges = ["$0 - $0.05", "$0.05 - $0.5", "$0.5 - $5", "$5 - $50", ">$50"]
    selected_ranges = st.multiselect("Price ranges ($)", ranges, default=["$0.5 - $5", "$5 - $50"])

    f = df[df["price_range"].isin(selected_ranges)].copy() if selected_ranges else df.iloc[0:0].copy()
    f = f.dropna(subset=["avg_downfall_pct", "price"])

    if f.empty:
        st.info("Select at least one price range.")
    else:
        best = f.sort_values("avg_downfall_pct", ascending=True).iloc[0]

        st.markdown(
            f"""
<div class="kpi-wrap">
  <div class="kpi"><div class="label">Coin Name</div><div class="value">{best.get("coin_name","—")}</div><div class="hint">Best in selected range</div></div>
  <div class="kpi"><div class="label">Symbol</div><div class="value">{str(best.get("coin_symbol","—")).upper()}</div><div class="hint">Ticker</div></div>
  <div class="kpi"><div class="label">Current Price</div><div class="value">{fmt_usd(best.get("price"))}</div><div class="hint">USD</div></div>
  <div class="kpi"><div class="label">Avg Downfall %</div><div class="value">{fmt_pct(best.get("avg_downfall_pct"))}</div><div class="hint">Avg(|1h|,|24h|,|7d|)</div></div>
  <div class="kpi"><div class="label">Coins Considered</div><div class="value">{int(f.shape[0])}</div><div class="hint">Records in selection</div></div>
</div>
""",
            unsafe_allow_html=True
        )

        show = f.sort_values("avg_downfall_pct").head(25)[
            ["coin_name", "coin_symbol", "price", "pct_1h", "pct_24h", "pct_7d", "avg_downfall_pct", "volume_24h", "market_cap"]
        ].copy()
        st.dataframe(show, use_container_width=True, height=460)


with tabs[1]:
    st.subheader("2) $0–$5 coins: top 10 (by 1h-before price)")
    st.caption("Within $0–$5, show top 10 coins based on 1h-before price. Chart compares 7d-before and 24h-before prices vs current.")

    d = df[(df["price"] >= 0) & (df["price"] <= 5)].copy()
    d = d.dropna(subset=["prev_price_1h", "prev_price_24h", "prev_price_7d", "price"])
    d = d.sort_values("prev_price_1h", ascending=False).head(10)

    if d.empty:
        st.warning("No coins found in $0–$5 range.")
    else:
        chart = d[["coin_name", "prev_price_7d", "prev_price_24h", "price"]].copy()
        fig = px.bar(
            chart,
            x="coin_name",
            y=["prev_price_7d", "prev_price_24h", "price"],
            barmode="group",
            title="Top 10 ($0–$5): 7d-before vs 24h-before vs Current"
        )
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=50, b=10), legend_title_text="Price")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            d[["coin_name", "coin_symbol", "price", "prev_price_1h", "prev_price_24h", "prev_price_7d"]],
            use_container_width=True,
            height=420
        )


with tabs[2]:
    st.subheader("3) Top 10 price increase vs previous 1 hour")
    st.caption("Assume 1h % is positive change. Show biggest price increase coins, and compare current vs 1h-before.")

    cat = st.radio("Price category", ["< $10", ">= $10"], horizontal=True, index=0)

    d = df.dropna(subset=["price", "prev_price_1h"]).copy()
    d["price_category_10"] = np.where(d["price"] >= 10, ">= $10", "< $10")
    d = d[d["price_category_10"] == cat].copy()
    d["price_change_1h"] = d["price"] - d["prev_price_1h"]
    d = d.sort_values("price_change_1h", ascending=False).head(10)

    if d.empty:
        st.warning("No data for selected category.")
    else:
        fig = px.bar(
            d,
            x="coin_symbol",
            y=["prev_price_1h", "price"],
            barmode="group",
            title="Top 10: Current vs 1h-before (by price increase)"
        )
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=50, b=10), legend_title_text="Price")
        st.plotly_chart(fig, use_container_width=True)

        table = d[["coin_symbol", "coin_name", "price_change_1h"]].copy()
        table["price_change_1h"] = table["price_change_1h"].map(lambda x: f"${x:,.6f}" if x < 1 else f"${x:,.2f}")
        st.dataframe(table, use_container_width=True, height=360)


with tabs[3]:
    st.subheader("4) Prefix filter + Working hours security")
    st.caption("Coins starting with vowels OR B/C/D. Chart visible only from 9 AM to 5 PM (local time).")

    now = dt.datetime.now()
    in_work_hours = 9 <= now.hour < 17

    d = df.copy()
    d = d[d["coin_name"].astype(str).str.match(r"^[AEIOUaeiouBCDbdc]")].copy()
    d = d.dropna(subset=["volume_24h"]).sort_values("volume_24h", ascending=False).head(10)

    if not in_work_hours:
        st.warning("Please open in working hours ( 9 am to 5 pm )")
    else:
        fig = px.bar(
            d.sort_values("volume_24h", ascending=True),
            x="volume_24h",
            y="coin_name",
            orientation="h",
            title="Top 10 Liquidity (Volume 24h)"
        )
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Volume(24h)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(d[["coin_name", "coin_symbol", "volume_24h", "price"]], use_container_width=True, height=360)


with tabs[4]:
    st.subheader("5) Compare two coins")
    st.caption("Enter two coin names. Shows fields + KPI differences. Validation: 3–10 characters, no numbers.")

    col1, col2 = st.columns(2)
    with col1:
        name1 = st.text_input("CoinName1", value="Bitcoin")
    with col2:
        name2 = st.text_input("CoinName2", value="Ethereum")

    if not valid_name(name1) or not valid_name(name2):
        st.error("Invalid input. Coin name must be 3–10 characters and contain no numbers.")
    else:
        d = df.copy()
        d["nm"] = d["coin_name"].astype(str).str.lower().str.strip()
        a = d[d["nm"] == name1.lower().strip()]
        b = d[d["nm"] == name2.lower().strip()]

        if a.empty or b.empty:
            st.error("One or both coin names not found in current live dataset.")
        else:
            a = a.iloc[0]
            b = b.iloc[0]

            table = pd.DataFrame({
                "Field": ["Symbol", "Price", "Volume(24h)", "Market Cap", "Circulating Supply"],
                "CoinName1": [a.get("coin_symbol"), a.get("price"), a.get("volume_24h"), a.get("market_cap"), a.get("circulating_supply")],
                "CoinName2": [b.get("coin_symbol"), b.get("price"), b.get("volume_24h"), b.get("market_cap"), b.get("circulating_supply")],
            })
            st.dataframe(table, use_container_width=True, height=240)

            k1, k2, k3 = st.columns(3)
            k1.metric("Volume Diff", f"{float(a.get('volume_24h', 0) - b.get('volume_24h', 0)):,.0f}")
            k2.metric("Supply Diff", f"{float(a.get('circulating_supply', 0) - b.get('circulating_supply', 0)):,.0f}")
            k3.metric("Market Cap Diff", f"{float(a.get('market_cap', 0) - b.get('market_cap', 0)):,.0f}")


with tabs[5]:
    st.subheader("6) Liquidity pie: Top 5 coins share + Others")
    st.caption("Slicer: $0–$50 or >$50 (based on price). Pie chart uses Volume(24h) as liquidity.")

    cat = st.radio("Price category", ["$0 - $50", ">$50"], horizontal=True, index=0)

    d = df.dropna(subset=["price", "volume_24h"]).copy()
    d["cat0_50"] = np.where(d["price"] <= 50, "$0 - $50", ">$50")
    d = d[d["cat0_50"] == cat].copy()
    d = d.sort_values("volume_24h", ascending=False)

    if d.empty:
        st.warning("No data for selected category.")
    else:
        top5 = d.head(5)[["coin_name", "volume_24h"]].copy()
        other_sum = float(d.iloc[5:]["volume_24h"].sum()) if d.shape[0] > 5 else 0.0

        pie = top5.copy()
        if other_sum > 0:
            pie = pd.concat([pie, pd.DataFrame([{"coin_name": "Others", "volume_24h": other_sum}])], ignore_index=True)

        fig = px.pie(pie, names="coin_name", values="volume_24h", title="Liquidity Share (Volume 24h)")
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=560, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(d.head(25)[["coin_name", "coin_symbol", "price", "volume_24h", "market_cap"]], use_container_width=True, height=420)


if show_history:
    st.divider()
    st.subheader("SQLite Recent Snapshots")
    st.caption("This shows any logged snapshots stored by your logger.py pipeline.")
    hist = load_recent()
    st.dataframe(hist.head(200), use_container_width=True, height=420)
