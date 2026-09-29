import datetime
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def classify_sentiment(val: float) -> tuple:
    """Classify sentiment score into 5 distinct regimes."""
    if val < 25.0:
        return "Extreme Fear 😨", "#ef4444"
    elif val < 45.0:
        return "Fear 😟", "#f97316"
    elif val < 55.0:
        return "Neutral ⚖️", "#eab308"
    elif val < 75.0:
        return "Greed 🤑", "#22c55e"
    else:
        return "Extreme Greed 🚀", "#00FF87"

def calculate_stock_sentiment(df_prices: pd.DataFrame, put_call_ratio_val: float = 0.85) -> tuple:
    """
    Calculate 5 sub-indicators and overall Stock Market Sentiment index (0-100).
    """
    spy = df_prices.get("SPY", pd.Series())
    gld = df_prices.get("GLD", pd.Series())
    jnk = df_prices.get("JNK", pd.Series())
    lqd = df_prices.get("LQD", pd.Series())
    vix = df_prices.get("VIX", pd.Series())
    
    if spy.empty or len(spy) < 130:
        return {
            "Market Momentum": 50.0,
            "Volatility VIX": 50.0,
            "Safe Haven Demand": 50.0,
            "Junk Bond Demand": 50.0,
            "Put/Call Ratio": 50.0
        }, 50.0, []
        
    # 1. Market Momentum (SPY vs 125-day SMA)
    spy_sma125 = spy.rolling(125).mean()
    mom_ratio = spy / spy_sma125
    mom_score = 10.0 + (mom_ratio - 0.9) / (1.1 - 0.9) * 80.0
    mom_score = mom_score.clip(5.0, 95.0)
    
    # 2. Volatility VIX (VIX vs 50-day SMA)
    if not vix.empty:
        vix_sma50 = vix.rolling(50).mean()
        vix_ratio = vix / vix_sma50
        vix_score = 90.0 - (vix_ratio - 0.7) / (1.5 - 0.7) * 80.0
        vix_score = vix_score.clip(5.0, 95.0)
    else:
        vix_score = pd.Series(50.0, index=spy.index)
        
    # 3. Safe Haven Demand (SPY 20d return - GLD 20d return)
    if not gld.empty:
        spy_ret = spy.pct_change(20)
        gld_ret = gld.pct_change(20)
        diff_haven = spy_ret - gld_ret
        haven_score = 50.0 + (diff_haven / 0.05) * 40.0
        haven_score = haven_score.clip(5.0, 95.0)
    else:
        haven_score = pd.Series(50.0, index=spy.index)
        
    # 4. Junk Bond Demand (JNK 20d return - LQD 20d return)
    if not jnk.empty and not lqd.empty:
        jnk_ret = jnk.pct_change(20)
        lqd_ret = lqd.pct_change(20)
        diff_junk = jnk_ret - lqd_ret
        junk_score = 50.0 + (diff_junk / 0.02) * 40.0
        junk_score = junk_score.clip(5.0, 95.0)
    else:
        junk_score = pd.Series(50.0, index=spy.index)
        
    # 5. Put/Call Ratio
    pc_score = 90.0 - (put_call_ratio_val - 0.5) / (1.2 - 0.5) * 80.0
    pc_score = max(5.0, min(95.0, pc_score))
    
    # Composite Stock Series
    stock_sent_series = (mom_score + vix_score + haven_score + junk_score) / 4.0
    
    df_hist = pd.DataFrame({
        "Market Momentum": mom_score,
        "Volatility VIX": vix_score,
        "Safe Haven Demand": haven_score,
        "Junk Bond Demand": junk_score,
        "Put/Call Ratio": pc_score,
        "Stock_Sentiment": stock_sent_series
    }, index=spy.index).dropna(subset=["Stock_Sentiment"])
    
    latest = df_hist.iloc[-1]
    indicators = {
        "Market Momentum": round(float(latest["Market Momentum"]), 1),
        "Volatility VIX": round(float(latest["Volatility VIX"]), 1),
        "Safe Haven Demand": round(float(latest["Safe Haven Demand"]), 1),
        "Junk Bond Demand": round(float(latest["Junk Bond Demand"]), 1),
        "Put/Call Ratio": round(float(pc_score), 1)
    }
    
    stock_val = round(float(latest["Stock_Sentiment"]), 1)
    
    # Historical list
    hist_list = []
    for dt, row in df_hist.tail(60).iterrows():
        hist_list.append({
            "date": dt.strftime('%Y-%m-%d'),
            "value": round(float(row['Stock_Sentiment']), 1),
            "classification": classify_sentiment(float(row['Stock_Sentiment']))[0]
        })
        
    return indicators, stock_val, hist_list

def calculate_crypto_sentiment(df_prices: pd.DataFrame, df_fng: pd.DataFrame) -> tuple:
    """
    Calculate 4 sub-indicators and overall Crypto Market Sentiment index (0-100).
    """
    btc = df_prices.get("Bitcoin", pd.Series())
    eth = df_prices.get("Ethereum", pd.Series())
    
    retail_fng = 50.0
    if not df_fng.empty:
        retail_fng = float(df_fng.iloc[-1]['value'])
        
    # 1. Bitcoin Momentum (BTC vs 125-day SMA)
    btc_mom = 50.0
    if not btc.empty and len(btc) >= 125:
        btc_close = btc.iloc[-1]
        btc_sma125 = btc.rolling(125).mean().iloc[-1]
        if pd.notna(btc_sma125) and btc_sma125 > 0:
            ratio = btc_close / btc_sma125
            score = 10.0 + (ratio - 0.8) / (1.2 - 0.8) * 80.0
            btc_mom = max(5.0, min(95.0, score))
            
    # 2. ETH/BTC Relative Strength
    eth_btc_strength = 50.0
    if not btc.empty and not eth.empty and len(btc) >= 50 and len(eth) >= 50:
        ratio_series = eth / btc
        ratio_now = ratio_series.iloc[-1]
        ratio_sma50 = ratio_series.rolling(50).mean().iloc[-1]
        if pd.notna(ratio_sma50) and ratio_sma50 > 0:
            rel = ratio_now / ratio_sma50
            score = 50.0 + (rel - 1.0) / 0.1 * 40.0
            eth_btc_strength = max(5.0, min(95.0, score))
            
    # 3. Bitcoin Volatility
    btc_vol_score = 50.0
    if not btc.empty and len(btc) >= 20:
        btc_ret = btc.pct_change()
        btc_vol_ann = btc_ret.tail(20).std() * np.sqrt(365) * 100.0
        btc_vol_score = max(5.0, min(95.0, 80.0 - (btc_vol_ann - 30.0) / (80.0 - 30.0) * 60.0))
        
    crypto_indicators = {
        "Retail Fear & Greed": round(float(retail_fng), 1),
        "Bitcoin Momentum": round(float(btc_mom), 1),
        "ETH/BTC Strength": round(float(eth_btc_strength), 1),
        "Bitcoin Volatility": round(float(btc_vol_score), 1)
    }
    
    crypto_val = round(sum(crypto_indicators.values()) / len(crypto_indicators), 1)
    
    # Timeseries from df_fng
    crypto_hist_list = []
    if not df_fng.empty:
        for _, row in df_fng.iterrows():
            crypto_hist_list.append({
                "date": row['timestamp'].strftime('%Y-%m-%d'),
                "value": int(row['value']),
                "classification": row.get('value_classification', 'Neutral')
            })
            
    return crypto_indicators, crypto_val, crypto_hist_list

def compute_benchmark_performance_matrix(df_prices: pd.DataFrame) -> dict:
    """Calculate multi-horizon returns (1W, 1M, 3M, 6M, YTD, 1Y)."""
    benchmarks = {
        "stocks": {"S&P 500": "S&P 500", "SPY": "SPY", "QQQ": "QQQ", "IWM (Russell 2000)": "IWM"},
        "crypto": {"Bitcoin (BTC)": "Bitcoin", "Ethereum (ETH)": "Ethereum", "Solana (SOL)": "Solana", "BNB": "BNB"}
    }
    
    output = {"stocks": [], "crypto": []}
    
    for category, items in benchmarks.items():
        for label, col_name in items.items():
            if col_name not in df_prices.columns:
                continue
            series = df_prices[col_name].dropna()
            if series.empty:
                continue
                
            curr_p = series.iloc[-1]
            last_date = series.index[-1]
            
            def _get_past_price(days_back):
                target_dt = last_date - datetime.timedelta(days=days_back)
                sub = series[series.index <= target_dt]
                return sub.iloc[-1] if not sub.empty else series.iloc[0]
                
            # YTD
            ytd_dt = pd.to_datetime(f"{last_date.year - 1}-12-31")
            sub_ytd = series[series.index <= ytd_dt]
            p_ytd = sub_ytd.iloc[-1] if not sub_ytd.empty else series.iloc[0]
            
            p_1w = _get_past_price(7)
            p_1m = _get_past_price(30)
            p_3m = _get_past_price(90)
            p_6m = _get_past_price(180)
            p_1y = _get_past_price(365)
            
            output[category].append({
                "asset": label,
                "currentPrice": round(float(curr_p), 2),
                "return1W": round(float((curr_p - p_1w) / p_1w * 100.0), 2),
                "return1M": round(float((curr_p - p_1m) / p_1m * 100.0), 2),
                "return3M": round(float((curr_p - p_3m) / p_3m * 100.0), 2),
                "return6M": round(float((curr_p - p_6m) / p_6m * 100.0), 2),
                "returnYTD": round(float((curr_p - p_ytd) / p_ytd * 100.0), 2),
                "return1Y": round(float((curr_p - p_1y) / p_1y * 100.0), 2)
            })
            
    return output

def compute_correlation_matrix(df_prices: pd.DataFrame) -> dict:
    """Compute 90-day Pearson correlation matrix across crypto and traditional macro assets."""
    target_cols = ["Bitcoin", "Ethereum", "Solana", "S&P 500", "GLD", "Brent Crude", "US Dollar Index"]
    avail_cols = [c for c in target_cols if c in df_prices.columns]
    
    if len(avail_cols) < 2:
        return {"matrix": {}, "assets": []}
        
    df_sub = df_prices[avail_cols].tail(90).pct_change().dropna()
    corr = df_sub.corr()
    
    corr_dict = {}
    for r in corr.index:
        corr_dict[r] = {c: round(float(corr.loc[r, c]), 3) for c in corr.columns}
        
    return {
        "matrix": corr_dict,
        "assets": avail_cols,
        "lookbackDays": len(df_sub)
    }

def compute_stablecoin_flows(df_stablecoins: pd.DataFrame, df_prices: pd.DataFrame) -> list:
    """Pair circulating stablecoin market cap with Bitcoin price."""
    if df_stablecoins.empty or "Bitcoin" not in df_prices.columns:
        return []
        
    btc = df_prices["Bitcoin"].dropna()
    df_stable = df_stablecoins.tail(180).copy()
    
    flow_list = []
    for _, row in df_stable.iterrows():
        dt = row['date_parsed']
        supply_b = round(float(row['supply']) / 1e9, 2)
        
        # Match BTC price
        sub_btc = btc[btc.index <= dt]
        btc_price = round(float(sub_btc.iloc[-1]), 2) if not sub_btc.empty else round(float(btc.iloc[0]), 2)
        
        flow_list.append({
            "date": dt.strftime('%Y-%m-%d'),
            "stablecoinSupplyBillions": supply_b,
            "bitcoinPrice": btc_price
        })
        
    return flow_list
