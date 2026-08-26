from __future__ import annotations


def score_setup(metrics: dict) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    price = metrics["last_close"]
    ema20 = metrics["ema20"]
    ema50 = metrics["ema50"]
    rsi = metrics["rsi"]
    macd = metrics["macd"]
    macd_signal = metrics["macd_signal"]
    rv = metrics["relative_volume"]
    distance = metrics["distance_to_breakout_pct"]

    if price > ema20:
        score += 15
        reasons.append("السعر فوق EMA20")

    if ema20 > ema50:
        score += 15
        reasons.append("EMA20 فوق EMA50")

    if 50 <= rsi <= 68:
        score += 15
        reasons.append(f"RSI مناسب ({rsi:.1f})")
    elif 45 <= rsi < 50 or 68 < rsi <= 72:
        score += 7

    if macd > macd_signal:
        score += 12
        reasons.append("MACD إيجابي")

    if rv >= 1.5:
        score += 18
        reasons.append(f"Relative Volume قوي ({rv:.2f})")
    elif rv >= 1.1:
        score += 10
        reasons.append(f"Relative Volume جيد ({rv:.2f})")

    if 0 <= distance <= 3:
        score += 20
        reasons.append(f"قريب من الاختراق ({distance:.1f}%)")
    elif -2 <= distance < 0:
        score += 14
        reasons.append("اختراق مبكر")
    elif 3 < distance <= 6:
        score += 8

    if price > metrics["support"] and metrics["resistance"] > price:
        score += 5

    return min(score, 100), reasons


def trade_levels(metrics: dict) -> dict:
    price = metrics["last_close"]
    atr = max(metrics["atr14"], price * 0.02)
    resistance = metrics["resistance"]
    support = metrics["support"]

    entry_low = max(metrics["ema20"], price - 0.35 * atr)
    entry_high = price + 0.10 * atr
    stop = max(support, entry_low - 1.15 * atr)

    risk = max(entry_high - stop, price * 0.01)
    target1 = entry_high + 2.0 * risk
    target2 = entry_high + 3.0 * risk

    return {
        "entry_low": entry_low,
        "entry_high": entry_high,
        "breakout": resistance,
        "stop": stop,
        "target1": target1,
        "target2": target2,
    }
