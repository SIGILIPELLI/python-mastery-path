"""Application entrypoint: wire the broker, engine and scheduler, then serve."""
from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI

from app.api.deps import build_broker, runtime
from app.api.routes import router
from app.brokers.paytm_auth import Credentials, NeedsManualLogin, save_credentials
from app.core.config import get_settings
from app.core.db import init_db, log_event
from app.engine import Engine
from app.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("trading")


def _seed_credentials_from_env(settings) -> None:
    """Optional convenience: if credentials arrive as env vars, vault them once."""
    creds = Credentials(
        api_key=settings.paytm_api_key,
        api_secret=settings.paytm_api_secret,
        login_id=settings.paytm_login_id,
        password=settings.paytm_password,
        totp_secret=settings.paytm_totp_secret,
    )
    if not creds.missing():
        save_credentials(creds)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()

    broker = build_broker(settings)
    runtime.engine = Engine(broker, settings)
    runtime.sessions = getattr(broker, "sessions", None)

    if settings.broker == "paytm":
        with contextlib.suppress(Exception):
            _seed_credentials_from_env(settings)

    def refresh_session() -> None:
        if runtime.sessions is None:
            return
        try:
            runtime.sessions.refresh()
        except NeedsManualLogin as exc:
            log.error("daily re-auth failed, trading stays halted: %s", exc)

    runtime.scheduler = build_scheduler(runtime.engine, refresh_session)
    runtime.scheduler.start()
    log_event("app", f"started (broker={settings.broker}, dry_run={settings.dry_run})")

    try:
        yield
    finally:
        runtime.scheduler.shutdown(wait=False)
        log_event("app", "stopped")


app = FastAPI(title="Multi-Agent Auto Trading", version="1.0.0", lifespan=lifespan)
app.include_router(router)
