"""In-memory paper broker.

Serves a deterministic pseudo-random price series so the whole agent stack can
be run, tested and backtested without any broker connectivity. Fills are
immediate at the requested price; that is optimistic, so treat paper P&L as an
upper bound on live performance.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import math
import random

from app.brokers.base import Broker, Candle, OrderResult, Position, Quote


def _seed(symbol: str) -> int:
    return int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16)


class PaperBroker(Broker):
    def __init__(self, cash: float = 100_000.0) -> None:
        self.cash = cash
        self._book: dict[str, tuple[int, float]] = {}
        self._order_seq = 0

    # ---- market data ------------------------------------------------------
    def history(self, symbol: str, days: int = 120) -> list[Candle]:
        rng = random.Random(_seed(symbol))
        price = 100.0 + _seed(symbol) % 900
        today = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        candles: list[Candle] = []
        for i in range(days, 0, -1):
            drift = math.sin(i / 9.0) * 0.004
            price = max(1.0, price * (1 + drift + rng.gauss(0, 0.012)))
            high = price * (1 + abs(rng.gauss(0, 0.005)))
            low = price * (1 - abs(rng.gauss(0, 0.005)))
            candles.append(
                Candle(
                    timestamp=today - dt.timedelta(days=i),
                    open=(high + low) / 2,
                    high=high,
                    low=low,
                    close=price,
                    volume=rng.randint(50_000, 500_000),
                )
            )
        return candles

    def quote(self, symbol: str) -> Quote:
        return Quote(symbol=symbol, last_price=self.history(symbol, 2)[-1].close)

    # ---- account ----------------------------------------------------------
    def positions(self) -> list[Position]:
        out = []
        for symbol, (qty, avg) in self._book.items():
            if qty:
                out.append(
                    Position(
                        symbol=symbol,
                        quantity=qty,
                        average_price=avg,
                        last_price=self.quote(symbol).last_price,
                    )
                )
        return out

    def funds(self) -> float:
        return self.cash

    # ---- execution --------------------------------------------------------
    def place_order(self, symbol: str, side: str, quantity: int, price: float) -> OrderResult:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        signed = quantity if side.upper() == "BUY" else -quantity
        held, avg = self._book.get(symbol, (0, 0.0))
        new_qty = held + signed

        if signed > 0:
            avg = (held * avg + signed * price) / new_qty if new_qty else price
        elif new_qty == 0:
            avg = 0.0

        self._book[symbol] = (new_qty, avg)
        self.cash -= signed * price
        self._order_seq += 1
        return OrderResult(
            broker_order_id=f"PAPER-{self._order_seq:06d}", status="COMPLETE", filled_price=price
        )
