from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_user_id: str
    alpaca_api_key: str
    alpaca_secret_key: str

    min_price: float = 2.0
    max_price: float = 50.0
    min_prev_day_volume: int = 300_000
    max_candidates_for_history: int = 250
    max_alerts: int = 8
    min_score: int = 65
    history_days: int = 90
    request_chunk_size: int = 100

    @classmethod
    def from_env(cls) -> "Settings":
        required = {
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            "TELEGRAM_USER_ID": os.getenv("TELEGRAM_USER_ID", "").strip(),
            "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", "").strip(),
            "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", "").strip(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Missing required secrets: {', '.join(missing)}")

        return cls(
            telegram_bot_token=required["TELEGRAM_BOT_TOKEN"],
            telegram_user_id=required["TELEGRAM_USER_ID"],
            alpaca_api_key=required["ALPACA_API_KEY"],
            alpaca_secret_key=required["ALPACA_SECRET_KEY"],
            min_price=_float_env("MIN_PRICE", 2.0),
            max_price=_float_env("MAX_PRICE", 50.0),
            min_prev_day_volume=_int_env("MIN_PREV_DAY_VOLUME", 300_000),
            max_candidates_for_history=_int_env("MAX_CANDIDATES_FOR_HISTORY", 250),
            max_alerts=_int_env("MAX_ALERTS", 8),
            min_score=_int_env("MIN_SCORE", 65),
            history_days=_int_env("HISTORY_DAYS", 90),
            request_chunk_size=_int_env("REQUEST_CHUNK_SIZE", 100),
        )
