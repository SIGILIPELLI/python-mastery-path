"""The analyst fleet: four independent views of the same tape.

They are intentionally uncorrelated in method — trend-following, mean
reversion, breakout, and volatility-regime — so that agreement between them
carries information. Each returns a `Signal`; none of them can trade.
"""
from __future__ import annotations

from app.agents.base import Agent, Signal
from app.agents.indicators import atr, realised_volatility, rsi, sma, zscore
from app.brokers.base import Candle


def _closes(candles: list[Candle]) -> list[float]:
    return [c.close for c in candles]


class MomentumAgent(Agent):
    """Classic dual moving-average trend follower."""

    name = "momentum"
    weight = 1.2

    def __init__(self, fast: int = 20, slow: int = 50) -> None:
        self.fast, self.slow = fast, slow

    def evaluate(self, symbol: str, candles: list[Candle]) -> Signal:
        closes = _closes(candles)
        fast, slow = sma(closes, self.fast), sma(closes, self.slow)
        if fast is None or slow is None or slow == 0:
            return self._hold(symbol, "not enough history for the slow average")

        gap = (fast - slow) / slow
        confidence = min(abs(gap) / 0.05, 1.0)  # a 5% separation is full conviction
        if abs(gap) < 0.005:
            return self._hold(symbol, f"{self.fast}/{self.slow} averages entangled ({gap:+.2%})")
        action = "BUY" if gap > 0 else "SELL"
        return Signal(
            self.name, symbol, action, confidence,
            f"{self.fast}d average is {gap:+.2%} vs {self.slow}d — trend is "
            f"{'up' if gap > 0 else 'down'}",
        )


class MeanReversionAgent(Agent):
    """Fades stretched moves; deliberately the momentum agent's opposite."""

    name = "mean_reversion"
    weight = 1.0

    def evaluate(self, symbol: str, candles: list[Candle]) -> Signal:
        closes = _closes(candles)
        z, strength = zscore(closes, 20), rsi(closes, 14)
        if z is None or strength is None:
            return self._hold(symbol, "not enough history for z-score/RSI")

        if z <= -1.5 and strength < 35:
            return Signal(
                self.name, symbol, "BUY", min(abs(z) / 3, 1.0),
                f"stretched {z:.2f}σ below its 20d mean with RSI {strength:.0f} — oversold",
            )
        if z >= 1.5 and strength > 65:
            return Signal(
                self.name, symbol, "SELL", min(abs(z) / 3, 1.0),
                f"stretched {z:.2f}σ above its 20d mean with RSI {strength:.0f} — overbought",
            )
        return self._hold(symbol, f"price within normal range (z={z:.2f}, RSI={strength:.0f})")


class BreakoutAgent(Agent):
    """Donchian-style channel break, sized by how far past the channel we are."""

    name = "breakout"
    weight = 0.9

    def __init__(self, lookback: int = 55) -> None:
        self.lookback = lookback

    def evaluate(self, symbol: str, candles: list[Candle]) -> Signal:
        if len(candles) < self.lookback + 1:
            return self._hold(symbol, "not enough history for the channel")

        window = candles[-self.lookback - 1 : -1]
        high, low = max(c.high for c in window), min(c.low for c in window)
        last = candles[-1].close
        band = high - low
        if band <= 0:
            return self._hold(symbol, "degenerate channel")

        if last > high:
            return Signal(
                self.name, symbol, "BUY", min((last - high) / band * 10, 1.0),
                f"closed above the {self.lookback}d high of {high:.2f}",
            )
        if last < low:
            return Signal(
                self.name, symbol, "SELL", min((low - last) / band * 10, 1.0),
                f"closed below the {self.lookback}d low of {low:.2f}",
            )
        return self._hold(symbol, f"inside the {self.lookback}d channel {low:.2f}–{high:.2f}")


class VolatilityRegimeAgent(Agent):
    """Not a directional view — a veto.

    When realised volatility spikes far above its own baseline, this agent votes
    SELL (risk-off) so the coordinator's consensus gets pulled toward flat.
    """

    name = "volatility_regime"
    weight = 0.8

    def evaluate(self, symbol: str, candles: list[Candle]) -> Signal:
        closes = _closes(candles)
        short, long = realised_volatility(closes, 10), realised_volatility(closes, 60)
        if short is None or long is None or long == 0:
            return self._hold(symbol, "not enough history to judge the volatility regime")

        ratio = short / long
        if ratio > 1.6:
            return Signal(
                self.name, symbol, "SELL", min((ratio - 1.6) / 1.0, 1.0),
                f"10d volatility is {ratio:.1f}x its 60d baseline — risk-off",
            )
        if ratio < 0.7:
            return Signal(
                self.name, symbol, "BUY", min((0.7 - ratio) / 0.4, 1.0),
                f"10d volatility is {ratio:.1f}x its 60d baseline — calm tape",
            )
        return self._hold(symbol, f"volatility regime normal ({ratio:.2f}x)")


def default_fleet() -> list[Agent]:
    return [MomentumAgent(), MeanReversionAgent(), BreakoutAgent(), VolatilityRegimeAgent()]


def stop_distance(candles: list[Candle], multiple: float = 2.0) -> float | None:
    """ATR-based stop distance, used by the risk agent for position sizing."""
    value = atr([c.high for c in candles], [c.low for c in candles], _closes(candles))
    return value * multiple if value else None
