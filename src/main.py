import asyncio
import datetime
import logging
from apify import Actor
from src.data_engine import (
    fetch_crypto_fng,
    fetch_stablecoins_supply,
    fetch_market_assets_history,
    fetch_spy_put_call_ratio
)
from src.sentiment_engine import (
    classify_sentiment,
    calculate_stock_sentiment,
    calculate_crypto_sentiment,
    compute_benchmark_performance_matrix,
    compute_correlation_matrix,
    compute_stablecoin_flows
)

logger = logging.getLogger(__name__)

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        
        include_stocks = bool(actor_input.get("includeStockSentiment", True))
        include_crypto = bool(actor_input.get("includeCryptoSentiment", True))
        include_corr = bool(actor_input.get("includeCorrelationMatrix", True))
        include_stables = bool(actor_input.get("includeStablecoinSupply", True))
        include_benchmarks = bool(actor_input.get("includeBenchmarkPerformance", True))
        history_days = int(actor_input.get("historyDays", 30))
        
        Actor.log.info("🔮 Starting Cross-Asset Market Sentiment & Fear/Greed Intelligence Actor...")
        
        # 1. Fetch market assets history
        Actor.log.info("Fetching multi-asset historical price data from financial providers...")
        df_prices = fetch_market_assets_history()
        
        # 2. Fetch live SPY Put/Call volume ratio
        Actor.log.info("Scraping live SPY options Put/Call volume ratio...")
        pc_ratio = fetch_spy_put_call_ratio()
        
        # 3. Fetch Crypto Fear & Greed Index
        Actor.log.info(f"Fetching Crypto Fear & Greed Index history ({history_days} days)...")
        df_fng = fetch_crypto_fng(limit=history_days)
        
        # 4. Fetch Stablecoins Supply
        Actor.log.info("Fetching global circulating stablecoins supply data from DeFiLlama...")
        df_stablecoins = fetch_stablecoins_supply()
        
        # 5. Compute Sentiment Sub-Indicators
        stock_indicators, stock_val, stock_hist = calculate_stock_sentiment(df_prices, pc_ratio)
        crypto_indicators, crypto_val, crypto_hist = calculate_crypto_sentiment(df_prices, df_fng)
        
        stock_class, stock_color = classify_sentiment(stock_val)
        crypto_class, crypto_color = classify_sentiment(crypto_val)
        
        global_val = round((stock_val + crypto_val) / 2.0, 1)
        global_class, global_color = classify_sentiment(global_val)
        
        # 6. Benchmark Performance
        benchmarks = compute_benchmark_performance_matrix(df_prices) if include_benchmarks else {}
        
        # 7. Correlation Matrix
        correlations = compute_correlation_matrix(df_prices) if include_corr else {}
        
        # 8. Stablecoin Supply vs BTC Flows
        stablecoin_flows = compute_stablecoin_flows(df_stablecoins, df_prices) if include_stables else []
        
        # Latest Stablecoin supply in billions
        latest_stable_b = stablecoin_flows[-1]["stablecoinSupplyBillions"] if stablecoin_flows else 182.5
        
        # Build Master Record
        master_record = {
            "recordType": "CROSS_ASSET_SENTIMENT_DOSSIER",
            "globalSentimentScore": global_val,
            "globalClassification": global_class,
            "stockSentimentScore": stock_val,
            "stockClassification": stock_class,
            "cryptoSentimentScore": crypto_val,
            "cryptoClassification": crypto_class,
            "marketMomentumScore": stock_indicators["Market Momentum"],
            "vixScore": stock_indicators["Volatility VIX"],
            "safeHavenScore": stock_indicators["Safe Haven Demand"],
            "junkBondScore": stock_indicators["Junk Bond Demand"],
            "putCallRatioScore": stock_indicators["Put/Call Ratio"],
            "retailCryptoFngScore": crypto_indicators["Retail Fear & Greed"],
            "bitcoinMomentumScore": crypto_indicators["Bitcoin Momentum"],
            "ethBtcStrengthScore": crypto_indicators["ETH/BTC Strength"],
            "bitcoinVolatilityScore": crypto_indicators["Bitcoin Volatility"],
            "stablecoinSupplyBillions": latest_stable_b,
            "stockIndicatorsBreakdown": stock_indicators,
            "cryptoIndicatorsBreakdown": crypto_indicators,
            "stockSentimentHistory": stock_hist[-history_days:] if include_stocks else [],
            "cryptoSentimentHistory": crypto_hist[-history_days:] if include_crypto else [],
            "benchmarkPerformance": benchmarks,
            "macroCorrelationMatrix": correlations,
            "stablecoinFlows": stablecoin_flows[-history_days:] if include_stables else [],
            "calculatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # Push master record to dataset
        await Actor.push_data(master_record)
        
        # Push daily historical sentiment rows for easy table charting
        for row in stock_hist[-history_days:]:
            await Actor.push_data({
                "recordType": "STOCK_DAILY_SENTIMENT",
                "date": row["date"],
                "value": row["value"],
                "classification": row["classification"]
            })
            
        for row in crypto_hist[-history_days:]:
            await Actor.push_data({
                "recordType": "CRYPTO_DAILY_SENTIMENT",
                "date": row["date"],
                "value": row["value"],
                "classification": row["classification"]
            })
            
        # Store executive summary in default Key-Value store
        summary_payload = {
            "globalSentiment": {
                "score": global_val,
                "classification": global_class
            },
            "stockMarket": {
                "score": stock_val,
                "classification": stock_class,
                "indicators": stock_indicators
            },
            "cryptoMarket": {
                "score": crypto_val,
                "classification": crypto_class,
                "indicators": crypto_indicators
            },
            "stablecoinSupplyBillions": latest_stable_b,
            "benchmarkHighlights": benchmarks
        }
        await Actor.set_value("OUTPUT", summary_payload)
        
        Actor.log.info(f"✅ Market Sentiment Actor completed! Master dossier and {len(stock_hist[-history_days:]) + len(crypto_hist[-history_days:])} daily records pushed to Apify Dataset.")

if __name__ == "__main__":
    asyncio.run(main())
