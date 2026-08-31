"""SQLAlchemy engine/session plus the persistence model."""
from __future__ import annotations

import datetime as dt
import pathlib

from sqlalchemy import Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Secret(Base):
    """One row per named secret bundle; `blob` is Fernet ciphertext."""

    __tablename__ = "secrets"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    blob: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)


class OrderRecord(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=_utcnow, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[int] = mapped_column()
    price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(24))
    broker_order_id: Mapped[str] = mapped_column(String(64), default="")
    rationale: Mapped[str] = mapped_column(Text, default="")


class EventLog(Base):
    """Append-only audit trail: every agent decision and auth event lands here."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[dt.datetime] = mapped_column(default=_utcnow, index=True)
    level: Mapped[str] = mapped_column(String(16), default="info")
    source: Mapped[str] = mapped_column(String(48))
    message: Mapped[str] = mapped_column(Text)


_settings = get_settings()
if _settings.database_url.startswith("sqlite:///"):
    pathlib.Path(_settings.database_url.removeprefix("sqlite:///")).parent.mkdir(
        parents=True, exist_ok=True
    )

engine = create_engine(_settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)


def log_event(source: str, message: str, level: str = "info") -> None:
    with SessionLocal() as session:
        session.add(EventLog(source=source, message=message, level=level))
        session.commit()
