# Cross-Asset Market Sentiment & Fear/Greed Intelligence 🔮📊

**Cross-Asset Market Sentiment Intelligence** is a quantitative sentiment analysis Actor on Apify. It extracts and models psychological indices, equity & cryptocurrency Fear & Greed gauges, option Put/Call volume ratios, 90-day Pearson cross-asset correlation matrices, multi-horizon benchmark performance matrices, and on-chain circulating stablecoin liquidity flows.

---

## 🌟 Key Features

1. **Stock Market Fear & Greed Index (0-100):**
   - **Market Momentum:** S&P 500 relative to 125-day moving average.
   - **Market Volatility (VIX):** VIX relative to 50-day moving average.
   - **Safe Haven Demand:** 20-day return spread between Equities (SPY) and Gold (GLD).
   - **Junk Bond Demand:** 20-day return spread between High-Yield Debt (JNK) and Investment-Grade Corporate Debt (LQD).
   - **Put/Call Ratio:** Real-time options chain put vs call volume ratio.

2. **Crypto Market Fear & Greed Index (0-100):**
   - **Retail Fear & Greed:** Alternative.me retail psychological index.
   - **Bitcoin Momentum:** BTC price relative to 125-day moving average.
   - **ETH/BTC Relative Strength:** Ratio relative to 50-day moving average.
   - **Bitcoin Volatility:** 20-day annualized rolling volatility.

3. **Global Cross-Asset Sentiment Composite:**
   - Weighted composite index ($0-100$) classifying overall market psychology into `Extreme Fear`, `Fear`, `Neutral`, `Greed`, or `Extreme Greed`.

4. **Macro-Crypto Pearson Correlation Matrix:**
   - 90-day rolling correlation coefficient matrix between Bitcoin, Ethereum, Solana, S&P 500, Gold, Crude Oil, and the US Dollar Index (UUP/DXY).

5. **Multi-Horizon Benchmark Performance Matrix:**
   - Real-time percentage returns across **1W, 1M, 3M, 6M, YTD, 1Y** for key equity (SPX, SPY, QQQ, IWM) and crypto (BTC, ETH, SOL, BNB) benchmarks.

6. **Circulating Stablecoin Supply & Liquidity Flows:**
   - Tracks total circulating stablecoin supply ($B) from DeFiLlama paired with Bitcoin price to identify leading liquidity inflows into risk assets.

---

## 📥 Input Configuration

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `includeStockSentiment` | `boolean` | `true` | Calculate equity sentiment index and underlying 5 drivers. |
| `includeCryptoSentiment` | `boolean` | `true` | Calculate crypto sentiment index and underlying 4 drivers. |
| `includeCorrelationMatrix` | `boolean` | `true` | Compute 90-day Pearson correlation matrix across assets. |
| `includeStablecoinSupply` | `boolean` | `true` | Track circulating stablecoin market cap vs Bitcoin price. |
| `includeBenchmarkPerformance` | `boolean` | `true` | Compute multi-horizon performance comparison table. |
| `historyDays` | `integer` | `30` | Number of daily historical sentiment records to output (7–365). |

---

## 📤 Output Schema

```json
{
  "recordType": "CROSS_ASSET_SENTIMENT_DOSSIER",
  "globalSentimentScore": 62.4,
  "globalClassification": "Greed 🤑",
  "stockSentimentScore": 65.8,
  "stockClassification": "Greed 🤑",
  "cryptoSentimentScore": 59.0,
  "cryptoClassification": "Greed 🤑",
  "marketMomentumScore": 72.4,
  "vixScore": 68.1,
  "safeHavenScore": 60.5,
  "junkBondScore": 62.2,
  "putCallRatioScore": 65.0,
  "retailCryptoFngScore": 58.0,
  "bitcoinMomentumScore": 64.2,
  "ethBtcStrengthScore": 52.0,
  "bitcoinVolatilityScore": 61.8,
  "stablecoinSupplyBillions": 182.54,
  "stockIndicatorsBreakdown": { ... },
  "cryptoIndicatorsBreakdown": { ... },
  "benchmarkPerformance": { ... },
  "macroCorrelationMatrix": { ... }
}
```

---

## 🚀 Local Run

```bash
uv run --with apify --with pandas --with numpy --with yfinance --with requests --with pytz --with python-dateutil python -m src.main
```
