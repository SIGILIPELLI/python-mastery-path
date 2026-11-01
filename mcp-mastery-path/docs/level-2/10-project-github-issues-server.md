---
description: "The capstone combines Streamable HTTP, bearer-token auth, and a real API wrapper into one deployable, container-shipped GitHub Issues MCP server."
---

# 10 · Project — A GitHub Issues MCP Server

This project pulls together everything from this level: a server reachable
over the network, protected by authentication, wrapping a real external API,
with tests and a deployable container. By the end you'll have a GitHub
Issues server someone else could actually point a client at.

## Spec

Build a Streamable HTTP MCP server, `github_issues_server.py`, exposing:

**Tools**

- `list_issues(owner: str, repo: str, state: Literal["open", "closed", "all"] = "open") -> str`
  — a one-line-per-issue summary, same shape as Lesson 7.
- `create_issue(owner: str, repo: str, title: str, body: str = "") -> IssueResult`
  — returns a structured result (use Lesson 6's structured-output pattern):
  a Pydantic model with `number: int` and `url: str`.
- `comment_on_issue(owner: str, repo: str, issue_number: int, body: str) -> str`
  — posts a comment, returns a confirmation with the comment's URL.

**Resources**

- `issue://{owner}/{repo}/{issue_number}` — a templated resource (Lesson 4's
  pattern, with three URI variables instead of one) returning the full
  issue body and metadata as text.

**Auth**

- The server requires a bearer token on every request (Lesson 3's pattern).
  For this project, a simplified scheme is acceptable: validate the
  incoming `Authorization: Bearer <token>` header against a single expected
  value read from an environment variable (`MCP_SERVER_TOKEN`), rather than
  standing up a full OAuth authorization server — note in a comment that a
  real production deployment would use the full OAuth 2.1 flow from Lesson
  3, and explain in one sentence why this simplified version is acceptable
  for a project but not for a real multi-user deployment.

**Deployment**

- A `Dockerfile` that builds and runs the server, reading `PORT`,
  `GITHUB_TOKEN`, and `MCP_SERVER_TOKEN` from the environment.
- A `/healthz` endpoint per Lesson 9.

**Tests**

- At least 4 unit tests covering `list_issues`, `create_issue`, and
  `comment_on_issue`, with the GitHub API calls mocked (Lesson 8's pattern)
  — including at least one test for an error path (GitHub returning a 4xx).

## Suggested structure

```
github-issues-mcp/
├── Dockerfile
├── requirements.txt
├── github_issues_server.py
└── test_github_issues_server.py
```

## Guided starting point

```python
# github_issues_server.py
import os
from typing import Literal
import httpx
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from starlette.responses import PlainTextResponse

mcp = FastMCP("github-issues")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
MCP_SERVER_TOKEN = os.environ["MCP_SERVER_TOKEN"]
BASE_URL = "https://api.github.com"


def gh_headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


class IssueResult(BaseModel):
    number: int
    url: str


@mcp.tool()
async def list_issues(
    owner: str, repo: str, state: Literal["open", "closed", "all"] = "open"
) -> str:
    """Lists issues for a GitHub repo."""
    # TODO: your turn — adapt Lesson 7's list_issues


@mcp.tool()
async def create_issue(owner: str, repo: str, title: str, body: str = "") -> IssueResult:
    """Creates a new GitHub issue and returns its number and URL."""
    # TODO: your turn — adapt Lesson 7's create_issue to return IssueResult


@mcp.tool()
async def comment_on_issue(owner: str, repo: str, issue_number: int, body: str) -> str:
    """Posts a comment on an existing issue."""
    # TODO: your turn — this is new; POST to
    # /repos/{owner}/{repo}/issues/{issue_number}/comments


@mcp.resource("issue://{owner}/{repo}/{issue_number}")
async def get_issue(owner: str, repo: str, issue_number: str) -> str:
    """Returns the full body and metadata of one issue."""
    # TODO: your turn — GET /repos/{owner}/{repo}/issues/{issue_number}


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request):
    return PlainTextResponse("ok")


# TODO: your turn — add bearer-token validation for MCP_SERVER_TOKEN,
# applied to every tool/resource request. Look at how FastMCP's auth
# middleware hooks in from Lesson 3 for the shape, even though you're
# checking against one fixed token instead of running a real OAuth flow.


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=int(os.environ.get("PORT", 8000)))
```

Fill in each `TODO` yourself, using the matching lesson from this level as a
reference rather than copying it verbatim — the point of this project is
building the muscle memory, not re-pasting code you've already seen.

## What "done" looks like

- `docker build` succeeds and the container starts cleanly.
- Through the Inspector (configured with the right bearer token), you can
  list issues on a real test repo, create one, comment on it, and read it
  back through the templated resource.
- A request with a missing or wrong bearer token is rejected before any
  tool runs.
- `pytest` passes, with GitHub's API fully mocked — no test should make a
  real network call.
