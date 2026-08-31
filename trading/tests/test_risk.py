import datetime as dt

from app.agents.risk import RiskAgent, RiskLimits
from app.brokers.base import Candle, Position

LIMITS = RiskLimits(capital=100_000, max_position_pct=0.15, max_open_positions=2)


def candles(n=80, price=100.0):
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    return [
        Candle(start + dt.timedelta(days=i), price, price * 1.02, price * 0.98, price, 1000)
        for i in range(n)
    ]


def test_position_is_capped_by_max_position_pct():
    verdict = RiskAgent(LIMITS).assess("A", "BUY", 100.0, candles(), [], cash=1_000_000)
    assert verdict.approved
    assert verdict.quantity * 100.0 <= LIMITS.capital * LIMITS.max_position_pct + 1e-6


def test_daily_loss_limit_halts_trading():
    verdict = RiskAgent(LIMITS).assess(
        "A", "BUY", 100.0, candles(), [], cash=100_000, realised_pnl=-5_000
    )
    assert not verdict.approved and "halted" in verdict.reason


def test_open_position_cap_is_enforced():
    held = [Position("X", 10, 100, 100), Position("Y", 10, 100, 100)]
    verdict = RiskAgent(LIMITS).assess("Z", "BUY", 100.0, candles(), held, cash=100_000)
    assert not verdict.approved and "cap reached" in verdict.reason


def test_no_pyramiding_into_an_existing_long():
    held = [Position("A", 10, 100, 100)]
    assert not RiskAgent(LIMITS).assess("A", "BUY", 100.0, candles(), held, cash=100_000).approved


def test_selling_without_a_position_is_refused():
    assert not RiskAgent(LIMITS).assess("A", "SELL", 100.0, candles(), [], cash=100_000).approved


def test_sell_closes_the_whole_position():
    held = [Position("A", 7, 100, 110)]
    verdict = RiskAgent(LIMITS).assess("A", "SELL", 110.0, candles(), held, cash=0)
    assert verdict.approved and verdict.quantity == 7


def test_cash_constrains_size():
    verdict = RiskAgent(LIMITS).assess("A", "BUY", 100.0, candles(), [], cash=250.0)
    assert verdict.quantity <= 2
