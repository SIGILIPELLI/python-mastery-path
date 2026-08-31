"""Control API. Everything mutating sits behind the admin bearer token."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

from app.api.deps import get_engine, require_admin, runtime
from app.backtest import backtest
from app.brokers.paytm_auth import Credentials, NeedsManualLogin, save_credentials
from app.core.config import get_settings
from app.core.db import EventLog, OrderRecord, SessionLocal

router = APIRouter()


class OnboardRequest(BaseModel):
    """Sent exactly once, over HTTPS. Stored encrypted; never returned."""

    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    login_id: str = Field(min_length=1)
    password: str = Field(min_length=1)
    totp_secret: str = Field(min_length=1, description="Base32 seed from Paytm 2FA setup")


class RequestTokenPayload(BaseModel):
    request_token: str = Field(min_length=1)


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "broker": settings.broker,
        "dry_run": settings.dry_run,
        "scheduler_running": bool(runtime.scheduler and runtime.scheduler.running),
        "needs_manual_login": bool(runtime.sessions and runtime.sessions.needs_manual_login),
    }


@router.post("/auth/onboard", dependencies=[Depends(require_admin)])
def onboard(payload: OnboardRequest) -> dict:
    save_credentials(Credentials(**payload.model_dump()))
    return {"status": "stored", "detail": "credentials encrypted; daily re-auth is now automatic"}


@router.post("/auth/refresh", dependencies=[Depends(require_admin)])
def refresh() -> dict:
    if runtime.sessions is None:
        raise HTTPException(503, "no session manager (paper broker in use)")
    try:
        runtime.sessions.refresh()
    except NeedsManualLogin as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"status": "refreshed"}


@router.post("/auth/request-token", dependencies=[Depends(require_admin)])
def adopt(payload: RequestTokenPayload) -> dict:
    """Manual escape hatch when headless re-auth breaks."""
    if runtime.sessions is None:
        raise HTTPException(503, "no session manager (paper broker in use)")
    try:
        runtime.sessions.adopt_request_token(payload.request_token)
    except NeedsManualLogin as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"status": "adopted"}


@router.post("/run", dependencies=[Depends(require_admin)])
def run_now(engine=Depends(get_engine)) -> dict:
    return engine.run_once().as_dict()


@router.get("/report")
def last_report(engine=Depends(get_engine)) -> dict:
    return engine.last_report.as_dict() if engine.last_report else {"detail": "no run yet"}


@router.get("/positions")
def positions(engine=Depends(get_engine)) -> list[dict]:
    return [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "average_price": p.average_price,
            "last_price": p.last_price,
            "pnl": round(p.pnl, 2),
        }
        for p in engine.broker.positions()
    ]


@router.get("/orders")
def orders(limit: int = 50) -> list[dict]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(OrderRecord).order_by(desc(OrderRecord.created_at)).limit(min(limit, 200))
        ).all()
    return [
        {
            "at": r.created_at.isoformat(),
            "symbol": r.symbol,
            "side": r.side,
            "quantity": r.quantity,
            "price": r.price,
            "status": r.status,
            "rationale": r.rationale,
        }
        for r in rows
    ]


@router.get("/events")
def events(limit: int = 100) -> list[dict]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(EventLog).order_by(desc(EventLog.created_at)).limit(min(limit, 500))
        ).all()
    return [
        {"at": r.created_at.isoformat(), "level": r.level, "source": r.source, "message": r.message}
        for r in rows
    ]


@router.get("/backtest/{symbol}", dependencies=[Depends(require_admin)])
def run_backtest(symbol: str, engine=Depends(get_engine)) -> dict:
    result = backtest(engine.broker, symbol.upper(), capital=get_settings().capital)
    return {
        "symbol": result.symbol,
        "trades": result.trades,
        "hit_rate": round(result.hit_rate, 3),
        "pnl": round(result.pnl, 2),
        "final_equity": round(result.final_equity, 2),
    }
