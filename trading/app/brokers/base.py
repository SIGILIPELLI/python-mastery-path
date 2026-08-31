"""Broker abstraction. Agents only ever talk to this interface."""
from __future__ import annotations

import abc
import dataclasses
import datetime as dt


@dataclasses.dataclass(frozen=True)
class Candle:
    timestamp: dt.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclasses.dataclass(frozen=True)
class Quote:
    symbol: str
    last_price: float


@dataclasses.dataclass(frozen=True)
class Position:
    symbol: str
    quantity: int
    average_price: float
    last_price: float

    @property
    def pnl(self) -> float:
        return (self.last_price - self.average_price) * self.quantity


@dataclasses.dataclass(frozen=True)
class OrderResult:
    broker_order_id: str
    status: str
    filled_price: float


class Broker(abc.ABC):
    """Minimum surface the strategy stack needs from any broker."""

    @abc.abstractmethod
    def history(self, symbol: str, days: int = 120) -> list[Candle]: ...

    @abc.abstractmethod
    def quote(self, symbol: str) -> Quote: ...

    @abc.abstractmethod
    def positions(self) -> list[Position]: ...

    @abc.abstractmethod
    def funds(self) -> float: ...

    @abc.abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int, price: float) -> OrderResult: ...
