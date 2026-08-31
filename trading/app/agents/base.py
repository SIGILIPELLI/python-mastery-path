"""Agent protocol shared by every analyst in the fleet."""
from __future__ import annotations

import abc
import dataclasses
from typing import Literal

from app.brokers.base import Candle

Action = Literal["BUY", "SELL", "HOLD"]


@dataclasses.dataclass(frozen=True)
class Signal:
    """One agent's opinion about one symbol.

    `confidence` is 0..1 and is what the coordinator weighs; `rationale` is
    plain English and is persisted so every trade can be explained afterwards.
    """

    agent: str
    symbol: str
    action: Action
    confidence: float
    rationale: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")

    @property
    def score(self) -> float:
        """Signed contribution: +conf for BUY, -conf for SELL, 0 for HOLD."""
        return {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0}[self.action] * self.confidence


class Agent(abc.ABC):
    name: str = "agent"
    weight: float = 1.0

    @abc.abstractmethod
    def evaluate(self, symbol: str, candles: list[Candle]) -> Signal: ...

    def _hold(self, symbol: str, why: str) -> Signal:
        return Signal(self.name, symbol, "HOLD", 0.0, why)
