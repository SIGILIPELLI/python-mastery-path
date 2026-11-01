---
description: "Wrapping a real REST API as MCP tools is mostly about hiding its auth, pagination and rate limits behind a handful of clean, model-friendly function signatures."
---

# 07 · Wrapping a Real API: GitHub as an MCP Server

Most MCP servers you'll build at work aren't inventing new functionality —
they're exposing an API that already exists, in a shape a model can call
safely. GitHub's REST API is a good real target: well-documented, widely
useful, and realistic about the things you actually have to handle (auth,
rate limits, pagination).

## Setup

```bash
pip install "mcp[cli]" httpx
export GITHUB_TOKEN="ghp_..."   # a personal access token with repo scope
```

```python
# github_server.py
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github-tools")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
BASE_URL = "https://api.github.com"

def gh_headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
```

Pulling the token from an environment variable, not a hardcoded string or a
tool parameter, keeps the credential out of chat context entirely — the
model never sees it, and it never ends up in a conversation log.

## Listing issues

```python
@mcp.tool()
async def list_issues(owner: str, repo: str, state: str = "open") -> str:
    """Lists issues for a GitHub repo. state is 'open', 'closed', or 'all'."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/repos/{owner}/{repo}/issues",
            headers=gh_headers(),
            params={"state": state, "per_page": 20},
        )
        resp.raise_for_status()
        issues = resp.json()

    if not issues:
        return f"No {state} issues in {owner}/{repo}."

    lines = [f"#{i['number']}: {i['title']}" for i in issues]
    return "\n".join(lines)
```

## Creating an issue

```python
@mcp.tool()
async def create_issue(owner: str, repo: str, title: str, body: str = "") -> str:
    """Creates a new issue in a GitHub repo."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/repos/{owner}/{repo}/issues",
            headers=gh_headers(),
            json={"title": title, "body": body},
        )
        resp.raise_for_status()
        issue = resp.json()

    return f"Created issue #{issue['number']}: {issue['html_url']}"
```

## Handling rate limits

GitHub returns rate-limit information in response headers on every request
— don't wait to hit a 403 to find out you're close to the limit:

```python
async def gh_request(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    resp = await client.request(method, url, headers=gh_headers(), **kwargs)
    remaining = int(resp.headers.get("x-ratelimit-remaining", "1"))
    if remaining < 5:
        reset_at = resp.headers.get("x-ratelimit-reset")
        raise RuntimeError(
            f"GitHub rate limit nearly exhausted ({remaining} left, resets at {reset_at})."
        )
    resp.raise_for_status()
    return resp
```

Route both tools above through this helper instead of calling `client.get`/
`client.post` directly, and a model that tries to hammer the API in a tight
loop gets a clear error — "rate limit nearly exhausted" — instead of GitHub
silently throttling or blocking the underlying token.

## What makes this a *good* API wrapper, not just a thin proxy

- **Tool names and descriptions describe intent** (`create_issue`), not raw
  endpoints (`POST /repos/{owner}/{repo}/issues`) — the model shouldn't need
  to know GitHub's URL structure to use this server.
- **Only expose what's actually safe to expose.** This server deliberately
  has no `delete_repo` tool — not every endpoint an API offers belongs in
  front of a model.
- **Summarized, not raw, responses.** `list_issues` returns a short text
  summary instead of dumping GitHub's full, deeply nested JSON response —
  that raw payload would burn a lot of the model's context for little
  benefit.

## Exercise

Add a `comment_on_issue(owner: str, repo: str, issue_number: int, body: str)`
tool using GitHub's `POST /repos/{owner}/{repo}/issues/{issue_number}/comments`
endpoint, routed through the `gh_request` rate-limit helper. Test it end to
end against a real (preferably disposable/test) repository through the
Inspector: list issues, pick one, comment on it, then list issues again and
confirm the comment count changed.
