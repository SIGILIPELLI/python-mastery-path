---
description: "The cheapest time to design a tool's permission scope is before you write it — splitting a 'manage_issues' tool into separate read and write tools after the fact means auditing every existing caller."
---

# 07 · Scopes, Permissions & Least Privilege

The previous lesson named least privilege as the single most effective
structural defense against a successful prompt injection or tool-poisoning
attack doing real damage. This lesson is about actually designing for it —
deliberately, at the point you define a server's tools, rather than bolting
restrictions on afterward.

## Read-only vs. write/destructive, as a first split

The single highest-leverage design decision is separating tools that only
read from tools that change state, and being honest with yourself about
which category each one is in:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github-server")

# read-only: safe to call freely, safe to retry, low blast radius
@mcp.tool()
async def list_issues(repo: str) -> list[dict]:
    """List open issues. Read-only."""
    ...

@mcp.tool()
async def get_issue(repo: str, issue_number: int) -> dict:
    """Read-only."""
    ...

# write/destructive: changes external state, needs more scrutiny
@mcp.tool()
async def create_issue(repo: str, title: str, body: str) -> dict:
    """Creates a new issue. Not idempotent — calling twice creates two issues."""
    ...

@mcp.tool()
async def close_issue(repo: str, issue_number: int) -> dict:
    """Destructive in the sense that it changes state other users can see."""
    ...
```

This isn't just documentation — it's the basis for every other control in
this lesson. A host can route read-only tools straight through and reserve
confirmation gates for the write/destructive set, exactly the
`SENSITIVE_TOOLS` pattern from the previous lesson.

## Scoping credentials to what the server actually does

If your server only ever calls `list_issues` and `get_issue`-style
endpoints, the token it holds should be a read-only token — not the same
admin token you'd need for `close_issue`, even if it's more convenient to
provision one token for everything up front.

```python
import os

# two separate env vars, two separate tokens with different GitHub scopes
READ_TOKEN = os.environ["GITHUB_READ_TOKEN"]   # scope: repo:read
WRITE_TOKEN = os.environ.get("GITHUB_WRITE_TOKEN")  # scope: repo (full) — only set if write tools are enabled

@mcp.tool()
async def list_issues(repo: str) -> list[dict]:
    return await github_api_call(repo, "issues", token=READ_TOKEN, method="GET")

@mcp.tool()
async def create_issue(repo: str, title: str, body: str) -> dict:
    if not WRITE_TOKEN:
        return {"error": "This server is configured read-only"}
    return await github_api_call(repo, "issues", token=WRITE_TOKEN, method="POST",
                                   data={"title": title, "body": body})
```

A server deployed with only `GITHUB_READ_TOKEN` set simply *cannot* create
or close issues, no matter what instruction reaches the model — not
because of application logic that might have a bug, but because the
credential it holds doesn't have the permission. That's a strictly stronger
guarantee than "the code checks a flag before allowing writes."

## Per-tool consent: a host-side responsibility

A well-behaved host should let a user approve tools at a granularity finer
than "trust this entire server or don't connect to it." A reasonable
default policy:

```python
class ToolApprovalPolicy:
    def __init__(self):
        self.always_allow: set[str] = set()   # user said "always allow" previously
        self.always_deny: set[str] = set()

    async def should_call(self, tool_name: str, risk_level: str, confirm_fn) -> bool:
        if tool_name in self.always_deny:
            return False
        if tool_name in self.always_allow:
            return True
        if risk_level == "read_only":
            return True  # no prompt needed for low-risk tools
        # write/destructive: ask every time unless the user opts into "always allow"
        decision = await confirm_fn(tool_name)
        if decision == "always":
            self.always_allow.add(tool_name)
        return decision in ("yes", "always")
```

This mirrors how mobile OS permission models work for a reason: "allow
once," "always allow," and "never allow" give the user real control without
asking them to re-approve a safe, read-only action every single time.

## Scoping by *resource*, not just by tool

Least privilege doesn't stop at "can this server create issues at all" — a
server with write access to one specific repository shouldn't
automatically have write access to every repository the underlying token
could technically reach. Where the underlying API supports it (GitHub
fine-grained personal access tokens, for instance), scope the credential to
the specific resource the server is meant to operate on:

```python
ALLOWED_REPOS = {"myorg/project-a"}  # explicit allow-list, not "whatever the token can reach"

@mcp.tool()
async def create_issue(repo: str, title: str, body: str) -> dict:
    if repo not in ALLOWED_REPOS:
        return {"error": f"This server is only configured for: {ALLOWED_REPOS}"}
    ...
```

This is the same pattern as roots from the previous lesson, applied to an
API-backed resource instead of a filesystem — explicit allow-lists checked
in code, backed by a credential that can't exceed them even if the check
were somehow bypassed.

## Exercise

Take the GitHub server sketch above and add a third tier: a
`delete_repository`-style tool (destructive and essentially
non-reversible). Design — in code, not just comments — a policy where this
specific tool requires a *different, explicit* confirmation flow than the
regular write tools (e.g. typing the repository name to confirm, the way
GitHub's own UI does for repo deletion), on top of the normal
`ToolApprovalPolicy` check. Explain in a short comment why a single
"always allow" toggle is the wrong UX for this particular tool.
