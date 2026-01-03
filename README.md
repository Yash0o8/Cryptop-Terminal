# 💹 Crypto Trading Dashboard 

A **Streamlit-based crypto dashboard** that feels like a mini trading terminal — built for investors who want **maximum profit insights with minimum effort**.

It fetches **Top-200 live crypto coins** from **CoinGecko** and delivers **6 investor-focused modules** with charts, KPIs, slicers, comparisons, and liquidity visuals.

---

## 🚀 What This Project Does (in real life)

Imagine an investor says:

> “I don’t have a big budget, but I want coins that look stable and profitable.  
> Also, show me which coins are moving, which ones are liquid, and compare 2 coins for me.”

This dashboard answers that with:
✅ **price-range slicers**  
✅ **least-downfall picks**  
✅ **reconstructed previous prices** (1h/24h/7d)  
✅ **top gainers analysis**  
✅ **liquidity charts**  
✅ **coin comparison**  
✅ **working-hours security logic**

---

## ✨ Key Features

- 🔄 **Live Data Fetching** (Top-200 coins)
- 🌐 **Two data sources**: CoinGecko + CoinMarketCap scraping
- 🎛️ **Slicers + KPIs** (interactive filtering)
- 📊 **Charts & Tables** (Plotly + Streamlit Dataframes)
- 💾 **Export to Excel** (for investor reports)
- 🗃️ **Optional SQLite snapshot viewer** (for logged history)

---

## 🧠 The 6 Investor Modules 

### ✅ 1) Budget KPIs (Price Range Slicer)
**Goal:** Investor has low budget → wants the coin with the **least average downfall**  
(Avg of |1h|, |24h|, |7d|)

**Slicer ranges:**
- `$0 - $0.05`
- `$0.05 - $0.5`
- `$0.5 - $5`
- `$5 - $50`
- `>$50`

**Output:**
- Coin Name
- Coin Symbol
- Current Price
- Avg Downfall %
- Total coins considered in selection

✅ *Real-life example:*  
If an investor selects `$0.5 - $5`, they get the coin that has been the **most stable** among cheap coins.

---

### ✅ 2) $0–$5 Top 10 (Previous Prices Chart)
**Goal:** Find best picks in the **0–5 USD** price range.  
Chart shows **reconstructed “7 days before” and “24 hours before” prices**.

**Logic used:**
- 7d % assumed **increase**
- 24h % assumed **decrease**
- 1h % used for ranking

**Output:**
- Bar chart: 7d-before vs 24h-before vs current
- Table of the top 10 coins in this range

✅ *Real-life example:*  
Investor asks: “Show me cheap coins that were stronger a week ago and how they moved.”

---

### ✅ 3) Top 10 Price Increase (vs previous 1h)
**Goal:** Show coins with the **biggest actual price increase** compared to the previous hour.

**Slicer:**
- `< $10`
- `>= $10`

**Output:**
- chart comparing current price vs 1h-before price
- table with symbol + price change

✅ *Real-life example:*  
Investor wants “fast movers” for short-term trading.

---

### ✅ 4) Prefix Filter + Working Hours Security
**Goal:** Investor only wants coins whose names start with:
- vowels (`A, E, I, O, U`)
- or `B`, `C`, `D`

**Security rule:**
- Chart visible only between **9 AM and 5 PM**
- Otherwise displays:
  > “Please open in working hours (9 am to 5 pm)”

**Output:**
- Top 10 coins by **Volume(24h)** (liquidity)

✅ *Real-life example:*  
Investor thinks vowels/BCD coins are “lucky picks” and only wants to view them during office hours.

---

### ✅ 5) Compare Two Coins (with validation + KPI diff)
**Goal:** Compare 2 coins on key fundamentals.

**Inputs:**
- CoinName1
- CoinName2

**Validation rules:**
- length must be **3–10 characters**
- **no numbers allowed**

**Outputs:**
- Symbol, Price, Volume, Market Cap, Circulating Supply (for both coins)
- KPIs showing differences:
  - Volume difference
  - Supply difference
  - Market Cap difference

✅ *Real-life example:*  
Investor asks: “Should I choose Bitcoin or Ethereum? Show the difference.”

---

### ✅ 6) Liquidity Pie Chart (Top 5 + Others)
**Goal:** Show liquidity distribution using Volume(24h).  
Investor wants share of top coins vs everyone else.

**Slicer categories:**
- `$0 - $50`
- `>$50`

**Output:**
- Pie chart: Top 5 coins + “Others”
- Table of top 25 coins in selection

✅ *Real-life example:*  
Investor wants coins where “big money is flowing” (high trading volume).

---

## 🔁 Data Pipeline 

1. **Fetch data** (Top-200 coins) from selected source
2. **Standardize columns** (name, symbol, price, % changes, volume, market cap)
3. **Compute derived fields**
   - price ranges
   - reconstructed previous prices (1h/24h/7d)
   - avg downfall %
4. **Render modules**
   - KPI cards
   - charts
   - interactive tables
   - slicers

---

## 🧰 Tech Stack

- **Python**
- **Streamlit**
- **Pandas / NumPy**
- **Plotly Express**
- **Requests + HTML parsing** (for CMC scraper)
- **SQLite** (optional snapshots)
- **Excel export** (openpyxl / xlsxwriter)
-To view the database:
Use DB Browser for SQLite
Open crypto.db
---

## ▶️ How to Run Locally

### 1) Clone the repository
https://github.com/aryman-singh-07/Crypto-Dashboard.git
cd Crypto-Dashboard
pip install -r requirements.txt
# 1) Start the snapshot logger (runs every 15 minutes)
python logger.py --source coingecko --per_page 200 --every_minutes 15
# 2) In a new terminal, run the Streamlit app
streamlit run app.py


📁 Project Structure
Crypto-Dashboard/
│
├── app.py                      # Streamlit app (Blue-Black Trading UI)
├── requirements.txt            # Dependencies
│
├── src/
│   ├── data.py                 # Live fetching + config (CoinGecko/CMC)
│   ├── analytics.py            # Derived columns + calculations
│   ├── storage.py              # SQLite snapshot reads
│
├── exports/                    # Auto-generated Excel exports
├── data/                       # (optional) cached files / logs
└── README.md

📦 Requirements
Python 3.9+
streamlit
pandas
numpy
plotly
openpyxl / xlsxwriter

👤 Author

Yash Pandey and Aryman Singh

📧 Email: yashpandeypandey11@gmail.com

