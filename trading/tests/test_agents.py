import datetime as dt

import pytest

from app.agents.analysts import BreakoutAgent, MeanReversionAgent, MomentumAgent, default_fleet
from app.agents.base import Signal
from app.agents.coordinator import Coordinator
from app.agents.indicators import rsi, sma, zscore
from app.agents.risk import RiskAgent, RiskLimits
from app.brokers.base import Candle, Position
from app.brokers.paper import PaperBroker


def series(prices):
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    return [
        Candle(start + dt.timedelta(days=i), p, p * 1.01, p * 0.99, p, 1000)
        for i, p in enumerate(prices)
    ]


def test_indicators_need_enough_history():
    assert sma([1, 2], 5) is None
    assert rsi([1, 2, 3], 14) is None
    assert zscore([1] * 20) is None  # zero variance


def test_momentum_follows_a_clean_uptrend():
    signal = MomentumAgent().evaluate("UP", series([100 * 1.01**i for i in range(120)]))
    assert signal.action == "BUY" and signal.confidence > 0.5


def test_momentum_flags_a_downtrend():
    signal = MomentumAgent().evaluate("DOWN", series([100 * 0.99**i for i in range(120)]))
    assert signal.action == "SELL"


def test_mean_reversion_buys_a_sharp_dip():
    prices = [100.0] * 100 + [100 - 3 * i for i in range(1, 15)]
    assert MeanReversionAgent().evaluate("DIP", series(prices)).action == "BUY"


def test_breakout_triggers_above_the_channel():
    prices = [100.0] * 80 + [140.0]
    assert BreakoutAgent().evaluate("BRK", series(prices)).action == "BUY"


def test_signal_rejects_impossible_confidence():
    with pytest.raises(ValueError):
        Signal("x", "Y", "BUY", 1.5, "nope")


def test_flat_tape_produces_no_consensus():
    decision = Coordinator(default_fleet()).decide("FLAT", series([100.0] * 120))
    assert decision.action == "HOLD"


def test_single_loud_agent_cannot_trade_the_book():
    class Loud:
        name, weight = "loud", 10.0

        def evaluate(self, symbol, candles):
            return Signal("loud", symbol, "BUY", 1.0, "very sure")

    class Quiet:
        name, weight = "quiet", 1.0

        def evaluate(self, symbol, candles):
            return Signal("quiet", symbol, "HOLD", 0.0, "meh")

    decision = Coordinator([Loud(), Quiet()]).decide("X", series([100.0] * 120))
    assert decision.action == "HOLD"
    assert "single agent" in decision.rationale


def test_coordinator_rejects_an_empty_fleet():
    with pytest.raises(ValueError):
        Coordinator([])


def test_paper_broker_history_is_deterministic():
    a, b = PaperBroker(), PaperBroker()
    assert [c.close for c in a.history("TCS")] == [c.close for c in b.history("TCS")]
