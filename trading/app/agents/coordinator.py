"""Portfolio coordinator — turns a fleet of opinions into at most one decision.

Consensus rule: weighted mean of each agent's signed score, then a threshold.
Two extra guards make the ensemble behave better than any single agent:

* Agreement — a decision needs at least two agents pointing the same way, so a
  single loud agent cannot trade the book on its own.
* Dissent damping — the consensus is scaled down by how split the fleet is, so
  a 3-against-1 read sizes smaller than a clean sweep.
"""
from __future__ import annotations

import dataclasses

from app.agents.base import Agent, Signal
from app.brokers.base import Candle

BUY_THRESHOLD = 0.25
SELL_THRESHOLD = -0.25


@dataclasses.dataclass(frozen=True)
class Decision:
    symbol: str
    action: str
    conviction: float
    signals: list[Signal]
    rationale: str


class Coordinator:
    def __init__(self, fleet: list[Agent]) -> None:
        if not fleet:
            raise ValueError("coordinator needs at least one agent")
        self.fleet = fleet

    def decide(self, symbol: str, candles: list[Candle]) -> Decision:
        signals = [agent.evaluate(symbol, candles) for agent in self.fleet]
        weights = [agent.weight for agent in self.fleet]
        total_weight = sum(weights) or 1.0

        consensus = sum(s.score * w for s, w in zip(signals, weights)) / total_weight

        buyers = sum(1 for s in signals if s.action == "BUY")
        sellers = sum(1 for s in signals if s.action == "SELL")
        voters = buyers + sellers

        if voters:
            majority = max(buyers, sellers)
            consensus *= majority / voters  # damp a split fleet

        action, reason = self._classify(consensus, buyers, sellers)
        detail = "; ".join(f"{s.agent}:{s.action}({s.confidence:.2f})" for s in signals)
        return Decision(
            symbol=symbol,
            action=action,
            conviction=abs(consensus),
            signals=signals,
            rationale=f"{reason} [consensus {consensus:+.3f}] {detail}",
        )

    @staticmethod
    def _classify(consensus: float, buyers: int, sellers: int) -> tuple[str, str]:
        if consensus >= BUY_THRESHOLD:
            if buyers < 2:
                return "HOLD", "bullish consensus rests on a single agent"
            return "BUY", f"{buyers} agents bullish"
        if consensus <= SELL_THRESHOLD:
            if sellers < 2:
                return "HOLD", "bearish consensus rests on a single agent"
            return "SELL", f"{sellers} agents bearish"
        return "HOLD", "no consensus"
