import sys, json, math
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf

ALIASES = {
    "APPLE":"AAPL", "MICROSOFT":"MSFT", "NVIDIA":"NVDA", "TESLA":"TSLA",
    "GOOGLE":"GOOGL", "ALPHABET":"GOOGL", "AMAZON":"AMZN", "META":"META", "NETFLIX":"NFLX",
    "BTC":"BTC-USD", "BITCOIN":"BTC-USD", "ETH":"ETH-USD", "ETHEREUM":"ETH-USD", "SOL":"SOL-USD", "SOLANA":"SOL-USD"
}

RANGES = {
    "1D": {"period":"1d", "interval":"5m", "label":"1 day intraday data"},
    "5D": {"period":"5d", "interval":"15m", "label":"5 days intraday data"},
    "1W": {"period":"7d", "interval":"30m", "label":"1 week intraday data"},
    "1M": {"period":"1mo", "interval":"1d", "label":"1 month daily data"},
}

def sf(v):
    try:
        if v is None: return None
        x = float(v)
        return None if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return None

def clean_symbol(v):
    s = (v or "AAPL").strip().upper()
    return ALIASES.get(s, s)

def clean_range(v):
    r = (v or "1D").strip().upper()
    return r if r in RANGES else "1D"

def records(df):
    out = []
    if df is None or df.empty: return out
    df = df.reset_index()
    date_col = "Datetime" if "Datetime" in df.columns else "Date"
    for _, row in df.iterrows():
        close = sf(row.get("Close"))
        if close is None: continue
        out.append({
            "time": int(pd.to_datetime(row[date_col]).timestamp() * 1000),
            "open": sf(row.get("Open")),
            "high": sf(row.get("High")),
            "low": sf(row.get("Low")),
            "close": close,
            "volume": sf(row.get("Volume")),
        })
    return out

def sma(vals, n):
    return sf(pd.Series(vals).rolling(n).mean().iloc[-1]) if len(vals) >= n else None

def ema(vals, n):
    return pd.Series(vals).ewm(span=n, adjust=False).mean()

def rsi(vals, n=14):
    if len(vals) <= n: return None
    s = pd.Series(vals)
    d = s.diff()
    gain = d.clip(lower=0)
    loss = -d.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    rs = avg_gain / avg_loss
    return sf((100 - (100 / (1 + rs))).iloc[-1])

def macd(vals):
    e12 = ema(vals, 12)
    e26 = ema(vals, 26)
    line = e12 - e26
    signal = line.ewm(span=9, adjust=False).mean()
    hist = line - signal
    return {"macd": sf(line.iloc[-1]), "signal": sf(signal.iloc[-1]), "hist": sf(hist.iloc[-1])}

def bollinger(vals, n=20):
    if len(vals) < n: return None
    s = pd.Series(vals)
    mid = sf(s.rolling(n).mean().iloc[-1])
    sd = sf(s.rolling(n).std().iloc[-1])
    if mid is None or sd is None: return None
    return {"mid": mid, "upper": mid + 2 * sd, "lower": mid - 2 * sd}

def limited_analysis(closes):
    return {
        "score": 50, "rsi14": None, "sma20": None, "sma50": None, "sma200": None,
        "macd": {"macd": None, "signal": None, "hist": None}, "bollinger": None,
        "support": min(closes) if closes else None, "resistance": max(closes) if closes else None,
        "signals": [{"name":"Data", "value":"Limited", "status":"neutral", "text":"Use 1M for stronger technical analysis"}],
        "strongest": {"name":"Data", "text":"Limited data"},
        "weakest": {"name":"Data", "text":"Limited data"},
        "summary": "This range has limited candles. Use 1M for stronger technical analysis.",
        "disclaimer": "This AI technical analysis is not investment advice. It is for informational purposes only."
    }

def analyze(candles):
    closes = [c["close"] for c in candles if c.get("close") is not None]
    volumes = [c.get("volume") or 0 for c in candles]
    if len(closes) < 30: return limited_analysis(closes)
    last = closes[-1]
    rv = rsi(closes)
    s20, s50, s200 = sma(closes,20), sma(closes,50), sma(closes,200)
    m = macd(closes)
    b = bollinger(closes)
    recent = candles[-60:]
    support = min([(c.get("low") or c.get("close")) for c in recent])
    resistance = max([(c.get("high") or c.get("close")) for c in recent])
    avg_vol = np.mean(volumes[-20:]) if volumes[-20:] else 0
    vol_ratio = (volumes[-1] / avg_vol) if avg_vol else 1
    signals = []
    if rv is not None:
        if rv > 70: st, txt = "weak", "Overbought zone"
        elif rv < 30: st, txt = "strong", "Oversold zone"
        elif rv > 55: st, txt = "strong", "Strong momentum"
        elif rv < 45: st, txt = "weak", "Weak momentum"
        else: st, txt = "neutral", "Neutral"
        signals.append({"name":"RSI 14", "value":round(rv,1), "status":st, "text":txt})
    if s20 and s50:
        if last > s20 > s50: st, val = "strong", "Strong"
        elif last < s20 < s50: st, val = "weak", "Weak"
        else: st, val = "neutral", "Mixed"
        signals.append({"name":"Trend", "value":val, "status":st, "text":"SMA20 / SMA50"})
    hist = m.get("hist") or 0
    signals.append({"name":"MACD", "value":round(hist,3), "status":"strong" if hist > 0 else "weak", "text":"Positive momentum" if hist > 0 else "Negative momentum"})
    if b:
        if last > b["upper"]: st, val = "weak", "Upper band"
        elif last < b["lower"]: st, val = "strong", "Lower band"
        else: st, val = "neutral", "Inside band"
        signals.append({"name":"Bollinger", "value":val, "status":st, "text":"Volatility zone"})
    signals.append({"name":"Volume", "value":f"{vol_ratio:.2f}x", "status":"strong" if vol_ratio > 1.5 else "weak" if vol_ratio < 0.7 else "neutral", "text":"Compared to 20-period average"})
    score = 50
    for item in signals:
        score += 10 if item["status"] == "strong" else -10 if item["status"] == "weak" else 0
    score = max(0, min(100, score))
    strongest = next((s for s in signals if s["status"] == "strong"), signals[0])
    weakest = next((s for s in signals if s["status"] == "weak"), signals[-1])
    summary = "The technical outlook is strong." if score >= 70 else "The technical outlook is weak." if score <= 35 else "Technical signals are mixed."
    return {"score":score, "rsi14":rv, "sma20":s20, "sma50":s50, "sma200":s200, "macd":m, "bollinger":b, "support":support, "resistance":resistance, "signals":signals, "strongest":strongest, "weakest":weakest, "summary":summary, "disclaimer":"This AI technical analysis is not investment advice. It is for informational purposes only."}

def market_state(raw):
    return "OPEN" if raw == "REGULAR" else "PRE" if raw == "PRE" else "POST" if raw == "POST" else "CLOSED"

def main():
    symbol = clean_symbol(sys.argv[1] if len(sys.argv) > 1 else "AAPL")
    chart_range = clean_range(sys.argv[2] if len(sys.argv) > 2 else "1D")
    selected = RANGES[chart_range]
    ticker = yf.Ticker(symbol)
    hist_df = ticker.history(period=selected["period"], interval=selected["interval"], auto_adjust=False, prepost=True)
    if hist_df is None or hist_df.empty:
        hist_df = ticker.history(period="1mo", interval="1d", auto_adjust=False, prepost=True)
    if hist_df is None or hist_df.empty:
        raise Exception("Data source did not respond.")
    candles = records(hist_df)
    if len(candles) < 2:
        raise Exception("Not enough candle data.")
    try: info = ticker.info or {}
    except Exception: info = {}
    try: fast = ticker.fast_info or {}
    except Exception: fast = {}
    last, prev = candles[-1], candles[-2]
    price = sf(info.get("regularMarketPrice")) or sf(info.get("currentPrice")) or sf(fast.get("last_price")) or last["close"]
    prev_close = sf(info.get("previousClose")) or sf(fast.get("previous_close")) or prev["close"]
    after_price = sf(info.get("postMarketPrice")) or sf(info.get("preMarketPrice"))
    change = price - prev_close
    change_percent = (change / prev_close * 100) if prev_close else 0
    after_change = None
    after_change_percent = None
    if after_price is not None:
        after_change = after_price - price
        after_change_percent = (after_change / price * 100) if price else 0
    name = info.get("shortName") or info.get("longName") or symbol
    currency = info.get("currency") or "USD"
    closes = [c["close"] for c in candles]
    quote = {"symbol":symbol, "name":name, "price":price, "change":change, "changePercent":change_percent, "previousClose":prev_close, "afterPrice":after_price, "afterChange":after_change, "afterChangePercent":after_change_percent, "open":last.get("open"), "high":last.get("high"), "low":last.get("low"), "volume":sf(info.get("volume")) or last.get("volume"), "currency":currency, "marketState":market_state(info.get("marketState") or "YFINANCE"), "source":"yfinance / Yahoo Finance", "lastUpdate":datetime.now().strftime("%d.%m.%Y %H:%M"), "warning":"yfinance is not an official API. Availability may change."}
    analysis = analyze(candles)
    details = {"symbol":symbol, "name":name, "sector":info.get("sector") or "Unknown", "assetType":info.get("quoteType") or "Asset", "marketCap":sf(info.get("marketCap")), "volume":quote["volume"], "high52":sf(info.get("fiftyTwoWeekHigh")) or max(closes), "low52":sf(info.get("fiftyTwoWeekLow")) or min(closes), "source":quote["source"], "website":info.get("website") or ""}
    news = [{"title":f"{name} technical outlook and price action are being monitored", "source":"CHARTIX News", "time":"Current", "url":"#"}, {"title":f"{symbol} analyzed by RSI, MACD, support and resistance", "source":"Market Desk", "time":"Current", "url":"#"}]
    print(json.dumps({"quote":quote, "history":{"symbol":symbol, "range":chart_range, "rangeLabel":selected["label"], "candles":candles, "source":"yfinance"}, "analysis":analysis, "details":details, "news":news}, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"error":"Data source did not respond."}, ensure_ascii=False))
        sys.exit(1)
