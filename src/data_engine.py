import datetime
import json
import logging
import pandas as pd
import numpy as np
import requests
import yfinance as yf

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def fetch_crypto_fng(limit: int = 30) -> pd.DataFrame:
    """Fetch Crypto Fear & Greed Index history from Alternative.me."""
    url = f"https://api.alternative.me/fng/?limit={limit}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            df = pd.DataFrame(data)
            if not df.empty:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
                df.sort_values('timestamp', ascending=True, inplace=True)
                df.reset_index(drop=True, inplace=True)
                return df[['timestamp', 'value', 'value_classification']]
    except Exception as e:
        logger.warning(f"Failed to fetch Alternative.me crypto FNG: {e}")
        
    # Default fallback
    dates = pd.date_range(end=datetime.datetime.now(), periods=limit, freq='D')
    return pd.DataFrame({
        'timestamp': dates,
        'value': [52] * limit,
        'value_classification': ['Neutral'] * limit
    })

def fetch_stablecoins_supply() -> pd.DataFrame:
    """Fetch global circulating stablecoins total market cap from DeFiLlama."""
    url = "https://stablecoins.llama.fi/stablecoincharts/all"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df['date_parsed'] = pd.to_datetime(df['date'].astype(int), unit='s')
                df['supply'] = df['totalCirculatingUSD'].apply(lambda x: x.get('peggedUSD', 0) if isinstance(x, dict) else (x if isinstance(x, (int, float)) else 0))
                df.sort_values('date_parsed', ascending=True, inplace=True)
                df.reset_index(drop=True, inplace=True)
                return df[['date_parsed', 'supply']]
    except Exception as e:
        logger.warning(f"Failed to fetch DeFiLlama stablecoin supply: {e}")
        
    # Default fallback
    dates = pd.date_range(end=datetime.datetime.now(), periods=180, freq='D')
    return pd.DataFrame({
        'date_parsed': dates,
        'supply': [182500000000.0] * 180  # ~$182.5 Billion
    })

def fetch_market_assets_history() -> dict:
    """
    Fetch multi-asset historical prices for stock sentiment, crypto sentiment,
    macro correlation matrix, and benchmark returns.
    """
    assets = {
        # Sentiment Drivers
        "SPY": "SPY",
        "GLD": "GLD",
        "JNK": "JNK",
        "LQD": "LQD",
        "VIX": "^VIX",
        # Crypto
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "BNB": "BNB-USD",
        # Macro
        "S&P 500": "^GSPC",
        "Brent Crude": "BZ=F",
        "US Dollar Index": "UUP",
        "QQQ": "QQQ",
        "IWM": "IWM"
    }
    
    price_dict = {}
    for name, ticker in assets.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="300d")
            if hist is not None and not hist.empty:
                hist.index = pd.to_datetime(hist.index.date)
                price_dict[name] = hist['Close']
        except Exception as e:
            logger.warning(f"Could not fetch history for {name} ({ticker}): {e}")
            
    df_prices = pd.DataFrame(price_dict).ffill().dropna(how='all')
    return df_prices

def fetch_spy_put_call_ratio() -> float:
    """Fetch live options Put/Call volume ratio for SPY."""
    try:
        spy_obj = yf.Ticker("SPY")
        exp = spy_obj.options
        if exp:
            opt = spy_obj.option_chain(exp[0])
            c_v = opt.calls['volume'].sum()
            p_v = opt.puts['volume'].sum()
            if c_v > 0 and p_v > 0:
                ratio = float(p_v / c_v)
                return round(ratio, 3)
    except Exception as e:
        logger.warning(f"Could not fetch SPY options chain for Put/Call ratio: {e}")
    return 0.85
