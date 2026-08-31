"""Walk-forward backtest over the same agents the live engine uses.

No separate research code path — if the backtest disagrees with production it
is a data problem, not a logic problem, which is the entire point of reusing
`Coordinator` and `RiskAgent` here verbatim.
"""
from __future__ import annotations

import dataclasses

from app.agents.analysts import default_fleet
from app.agents.coordinator import Coordinator
from app.agents.risk import RiskAgent, RiskLimits
from app.brokers.base import Broker


@dataclasses.dataclass
class BacktestResult:
    symbol: str
    trades: int
    wins: int
    pnl: float
    final_equity: float

    @property
    def hit_rate(self) -> float:
        return self.wins / self.trades if self.trades else 0.0


def backtest(broker: Broker, symbol: str, capital: float = 100_000.0, warmup: int = 60) -> BacktestResult:
    candles = broker.history(symbol, days=365)
    if len(candles) <= warmup + 1:
        return BacktestResult(symbol, 0, 0, 0.0, capital)

    coordinator = Coordinator(default_fleet())
    risk = RiskAgent(RiskLimits(capital=capital))

    cash, qty, entry = capital, 0, 0.0
    trades = wins = 0
    realised = 0.0

    for i in range(warmup, len(candles)):
        window = candles[:i]
        price = candles[i].open  # trade the next open, never the signal bar's close
        decision = coordinator.decide(symbol, window)

        if decision.action == "BUY" and qty == 0:
            verdict = risk.assess(symbol, "BUY", price, window, [], cash, realised)
            if verdict.approved:
                qty, entry = verdict.quantity, price
                cash -= qty * price
        elif decision.action == "SELL" and qty > 0:
            cash += qty * price
            pnl = (price - entry) * qty
            realised += pnl
            trades += 1
            wins += pnl > 0
            qty = 0

    if qty:  # mark the open position out at the last close
        last = candles[-1].close
        cash += qty * last
        pnl = (last - entry) * qty
        realised += pnl
        trades += 1
        wins += pnl > 0

    return BacktestResult(symbol, trades, wins, realised, cash)
