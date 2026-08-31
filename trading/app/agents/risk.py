"""Risk agent — the only component with a veto over every other agent.

Deliberately dumb and absolute. Position sizing is volatility-aware (ATR based)
so a jumpy stock gets fewer shares than a sleepy one for the same rupee risk,
and hard caps are checked *after* sizing so no combination of agent enthusiasm
can breach them.
"""
from __future__ import annotations

import dataclasses

from app.agents.analysts import stop_distance
from app.brokers.base import Candle, Position


@dataclasses.dataclass(frozen=True)
class RiskLimits:
    capital: float
    max_position_pct: float = 0.15
    max_daily_loss_pct: float = 0.03
    max_open_positions: int = 5
    risk_per_trade_pct: float = 0.01


@dataclasses.dataclass(frozen=True)
class RiskVerdict:
    approved: bool
    quantity: int
    reason: str


class RiskAgent:
    name = "risk"

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def day_halted(self, realised_pnl: float) -> bool:
        """True once the day's loss budget is spent. Checked before anything else."""
        return realised_pnl <= -abs(self.limits.capital * self.limits.max_daily_loss_pct)

    def assess(
        self,
        symbol: str,
        action: str,
        price: float,
        candles: list[Candle],
        positions: list[Position],
        cash: float,
        realised_pnl: float = 0.0,
    ) -> RiskVerdict:
        if price <= 0:
            return RiskVerdict(False, 0, "invalid price")
        if self.day_halted(realised_pnl):
            return RiskVerdict(
                False, 0, f"daily loss limit hit ({realised_pnl:,.0f}); trading halted for the day"
            )

        held = next((p for p in positions if p.symbol == symbol), None)

        if action == "SELL":
            if not held or held.quantity <= 0:
                return RiskVerdict(False, 0, "no long position to reduce; shorting is disabled")
            return RiskVerdict(True, held.quantity, "closing existing long")

        if held and held.quantity > 0:
            return RiskVerdict(False, 0, "already long; no pyramiding")
        open_count = sum(1 for p in positions if p.quantity)
        if open_count >= self.limits.max_open_positions:
            return RiskVerdict(False, 0, f"already holding {open_count} positions (cap reached)")

        # Volatility-scaled size: risk a fixed slice of capital down to the stop.
        rupees_at_risk = self.limits.capital * self.limits.risk_per_trade_pct
        stop = stop_distance(candles) or price * 0.03
        quantity = int(rupees_at_risk / stop)

        cap_value = self.limits.capital * self.limits.max_position_pct
        quantity = min(quantity, int(cap_value / price), int(cash / price))

        if quantity <= 0:
            return RiskVerdict(False, 0, "sized position rounds to zero shares")
        return RiskVerdict(
            True, quantity, f"risking {rupees_at_risk:,.0f} with a {stop:.2f} stop -> {quantity} sh"
        )
