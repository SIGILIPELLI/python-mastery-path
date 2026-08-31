"""Shared FastAPI dependencies: auth guard and singletons."""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.brokers.base import Broker
from app.brokers.paper import PaperBroker
from app.core.config import Settings, get_settings
from app.engine import Engine


def require_admin(authorization: str = Header(default="")) -> None:
    settings = get_settings()
    expected = f"Bearer {settings.admin_token}"
    if settings.admin_token in ("", "change-me"):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "ADMIN_TOKEN is unset or left at its default; refusing to expose the control API",
        )
    if authorization != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid admin token")


def build_broker(settings: Settings) -> Broker:
    if settings.broker == "paytm":
        from app.brokers.paytm import PaytmBroker  # imported lazily: needs credentials

        return PaytmBroker()
    return PaperBroker(cash=settings.capital)


class Runtime:
    """Process-wide singletons, assembled once at startup."""

    engine: Engine | None = None
    scheduler = None
    sessions = None


runtime = Runtime()


def get_engine() -> Engine:
    if runtime.engine is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "engine not started")
    return runtime.engine
