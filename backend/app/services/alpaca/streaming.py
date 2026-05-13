"""Alpaca streaming fan-out manager.

A single upstream StockDataStream is multiplexed to many per-client asyncio.Queues.
The manager subscribes upstream on first listener, unsubscribes on last drop.
"""

from __future__ import annotations

import asyncio
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from alpaca.data.live.stock import StockDataStream

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("alpaca.streaming")

QUEUE_SIZE = 1000
RECONNECT_DELAYS = [1, 2, 4, 8, 16, 30]
EventEnvelope = dict[str, Any]


@dataclass
class _Subscriber:
    queue: asyncio.Queue[EventEnvelope]
    symbols: set[str] = field(default_factory=set)
    kinds: set[str] = field(default_factory=lambda: {"quotes", "trades", "bars"})


class AlpacaStreamManager:
    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.alpaca_api_key.get_secret_value()
        self._secret = s.alpaca_secret_key.get_secret_value()
        self._feed = s.alpaca_data_feed
        self._stream: StockDataStream | None = None
        self._task: asyncio.Task | None = None
        self._subs: dict[str, set[_Subscriber]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._upstream_kinds: dict[str, set[str]] = defaultdict(set)
        self._dropped = 0

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_forever(), name="alpaca-stream")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        if self._stream is not None:
            try:
                await self._stream.stop_ws()
            except Exception:
                pass
            self._stream = None

    async def _run_forever(self) -> None:
        attempt = 0
        while True:
            try:
                await self._connect_and_run()
                attempt = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                delay = RECONNECT_DELAYS[min(attempt, len(RECONNECT_DELAYS) - 1)]
                jitter = random.uniform(0, 0.5 * delay)
                wait = delay + jitter
                log.warning("stream.disconnect", error=str(exc), retry_in=wait)
                attempt += 1
                self._broadcast_system({"reconnecting_in": wait})
                await asyncio.sleep(wait)

    async def _connect_and_run(self) -> None:
        log.info("stream.connect", feed=self._feed)
        self._stream = StockDataStream(self._api_key, self._secret, feed=self._feed)

        async def on_quote(q):
            await self._fanout(
                "quote",
                q.symbol,
                {
                    "bid": q.bid_price,
                    "bid_size": q.bid_size,
                    "ask": q.ask_price,
                    "ask_size": q.ask_size,
                    "ts": q.timestamp.isoformat() if q.timestamp else None,
                },
            )

        async def on_trade(t):
            await self._fanout(
                "trade",
                t.symbol,
                {
                    "price": t.price,
                    "size": t.size,
                    "ts": t.timestamp.isoformat() if t.timestamp else None,
                },
            )

        async def on_bar(b):
            await self._fanout(
                "bar",
                b.symbol,
                {
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                    "ts": b.timestamp.isoformat() if b.timestamp else None,
                },
            )

        # Re-subscribe any existing symbols on (re)connect.
        for sym, kinds in self._upstream_kinds.items():
            if "quotes" in kinds:
                self._stream.subscribe_quotes(on_quote, sym)
            if "trades" in kinds:
                self._stream.subscribe_trades(on_trade, sym)
            if "bars" in kinds:
                self._stream.subscribe_bars(on_bar, sym)

        self._broadcast_system({"connected": True})
        self._on_quote = on_quote
        self._on_trade = on_trade
        self._on_bar = on_bar

        # alpaca-py's run() is blocking sync; bridge via to_thread.
        await asyncio.to_thread(self._stream.run)

    async def _fanout(self, kind: str, symbol: str, data: dict) -> None:
        envelope: EventEnvelope = {"kind": kind, "symbol": symbol, "data": data}
        for sub in list(self._subs.get(symbol, ())):
            if kind + "s" not in sub.kinds and kind not in sub.kinds:
                continue
            try:
                sub.queue.put_nowait(envelope)
            except asyncio.QueueFull:
                self._dropped += 1
                try:
                    sub.queue.get_nowait()
                    sub.queue.put_nowait(envelope)
                except Exception:
                    pass

    def _broadcast_system(self, data: dict) -> None:
        for subs in self._subs.values():
            for sub in subs:
                try:
                    sub.queue.put_nowait({"kind": "system", "data": data})
                except asyncio.QueueFull:
                    pass

    async def subscribe(
        self,
        symbols: list[str],
        queue: asyncio.Queue,
        kinds: tuple[str, ...] = ("quotes", "trades"),
    ) -> _Subscriber:
        sub = _Subscriber(queue=queue, symbols=set(symbols), kinds=set(kinds))
        async with self._lock:
            for sym in symbols:
                self._subs[sym].add(sub)
                added = kinds and not self._upstream_kinds[sym]
                if added and self._stream is not None:
                    if "quotes" in kinds:
                        self._stream.subscribe_quotes(self._on_quote, sym)
                    if "trades" in kinds:
                        self._stream.subscribe_trades(self._on_trade, sym)
                    if "bars" in kinds:
                        self._stream.subscribe_bars(self._on_bar, sym)
                self._upstream_kinds[sym].update(kinds)
        return sub

    async def unsubscribe(self, sub: _Subscriber) -> None:
        async with self._lock:
            for sym in list(sub.symbols):
                self._subs[sym].discard(sub)
                if not self._subs[sym]:
                    self._upstream_kinds.pop(sym, None)
                    if self._stream is not None:
                        try:
                            self._stream.unsubscribe_quotes(sym)
                            self._stream.unsubscribe_trades(sym)
                            self._stream.unsubscribe_bars(sym)
                        except Exception:
                            pass


_manager: AlpacaStreamManager | None = None


def get_stream_manager() -> AlpacaStreamManager:
    global _manager
    if _manager is None:
        _manager = AlpacaStreamManager()
    return _manager
