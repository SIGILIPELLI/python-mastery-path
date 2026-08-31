"""Paytm Money session management — the 'log in once' machinery.

Why this file exists
--------------------
SEBI rules require an interactive login for every broker session, and Paytm
Money access tokens expire at the end of each trading day. So a literal
"authenticate once, forever" is impossible against the real API. What we do
instead:

1. The human onboards ONCE, handing over api key/secret, login id, password and
   the TOTP seed shown when 2FA is enabled. All of it is Fernet-encrypted
   before it touches the database.
2. Every trading morning a scheduled job replays that login headlessly:
   password + a TOTP code generated from the stored seed -> request_token ->
   access_token. No human involved.
3. If the automated replay ever fails (password rotated, seed reset, captcha,
   API change), trading stays halted and `needs_manual_login` flips true so the
   dashboard can prompt for a one-off re-onboard. It never silently trades on a
   stale session.

Endpoint paths are collected in `Endpoints` because Paytm has revised them
before; verify against https://developer.paytmmoney.com before going live.
"""
from __future__ import annotations

import dataclasses
import datetime as dt

import httpx
import pyotp
from sqlalchemy import select

from app.core.db import SessionLocal, Secret, log_event
from app.core.vault import seal, unseal

CREDENTIAL_KEY = "paytm.credentials"
SESSION_KEY = "paytm.session"


class Endpoints:
    BASE = "https://developer.paytmmoney.com"
    LOGIN = f"{BASE}/merchant/v1/login"
    VALIDATE_PASSWORD = f"{BASE}/login/v1/validate/password"
    VALIDATE_TOTP = f"{BASE}/login/v1/validate/totp"
    ACCESS_TOKEN = f"{BASE}/accounts/v2/gettoken"


class NeedsManualLogin(RuntimeError):
    """Automated re-auth is impossible; a human must re-onboard."""


@dataclasses.dataclass(frozen=True)
class Credentials:
    api_key: str
    api_secret: str
    login_id: str
    password: str
    totp_secret: str

    def missing(self) -> list[str]:
        return [f.name for f in dataclasses.fields(self) if not getattr(self, f.name)]


def _read(name: str) -> dict | None:
    with SessionLocal() as session:
        row = session.scalar(select(Secret).where(Secret.name == name))
        return unseal(row.blob) if row else None


def _write(name: str, payload: dict) -> None:
    blob = seal(payload)
    with SessionLocal() as session:
        row = session.get(Secret, name)
        if row:
            row.blob = blob
        else:
            session.add(Secret(name=name, blob=blob))
        session.commit()


def save_credentials(creds: Credentials) -> None:
    missing = creds.missing()
    if missing:
        raise ValueError(f"missing credential fields: {', '.join(missing)}")
    _write(CREDENTIAL_KEY, dataclasses.asdict(creds))
    log_event("auth", "credentials onboarded (encrypted)")


def load_credentials() -> Credentials:
    data = _read(CREDENTIAL_KEY)
    if not data:
        raise NeedsManualLogin("no credentials onboarded yet; POST /auth/onboard first")
    return Credentials(**data)


class SessionManager:
    """Hands out a valid access token, refreshing it without human help."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=20.0)
        self.needs_manual_login = False

    # ---- public API -------------------------------------------------------
    def access_token(self) -> str:
        session = _read(SESSION_KEY)
        if session and not self._expired(session):
            return session["access_token"]
        return self.refresh()

    def refresh(self) -> str:
        creds = load_credentials()
        try:
            token = self._login(creds)
        except NeedsManualLogin:
            raise
        except Exception as exc:  # network / contract change / rejected creds
            self.needs_manual_login = True
            log_event("auth", f"automated re-auth failed: {exc}", level="error")
            raise NeedsManualLogin(f"automated re-auth failed: {exc}") from exc

        self.needs_manual_login = False
        _write(
            SESSION_KEY,
            {
                "access_token": token,
                # Paytm tokens die at end of trading day; expire defensively at
                # the next midnight UTC rather than trusting a long TTL.
                "expires_at": self._next_expiry().isoformat(),
            },
        )
        log_event("auth", "access token refreshed automatically")
        return token

    def adopt_request_token(self, request_token: str) -> str:
        """Manual fallback: human pastes a request_token from the browser flow."""
        creds = load_credentials()
        token = self._exchange(creds, request_token)
        self.needs_manual_login = False
        _write(SESSION_KEY, {"access_token": token, "expires_at": self._next_expiry().isoformat()})
        log_event("auth", "access token adopted from manual request_token")
        return token

    # ---- internals --------------------------------------------------------
    @staticmethod
    def _expired(session: dict) -> bool:
        return dt.datetime.fromisoformat(session["expires_at"]) <= dt.datetime.now(dt.timezone.utc)

    @staticmethod
    def _next_expiry() -> dt.datetime:
        now = dt.datetime.now(dt.timezone.utc)
        return (now + dt.timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)

    def _login(self, creds: Credentials) -> str:
        pwd = self._client.post(
            Endpoints.VALIDATE_PASSWORD,
            json={"username": creds.login_id, "password": creds.password, "apiKey": creds.api_key},
        )
        pwd.raise_for_status()
        state = pwd.json().get("state_key") or pwd.json().get("stateKey")
        if not state:
            raise NeedsManualLogin("password step returned no state key")

        otp = self._client.post(
            Endpoints.VALIDATE_TOTP,
            json={"state_key": state, "otp": pyotp.TOTP(creds.totp_secret).now()},
        )
        otp.raise_for_status()
        request_token = otp.json().get("request_token") or otp.json().get("requestToken")
        if not request_token:
            raise NeedsManualLogin("TOTP step returned no request token")

        return self._exchange(creds, request_token)

    def _exchange(self, creds: Credentials, request_token: str) -> str:
        resp = self._client.post(
            Endpoints.ACCESS_TOKEN,
            json={
                "api_key": creds.api_key,
                "api_secret_key": creds.api_secret,
                "request_token": request_token,
            },
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise NeedsManualLogin("token exchange returned no access_token")
        return token
