from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.trading.requests import GetAssetsRequest


EXCLUDED_NAME_TERMS = (
    " ETF",
    " ETN",
    " FUND",
    " TRUST",
    " WARRANT",
    " WTS",
    " UNIT",
    " UNITS",
    " PREFERRED",
    " DEPOSITARY",
    " ACQUISITION CORP",
    " ACQUISITION CORPORATION",
)


def chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


class AlpacaClient:
    def __init__(self, api_key: str, secret_key: str) -> None:
        self.trading = TradingClient(api_key, secret_key, paper=True)
        self.data = StockHistoricalDataClient(api_key, secret_key)

    def get_active_stock_symbols(self) -> list[str]:
        request = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
        )
        assets = self.trading.get_all_assets(request)

        symbols: list[str] = []
        for asset in assets:
            exchange = str(asset.exchange).upper()
            name = (asset.name or "").upper()

            if not asset.tradable:
                continue
            if exchange not in {"NASDAQ", "NYSE", "AMEX", "NYSEARCA"}:
                continue
            if any(term in name for term in EXCLUDED_NAME_TERMS):
                continue
            if "." in asset.symbol or "/" in asset.symbol:
                continue

            symbols.append(asset.symbol.upper())

        return sorted(set(symbols))

    def prefilter_with_snapshots(
        self,
        symbols: list[str],
        min_price: float,
        max_price: float,
        min_prev_day_volume: int,
        chunk_size: int,
    ) -> list[dict]:
        candidates: list[dict] = []

        for batch in chunks(symbols, chunk_size):
            request = StockSnapshotRequest(
                symbol_or_symbols=batch,
                feed=DataFeed.IEX,
            )
            try:
                snapshots = self.data.get_stock_snapshot(request)
            except Exception as exc:
                print(f"Snapshot batch failed ({len(batch)} symbols): {exc}")
                continue

            for symbol, snapshot in snapshots.items():
                latest_trade = getattr(snapshot, "latest_trade", None)
                daily_bar = getattr(snapshot, "daily_bar", None)
                prev_bar = getattr(snapshot, "previous_daily_bar", None)

                if latest_trade is None or prev_bar is None:
                    continue

                price = float(latest_trade.price)
                prev_volume = int(prev_bar.volume or 0)
                current_volume = int(daily_bar.volume or 0) if daily_bar else 0

                if not (min_price <= price <= max_price):
                    continue
                if prev_volume < min_prev_day_volume:
                    continue

                candidates.append(
                    {
                        "symbol": symbol,
                        "price": price,
                        "prev_volume": prev_volume,
                        "current_volume": current_volume,
                        "liquidity_rank": max(prev_volume, current_volume),
                    }
                )

        candidates.sort(key=lambda row: row["liquidity_rank"], reverse=True)
        return candidates

    def get_daily_bars(
        self,
        symbols: list[str],
        history_days: int,
        chunk_size: int,
    ) -> dict[str, pd.DataFrame]:
        result: dict[str, pd.DataFrame] = {}
        start = datetime.now(timezone.utc) - timedelta(days=history_days * 2)

        for batch in chunks(symbols, chunk_size):
            request = StockBarsRequest(
                symbol_or_symbols=batch,
                timeframe=TimeFrame.Day,
                start=start,
                feed=DataFeed.IEX,
            )
            try:
                bars = self.data.get_stock_bars(request)
            except Exception as exc:
                print(f"Bars batch failed ({len(batch)} symbols): {exc}")
                continue

            frame = bars.df
            if frame is None or frame.empty:
                continue

            frame = frame.reset_index()
            for symbol, group in frame.groupby("symbol"):
                cleaned = (
                    group.sort_values("timestamp")
                    .tail(history_days)
                    .reset_index(drop=True)
                )
                result[str(symbol)] = cleaned

        return result
