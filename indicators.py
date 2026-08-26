from __future__ import annotations

import math
import pandas as pd


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def analyze_bars(frame: pd.DataFrame) -> dict | None:
    if frame is None or len(frame) < 50:
        return None

    data = frame.copy()
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["close", "high", "low", "volume"])
    if len(data) < 50:
        return None

    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data["volume"]

    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    rsi = _rsi(close, 14)

    avg_volume20 = volume.rolling(20).mean()
    rel_volume = volume.iloc[-1] / avg_volume20.iloc[-1] if avg_volume20.iloc[-1] else 0

    resistance20 = high.shift(1).rolling(20).max().iloc[-1]
    support20 = low.shift(1).rolling(20).min().iloc[-1]

    last_price = float(close.iloc[-1])
    atr = (
        pd.concat(
            [
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs(),
            ],
            axis=1,
        )
        .max(axis=1)
        .rolling(14)
        .mean()
        .iloc[-1]
    )

    if pd.isna(resistance20) or pd.isna(support20) or pd.isna(atr):
        return None

    distance_to_breakout = (
        (float(resistance20) - last_price) / last_price * 100
        if last_price > 0
        else math.inf
    )

    return {
        "last_close": last_price,
        "ema20": float(ema20.iloc[-1]),
        "ema50": float(ema50.iloc[-1]),
        "rsi": float(rsi.iloc[-1]),
        "macd": float(macd.iloc[-1]),
        "macd_signal": float(macd_signal.iloc[-1]),
        "avg_volume20": float(avg_volume20.iloc[-1]),
        "relative_volume": float(rel_volume),
        "resistance": float(resistance20),
        "support": float(support20),
        "distance_to_breakout_pct": float(distance_to_breakout),
        "atr14": float(atr),
    }
