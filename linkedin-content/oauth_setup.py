#!/usr/bin/env python3
"""
One-time OAuth helper: exchanges your LinkedIn Developer App credentials for
an access token by walking through LinkedIn's real consent screen in your
browser. You are the one logging in and clicking "Allow" — this script only
handles the local redirect and the token exchange.

Prereqs (see SETUP.md): a LinkedIn Developer App with the "Share on LinkedIn"
and "Sign In with LinkedIn using OpenID Connect" products approved, and a
redirect URL of http://localhost:8765/callback registered on the app.

Usage:
    LINKEDIN_CLIENT_ID=... LINKEDIN_CLIENT_SECRET=... python3 oauth_setup.py

Writes the resulting access token to linkedin-content/.env (gitignored).
"""
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).parent
ENV_FILE = HERE / ".env"
REDIRECT_URI = "http://localhost:8765/callback"
SCOPES = "openid profile email w_member_social"

received = {}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        qs = urllib.parse.parse_qs(parsed.query)
        received["code"] = qs.get("code", [None])[0]
        received["state"] = qs.get("state", [None])[0]
        received["error"] = qs.get("error_description", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        msg = "Success — you can close this tab and return to the terminal." if received.get("code") else f"Error: {received.get('error')}"
        self.wfile.write(f"<html><body><p>{msg}</p></body></html>".encode())

    def log_message(self, *args):
        pass  # keep terminal quiet


def main():
    client_id = os.environ.get("LINKEDIN_CLIENT_ID")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET env vars first "
            "(from your LinkedIn Developer App's Auth tab)."
        )

    state = secrets.token_urlsafe(16)
    auth_url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    })

    print("1. Open this URL in your browser, log in, and click Allow:\n")
    print(f"   {auth_url}\n")
    print("2. Waiting for the redirect on http://localhost:8765/callback ...")

    server = HTTPServer(("localhost", 8765), CallbackHandler)
    server.handle_request()  # blocks for exactly one request

    if received.get("error"):
        raise SystemExit(f"LinkedIn returned an error: {received['error']}")
    if received.get("state") != state:
        raise SystemExit("State mismatch — possible CSRF, aborting.")
    code = received.get("code")
    if not code:
        raise SystemExit("No authorization code received.")

    token_req = urllib.request.Request(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        }).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(token_req) as resp:
        token_data = json.loads(resp.read())

    access_token = token_data["access_token"]
    expires_in_days = token_data.get("expires_in", 0) // 86400

    existing = ENV_FILE.read_text() if ENV_FILE.exists() else ""
    lines = [l for l in existing.splitlines() if not l.startswith("LINKEDIN_ACCESS_TOKEN=")]
    lines.append(f"LINKEDIN_ACCESS_TOKEN={access_token}")
    ENV_FILE.write_text("\n".join(lines) + "\n")
    ENV_FILE.chmod(0o600)

    print(f"\nAccess token saved to {ENV_FILE} (expires in ~{expires_in_days} days).")
    print("You'll need to re-run this script to refresh it when it expires.")


if __name__ == "__main__":
    main()
