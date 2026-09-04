"""Force a fresh interactive YouTube OAuth re-auth.

Run this when the cached refresh token has expired/been revoked
(`invalid_grant: Token has been expired or revoked`). It backs up the dead
token, opens the Google consent screen in your browser, and writes a fresh
credentials/token.json.

    .venv/bin/python -u upload/reauth.py
"""
import time
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

CREDS_DIR = Path(__file__).resolve().parents[1] / "credentials"
CLIENT_SECRET_PATH = CREDS_DIR / "client_secret.json"
TOKEN_PATH = CREDS_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def main() -> None:
    if not CLIENT_SECRET_PATH.exists():
        raise SystemExit(f"Missing {CLIENT_SECRET_PATH}")

    if TOKEN_PATH.exists():
        backup = TOKEN_PATH.with_suffix(f".json.dead-{time.strftime('%Y%m%d%H%M%S')}")
        TOKEN_PATH.rename(backup)
        print(f"Moved stale token aside -> {backup.name}")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json())
    print(f"Wrote fresh token -> {TOKEN_PATH}")
    print(f"expiry: {creds.expiry}")


if __name__ == "__main__":
    main()
