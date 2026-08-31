"""Encrypted-at-rest storage for broker credentials and session tokens.

Secrets never touch the database in plaintext. The Fernet key lives only in the
process environment (a platform secret on the host), so a database dump alone
is useless to an attacker.
"""
from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class VaultError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = get_settings().vault_key
    if not key:
        raise VaultError("VAULT_KEY is not set; refusing to store secrets in plaintext")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:  # malformed key
        raise VaultError(f"VAULT_KEY is not a valid Fernet key: {exc}") from exc


def seal(payload: dict[str, Any]) -> str:
    return _fernet().encrypt(json.dumps(payload).encode()).decode()


def unseal(blob: str) -> dict[str, Any]:
    try:
        return json.loads(_fernet().decrypt(blob.encode()).decode())
    except InvalidToken as exc:
        raise VaultError("cannot decrypt secret; VAULT_KEY changed or data corrupt") from exc
