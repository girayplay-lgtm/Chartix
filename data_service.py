import sys
import json
import math
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf


ALIASES = {
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "NVIDIA": "NVDA",
    "TESLA": "TSLA",
    "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL",
    "AMAZON": "AMZN",
    "META": "META",
    "NETFLIX": "NFLX",

    "BTC": "BTC-USD",
    "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD",
    "ETHEREUM": "ETH-USD",
    "SOL": "SOL-USD",
    "SOLANA": "SOL-USD",
}

RANGES = {
    "1D": {
        "period": "1d",
        "interval": "5m",
        "label": "1 day intraday data"
    },
    "5D": {
        "period": "5d",
        "interval": "15m",
        "label": "5 days intraday data"
    },
    "1W": {
        "period": "7d",
        "interval": "30m",
        "label": "1 week intraday data"
    },
    "1M": {
        "period": "1mo",
        "interval": "1d",
        "label": "1 month daily data"
    }
}


def safe_float(value):
    try:
        if value is None:
            return None

        x = float(value)

        if math.isnan(x) or math.isinf(x):
            return None

        return x
    except Exception:
        return None


def clean_symbol(value):
    symbol = str(value or "AAPL").strip().upper()
    return ALIASES.get(symbol, symbol)


def clean_range(value):
    chart_range = str(value or "1D").strip().upper()
    return chart_range if chart_range in RANGES else "1D"


def dataframe_to_candles(df):
    candles = []

    if df is None or df.empty:
        return candles

    df = df.reset_index()

    date_col = "Datetime" if "Datetime" in df.columns else "Date"

    for _, row in df.iterrows():
        close = safe_float(row.get("Close"))

        if close is None:
            continue

        timestamp = pd.to_datetime(row[date_col]).timestamp()

        candles.append({
            "time": int(timestamp * 1000),
            "open": safe_float(row.get("Open")),
            "high": safe_float(row.get("High")),
            "low": safe_float(row.get("Low")),
            "close": close,
            "volume": safe_float(row.get("Volume")),
        })

    return candles


def sma(values, length):
    if len(values) < length:
        return None

    return safe_float(
        pd.Series(values).rolling(length).mean().iloc[-1]
    )


def ema(values, length):
    return pd.Series(values).ewm(span=length, adjust=False).mean()


def rsi(values, length=14):
    if len(values) <= length:
        return None

    series = pd.Series(values)
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / length,
        min_periods=length,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / length,
        min_periods=length,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss
    value = 100 - (100 / (1 + rs))

    return safe_float(value.iloc[-1])


def macd(values):
    if len(values) < 26:
        return {
            "macd": None,
            "signal": None,
            "hist": None
        }

    e12 = ema(values, 12)
    e26 = ema(values, 26)

    line = e12 - e26
    signal = line.ewm(span=9, adjust=False).mean()
    hist = line - signal

    return {
        "macd": safe_float(line.iloc[-1]),
        "signal": safe_float(signal.iloc[-1]),
        "hist": safe_float(hist.iloc[-1])
    }


def bollinger(values, length=20):
    if len(values) < length:
        return None

    series = pd.Series(values)

    mid = safe_float(series.rolling(length).mean().iloc[-1])
    std = safe_float(series.rolling(length).std().iloc[-1])

    if mid is None or std is None:
        return None

    return {
        "mid": mid,
        "upper": mid + 2 * std,
        "lower": mid - 2 * std
    }


def limited_analysis(closes):
    return {
        "score": 50,
        "rsi14": None,
        "sma20": None,
        "sma50": None,
        "sma200": None,
        "macd": {
            "macd": None,
            "signal": None,
            "hist": None
        },
        "bollinger": None,
        "support": min(closes) if closes else None,
        "resistance": max(closes) if closes else None,
        "signals": [
            {
                "name": "Data",
                "value": "Limited",
                "status": "neutral",
                "text": "Use 1M for stronger technical analysis"
            }
        ],
        "strongest": {
            "name": "Data",
            "text": "Limited data"
        },
        "weakest": {
            "name": "Data",
            "text": "Limited data"
        },
        "summary": "This range has limited candles. Use 1M for stronger technical analysis.",
        "disclaimer": "This AI technical analysis is not investment advice. It is for informational purposes only."
    }


def analyze(candles):
    closes = [
        c["close"]
        for c in candles
        if c.get("close") is not None
    ]

    volumes = [
        c.get("volume") or 0
        for c in candles
    ]

    if len(closes) < 30:
        return limited_analysis(closes)

    last = closes[-1]

    rsi14 = rsi(closes, 14)
    sma20 = sma(closes, 20)
    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    macd_data = macd(closes)
    bollinger_data = bollinger(closes)

    recent = candles[-60:]

    support = min([
        c.get("low") or c.get("close")
        for c in recent
    ])

    resistance = max([
        c.get("high") or c.get("close")
        for c in recent
    ])

    avg_vol = np.mean(volumes[-20:]) if volumes[-20:] else 0
    vol_ratio = (volumes[-1] / avg_vol) if avg_vol else 1

    signals = []

    if rsi14 is not None:
        if rsi14 > 70:
            status = "weak"
            text = "Overbought zone"
        elif rsi14 < 30:
            status = "strong"
            text = "Oversold zone"
        elif rsi14 > 55:
            status = "strong"
            text = "Strong momentum"
        elif rsi14 < 45:
            status = "weak"
            text = "Weak momentum"
        else:
            status = "neutral"
            text = "Neutral"

        signals.append({
            "name": "RSI 14",
            "value": round(rsi14, 1),
            "status": status,
            "text": text
        })

    if sma20 and sma50:
        if last > sma20 > sma50:
            status = "strong"
            value = "Strong"
        elif last < sma20 < sma50:
            status = "weak"
            value = "Weak"
        else:
            status = "neutral"
            value = "Mixed"

        signals.append({
            "name": "Trend",
            "value": value,
            "status": status,
            "text": "SMA20 / SMA50"
        })

    hist = macd_data.get("hist") or 0

    signals.append({
        "name": "MACD",
        "value": round(hist, 3),
        "status": "strong" if hist > 0 else "weak",
        "text": "Positive momentum" if hist > 0 else "Negative momentum"
    })

    if bollinger_data:
        if last > bollinger_data["upper"]:
            status = "weak"
            value = "Upper band"
        elif last < bollinger_data["lower"]:
            status = "strong"
            value = "Lower band"
        else:
            status = "neutral"
            value = "Inside band"

        signals.append({
            "name": "Bollinger",
            "value": value,
            "status": status,
            "text": "Volatility zone"
        })

    signals.append({
        "name": "Volume",
        "value": f"{vol_ratio:.2f}x",
        "status": "strong" if vol_ratio > 1.5 else "weak" if vol_ratio < 0.7 else "neutral",
        "text": "Compared to 20-period average"
    })

    score = 50

    for item in signals:
        if item["status"] == "strong":
            score += 10
        elif item["status"] == "weak":
            score -= 10

    score = max(0, min(100, score))

    strongest = next(
        (s for s in signals if s["status"] == "strong"),
        signals[0]
    )

    weakest = next(
        (s for s in signals if s["status"] == "weak"),
        signals[-1]
    )

    if score >= 70:
        summary = "The technical outlook is strong."
    elif score <= 35:
        summary = "The technical outlook is weak."
    else:
        summary = "Technical signals are mixed."

    return {
        "score": score,
        "rsi14": rsi14,
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "macd": macd_data,
        "bollinger": bollinger_data,
        "support": support,
        "resistance": resistance,
        "signals": signals,
        "strongest": strongest,
        "weakest": weakest,
        "summary": summary,
        "disclaimer": "This AI technical analysis is not investment advice. It is for informational purposes only."
    }


def market_state(raw):
    if raw == "REGULAR":
        return "OPEN"

    if raw == "PRE":
        return "PRE"

    if raw == "POST":
        return "POST"

    return "CLOSED"


def get_fast_value(fast, key):
    try:
        return safe_float(fast.get(key))
    except Exception:
        return None


def main():
    symbol = clean_symbol(
        sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    )

    chart_range = clean_range(
        sys.argv[2] if len(sys.argv) > 2 else "1D"
    )

    selected = RANGES[chart_range]

    ticker = yf.Ticker(symbol)

    hist_df = ticker.history(
        period=selected["period"],
        interval=selected["interval"],
        auto_adjust=False,
        prepost=True
    )

    if hist_df is None or hist_df.empty:
        hist_df = ticker.history(
            period="1mo",
            interval="1d",
            auto_adjust=False,
            prepost=True
        )

    if hist_df is None or hist_df.empty:
        raise Exception("No price history returned from yfinance.")

    candles = dataframe_to_candles(hist_df)

    if len(candles) < 2:
        raise Exception("Not enough candle data returned from yfinance.")

    try:
        fast = ticker.fast_info or {}
    except Exception:
        fast = {}

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    last = candles[-1]
    prev = candles[-2]

    price = (
        safe_float(info.get("regularMarketPrice"))
        or safe_float(info.get("currentPrice"))
        or get_fast_value(fast, "last_price")
        or last["close"]
    )

    previous_close = (
        safe_float(info.get("previousClose"))
        or get_fast_value(fast, "previous_close")
        or prev["close"]
    )

    after_price = (
        safe_float(info.get("postMarketPrice"))
        or safe_float(info.get("preMarketPrice"))
    )

    change = price - previous_close
    change_percent = (
        change / previous_close * 100
        if previous_close
        else 0
    )

    after_change = None
    after_change_percent = None

    if after_price is not None:
        after_change = after_price - price
        after_change_percent = (
            after_change / price * 100
            if price
            else 0
        )

    name = (
        info.get("shortName")
        or info.get("longName")
        or symbol
    )

    currency = (
        info.get("currency")
        or "USD"
    )

    closes = [
        c["close"]
        for c in candles
        if c.get("close") is not None
    ]

    quote = {
        "symbol": symbol,
        "name": name,
        "price": price,
        "change": change,
        "changePercent": change_percent,
        "previousClose": previous_close,
        "afterPrice": after_price,
        "afterChange": after_change,
        "afterChangePercent": after_change_percent,
        "open": last.get("open"),
        "high": last.get("high"),
        "low": last.get("low"),
        "volume": safe_float(info.get("volume")) or last.get("volume"),
        "currency": currency,
        "marketState": market_state(
            info.get("marketState") or "YFINANCE"
        ),
        "source": "yfinance / Yahoo Finance",
        "lastUpdate": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "warning": "yfinance is not an official API. Availability may change."
    }

    analysis = analyze(candles)

    details = {
        "symbol": symbol,
        "name": name,
        "sector": info.get("sector") or "Unknown",
        "assetType": info.get("quoteType") or "Asset",
        "marketCap": safe_float(info.get("marketCap")),
        "volume": quote["volume"],
        "high52": safe_float(info.get("fiftyTwoWeekHigh")) or max(closes),
        "low52": safe_float(info.get("fiftyTwoWeekLow")) or min(closes),
        "source": quote["source"],
        "website": info.get("website") or ""
    }

    news = [
        {
            "title": f"{name} technical outlook and price action are being monitored",
            "source": "CHARTIX News",
            "time": "Current",
            "url": "#"
        },
        {
            "title": f"{symbol} analyzed by RSI, MACD, support and resistance",
            "source": "Market Desk",
            "time": "Current",
            "url": "#"
        }
    ]

    result = {
        "quote": quote,
        "history": {
            "symbol": symbol,
            "range": chart_range,
            "rangeLabel": selected["label"],
            "candles": candles,
            "source": "yfinance"
        },
        "analysis": analysis,
        "details": details,
        "news": news
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "trace": traceback.format_exc()
        }, ensure_ascii=False))
        sys.exit(1)