#!/usr/bin/env python3
"""
Publish a staged draft to LinkedIn via the official REST Posts API.

This script performs the actual publish action. It should only ever be
invoked after the user has explicitly approved the specific draft in chat —
that approval gate lives in the operating prompt / conversation, not in this
script. This script has no concept of "approved"; it will post whatever
draft path you give it, so treat calling it as the irreversible step.

Usage:
    python3 publish.py drafts/2026-07-19-edge-ai-npu.md

Requires linkedin-content/.env (gitignored) with:
    LINKEDIN_ACCESS_TOKEN=...
    LINKEDIN_PERSON_URN=urn:li:person:XXXXXXXX   (optional — auto-fetched if absent)

See SETUP.md for how to obtain these.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).parent
ENV_FILE = HERE / ".env"
LINKEDIN_API_VERSION = "202406"


def load_env():
    env = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env.setdefault(key.strip(), value.strip())
    return env


def api_request(url, token, method="GET", body=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": LINKEDIN_API_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read()
            return resp.status, json.loads(resp_body) if resp_body else {}, dict(resp.headers)
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"LinkedIn API error {e.code}: {e.read().decode(errors='replace')}"
        )


def get_person_urn(token):
    _, body, _ = api_request("https://api.linkedin.com/v2/userinfo", token)
    sub = body.get("sub")
    if not sub:
        raise SystemExit("Could not resolve person URN from /v2/userinfo response.")
    return f"urn:li:person:{sub}"


def parse_draft(path: Path) -> str:
    text = path.read_text().strip()
    if "---SOURCES---" in text:
        text = text.split("---SOURCES---")[0].strip()
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 publish.py <path-to-draft.md>")

    draft_path = Path(sys.argv[1])
    if not draft_path.exists():
        raise SystemExit(f"Draft not found: {draft_path}")

    env = load_env()
    token = env.get("LINKEDIN_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "LINKEDIN_ACCESS_TOKEN not set. Run oauth_setup.py first (see SETUP.md)."
        )

    person_urn = env.get("LINKEDIN_PERSON_URN") or get_person_urn(token)
    commentary = parse_draft(draft_path)

    if not commentary:
        raise SystemExit("Draft is empty after stripping title/sources — nothing to post.")

    print("----- ABOUT TO PUBLISH TO LINKEDIN -----")
    print(commentary)
    print("-----------------------------------------")

    body = {
        "author": person_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    status, _, headers = api_request(
        "https://api.linkedin.com/rest/posts", token, method="POST", body=body
    )
    post_id = headers.get("x-restli-id") or headers.get("X-RestLi-Id")
    print(f"Published (HTTP {status}). Post ID: {post_id}")


if __name__ == "__main__":
    main()
