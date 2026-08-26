from __future__ import annotations

from datetime import datetime, timezone

from alpaca_client import AlpacaClient
from config import Settings
from indicators import analyze_bars
from scoring import score_setup, trade_levels
from telegram_client import TelegramClient


def build_message(
    total_assets: int,
    price_filtered: int,
    analyzed: int,
    opportunities: list[dict],
    settings: Settings,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header = (
        "🚀 Rocket Stock Scanner\n"
        f"🕒 {now}\n\n"
        f"تم فحص الأصول النشطة: {total_assets}\n"
        f"نجح فلتر السعر والسيولة: {price_filtered}\n"
        f"تم تحليل الشارت: {analyzed}\n"
        f"النطاق السعري: ${settings.min_price:g}–${settings.max_price:g}\n"
        "مصدر الأسعار: Alpaca IEX (ليس Full SIP)\n"
        "التوافق الشرعي: غير متحقق آليًا في هذه النسخة\n"
    )

    if not opportunities:
        return (
            header
            + "\n⚪ لم تظهر فرصة تتجاوز الحد المطلوب حاليًا."
            + f"\nالحد الأدنى للـScore: {settings.min_score}"
        )

    lines = [header, "\n🏆 أفضل الفرص:\n"]

    for index, row in enumerate(opportunities, start=1):
        levels = row["levels"]
        metrics = row["metrics"]
        reasons = "، ".join(row["reasons"][:4])

        lines.append(
            f"\n{index}) {row['symbol']} — Score {row['score']}/100\n"
            f"السعر: ${metrics['last_close']:.2f}\n"
            f"منطقة الدخول: ${levels['entry_low']:.2f}–${levels['entry_high']:.2f}\n"
            f"Breakout: ${levels['breakout']:.2f}\n"
            f"Stop: ${levels['stop']:.2f}\n"
            f"T1: ${levels['target1']:.2f} | T2: ${levels['target2']:.2f}\n"
            f"RSI: {metrics['rsi']:.1f} | RVOL: {metrics['relative_volume']:.2f}\n"
            f"السبب: {reasons}\n"
        )

    lines.append(
        "\n⚠️ هذه إشارات فنية آلية وليست توصية شراء. "
        "راجع الخبر، السيولة، والتوافق الشرعي قبل أي صفقة."
    )
    return "".join(lines)


def main() -> None:
    settings = Settings.from_env()
    telegram = TelegramClient(
        settings.telegram_bot_token,
        settings.telegram_user_id,
    )
    alpaca = AlpacaClient(
        settings.alpaca_api_key,
        settings.alpaca_secret_key,
    )

    try:
        symbols = alpaca.get_active_stock_symbols()
        print(f"Active symbols: {len(symbols)}")

        candidates = alpaca.prefilter_with_snapshots(
            symbols=symbols,
            min_price=settings.min_price,
            max_price=settings.max_price,
            min_prev_day_volume=settings.min_prev_day_volume,
            chunk_size=settings.request_chunk_size,
        )
        print(f"Snapshot candidates: {len(candidates)}")

        selected = candidates[: settings.max_candidates_for_history]
        selected_symbols = [row["symbol"] for row in selected]

        bars_by_symbol = alpaca.get_daily_bars(
            symbols=selected_symbols,
            history_days=settings.history_days,
            chunk_size=settings.request_chunk_size,
        )

        opportunities: list[dict] = []
        analyzed = 0

        for symbol in selected_symbols:
            metrics = analyze_bars(bars_by_symbol.get(symbol))
            if metrics is None:
                continue

            analyzed += 1
            score, reasons = score_setup(metrics)
            if score < settings.min_score:
                continue

            opportunities.append(
                {
                    "symbol": symbol,
                    "score": score,
                    "reasons": reasons,
                    "metrics": metrics,
                    "levels": trade_levels(metrics),
                }
            )

        opportunities.sort(
            key=lambda row: (
                row["score"],
                row["metrics"]["relative_volume"],
            ),
            reverse=True,
        )
        opportunities = opportunities[: settings.max_alerts]

        telegram.send(
            build_message(
                total_assets=len(symbols),
                price_filtered=len(candidates),
                analyzed=analyzed,
                opportunities=opportunities,
                settings=settings,
            )
        )

    except Exception as exc:
        print(f"Scanner failed: {exc}")
        telegram.send(
            "🔴 Rocket Scanner Error\n\n"
            f"{type(exc).__name__}: {exc}"
        )
        raise


if __name__ == "__main__":
    main()
