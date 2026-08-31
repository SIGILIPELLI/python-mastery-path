import os

import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("VAULT_KEY", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test.db")

from app.backtest import backtest  # noqa: E402
from app.brokers.paper import PaperBroker  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.core.db import init_db  # noqa: E402
from app.core.vault import seal, unseal  # noqa: E402
from app.engine import Engine  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_db()


def settings(**overrides) -> Settings:
    base = dict(
        vault_key=os.environ["VAULT_KEY"],
        database_url=os.environ["DATABASE_URL"],
        broker="paper",
        dry_run=True,
        universe="RELIANCE,TCS,INFY",
        capital=100_000,
    )
    base.update(overrides)
    return Settings(**base)


def test_vault_round_trip():
    assert unseal(seal({"password": "hunter2"}))["password"] == "hunter2"


def test_vault_ciphertext_hides_the_secret():
    assert "hunter2" not in seal({"password": "hunter2"})


def test_dry_run_never_reaches_the_broker():
    broker = PaperBroker(cash=100_000)
    calls = []
    broker.place_order = lambda *a, **k: calls.append(a)  # type: ignore[method-assign]

    report = Engine(broker, settings(dry_run=True)).run_once()
    assert calls == []
    assert all(p["status"] == "DRY_RUN" for p in report.placed)


def test_a_pass_covers_every_symbol_without_errors():
    report = Engine(PaperBroker(cash=100_000), settings()).run_once()
    assert report.errors == []
    assert {d.symbol for d in report.decisions} == {"RELIANCE", "TCS", "INFY"}


def test_one_bad_symbol_does_not_abort_the_pass():
    broker = PaperBroker(cash=100_000)
    real_history = broker.history

    def flaky(symbol, days=120):
        if symbol == "TCS":
            raise RuntimeError("feed down")
        return real_history(symbol, days)

    broker.history = flaky  # type: ignore[method-assign]
    report = Engine(broker, settings()).run_once()
    assert any("TCS" in e for e in report.errors)
    assert {d.symbol for d in report.decisions} == {"RELIANCE", "INFY"}


def test_broker_outage_aborts_cleanly():
    broker = PaperBroker()
    broker.positions = lambda: (_ for _ in ()).throw(RuntimeError("no auth"))  # type: ignore
    report = Engine(broker, settings()).run_once()
    assert report.errors and report.placed == []


def test_backtest_produces_a_coherent_result():
    result = backtest(PaperBroker(), "RELIANCE", capital=100_000)
    assert result.trades >= 0
    assert 0.0 <= result.hit_rate <= 1.0
