"""Small, dependency-light indicator set. All functions take closing prices."""
from __future__ import annotations

import statistics


def sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def ema(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    k = 2 / (window + 1)
    out = values[0]
    for v in values[1:]:
        out = v * k + out * (1 - k)
    return out


def rsi(values: list[float], window: int = 14) -> float | None:
    if len(values) < window + 1:
        return None
    gains, losses = [], []
    for prev, cur in zip(values[-window - 1 : -1], values[-window:]):
        change = cur - prev
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def zscore(values: list[float], window: int = 20) -> float | None:
    if len(values) < window:
        return None
    window_values = values[-window:]
    spread = statistics.pstdev(window_values)
    if spread == 0:
        return None
    return (window_values[-1] - statistics.fmean(window_values)) / spread


def realised_volatility(values: list[float], window: int = 20) -> float | None:
    """Stdev of daily returns over `window` days (not annualised)."""
    if len(values) < window + 1:
        return None
    returns = [
        (cur / prev) - 1 for prev, cur in zip(values[-window - 1 : -1], values[-window:]) if prev
    ]
    if len(returns) < 2:
        return None
    return statistics.pstdev(returns)


def atr(highs: list[float], lows: list[float], closes: list[float], window: int = 14) -> float | None:
    if min(len(highs), len(lows), len(closes)) < window + 1:
        return None
    trs = []
    for i in range(-window, 0):
        prev_close = closes[i - 1]
        trs.append(max(highs[i] - lows[i], abs(highs[i] - prev_close), abs(lows[i] - prev_close)))
    return sum(trs) / window
