"""Cron for the trading day, in IST regardless of where the container runs.

08:45 — re-authenticate headlessly, well before the market opens at 09:15.
09:20–15:15 — run the agent fleet every 15 minutes on weekdays.
15:25 — end-of-day summary into the event log.

Holidays are not modelled: on an NSE holiday the broker simply returns stale
data and the coordinator finds no consensus, so the pass is a no-op.
"""
from __future__ import annotations

import zoneinfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.db import log_event

IST = zoneinfo.ZoneInfo("Asia/Kolkata")
WEEKDAYS = "mon-fri"


def build_scheduler(engine, refresh_session) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=IST)

    scheduler.add_job(
        refresh_session,
        CronTrigger(day_of_week=WEEKDAYS, hour=8, minute=45, timezone=IST),
        id="daily-auth",
        replace_existing=True,
        misfire_grace_time=1800,
    )
    scheduler.add_job(
        engine.run_once,
        CronTrigger(day_of_week=WEEKDAYS, hour="9-15", minute="*/15", timezone=IST),
        id="trading-pass",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        lambda: log_event("scheduler", "trading day closed"),
        CronTrigger(day_of_week=WEEKDAYS, hour=15, minute=25, timezone=IST),
        id="eod-summary",
        replace_existing=True,
    )
    return scheduler
