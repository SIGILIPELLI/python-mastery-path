"""Execution engine: one pass over the universe, end to end.

Order of operations per symbol is deliberate — analysts, then consensus, then
risk, then execution. Risk sits between the decision and the broker so that no
agent path can reach `place_order` without passing a limit check.
"""
from __future__ import annotations

import dataclasses
import datetime as dt

from app.agents.analysts import default_fleet
from app.agents.coordinator import Coordinator, Decision
from app.agents.risk import RiskAgent, RiskLimits
from app.brokers.base import Broker
from app.core.config import Settings
from app.core.db import OrderRecord, SessionLocal, log_event


@dataclasses.dataclass
class RunReport:
    started_at: dt.datetime
    decisions: list[Decision] = dataclasses.field(default_factory=list)
    placed: list[dict] = dataclasses.field(default_factory=list)
    skipped: list[dict] = dataclasses.field(default_factory=list)
    errors: list[str] = dataclasses.field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "started_at": self.started_at.isoformat(),
            "decisions": [
                {
                    "symbol": d.symbol,
                    "action": d.action,
                    "conviction": round(d.conviction, 3),
                    "rationale": d.rationale,
                }
                for d in self.decisions
            ],
            "placed": self.placed,
            "skipped": self.skipped,
            "errors": self.errors,
        }


class Engine:
    def __init__(self, broker: Broker, settings: Settings) -> None:
        self.broker = broker
        self.settings = settings
        self.coordinator = Coordinator(default_fleet())
        self.risk = RiskAgent(
            RiskLimits(
                capital=settings.capital,
                max_position_pct=settings.max_position_pct,
                max_daily_loss_pct=settings.max_daily_loss_pct,
                max_open_positions=settings.max_open_positions,
            )
        )
        self.last_report: RunReport | None = None

    def run_once(self) -> RunReport:
        report = RunReport(started_at=dt.datetime.now(dt.timezone.utc))
        try:
            positions = self.broker.positions()
            cash = self.broker.funds()
        except Exception as exc:
            report.errors.append(f"broker unreachable: {exc}")
            log_event("engine", f"aborted: {exc}", level="error")
            self.last_report = report
            return report

        unrealised = sum(p.pnl for p in positions)

        for symbol in self.settings.symbols:
            try:
                self._step(symbol, positions, cash, unrealised, report)
            except Exception as exc:  # one bad symbol must not stop the pass
                report.errors.append(f"{symbol}: {exc}")
                log_event("engine", f"{symbol} failed: {exc}", level="error")

        self.last_report = report
        log_event(
            "engine",
            f"pass complete: {len(report.placed)} order(s), {len(report.skipped)} skipped",
        )
        return report

    def _step(self, symbol, positions, cash, unrealised, report: RunReport) -> None:
        candles = self.broker.history(symbol)
        if len(candles) < 60:
            report.skipped.append({"symbol": symbol, "reason": "insufficient history"})
            return

        decision = self.coordinator.decide(symbol, candles)
        report.decisions.append(decision)
        if decision.action == "HOLD":
            return

        price = self.broker.quote(symbol).last_price
        verdict = self.risk.assess(
            symbol=symbol,
            action=decision.action,
            price=price,
            candles=candles,
            positions=positions,
            cash=cash,
            realised_pnl=unrealised,
        )
        if not verdict.approved:
            report.skipped.append(
                {"symbol": symbol, "action": decision.action, "reason": verdict.reason}
            )
            return

        rationale = f"{decision.rationale} | risk: {verdict.reason}"
        if self.settings.dry_run:
            report.placed.append(
                {
                    "symbol": symbol,
                    "side": decision.action,
                    "quantity": verdict.quantity,
                    "price": price,
                    "status": "DRY_RUN",
                    "rationale": rationale,
                }
            )
            self._record(symbol, decision.action, verdict.quantity, price, "DRY_RUN", "", rationale)
            return

        result = self.broker.place_order(symbol, decision.action, verdict.quantity, price)
        report.placed.append(
            {
                "symbol": symbol,
                "side": decision.action,
                "quantity": verdict.quantity,
                "price": result.filled_price,
                "status": result.status,
                "broker_order_id": result.broker_order_id,
                "rationale": rationale,
            }
        )
        self._record(
            symbol,
            decision.action,
            verdict.quantity,
            result.filled_price,
            result.status,
            result.broker_order_id,
            rationale,
        )

    @staticmethod
    def _record(symbol, side, quantity, price, status, broker_order_id, rationale) -> None:
        with SessionLocal() as session:
            session.add(
                OrderRecord(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    status=status,
                    broker_order_id=broker_order_id,
                    rationale=rationale,
                )
            )
            session.commit()
