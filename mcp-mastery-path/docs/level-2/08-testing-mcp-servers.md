---
description: "The fastest tests call your tool functions directly in plain pytest with no protocol involved at all — the Inspector and an in-process client are for the layer above that."
---

# 08 · Testing MCP Servers (Inspector & Unit Tests)

You've been testing every server so far by poking at it manually through the
Inspector. That's the right tool for exploration — it's the wrong tool for
making sure `create_issue` still works after you refactor it next month.
This lesson covers both: deeper Inspector usage, and real automated tests.

## The Inspector, beyond "click a tool and see what happens"

A few features worth knowing:

- **History tab** — every request and response sent during the session,
  in order, with full JSON. This is the easiest way to see the exact wire
  shape of a call without writing `curl` by hand.
- **Notifications** — a separate panel for one-way messages (progress
  updates, log messages) that don't fit the request/response view.
- **Direct JSON editing** — for a tool with a complex input schema, you can
  edit the raw JSON arguments instead of filling in a generated form, which
  is faster for testing edge cases like missing required fields.

Treat the Inspector as your REPL for this protocol — reach for it the moment
something behaves unexpectedly, before reaching for print statements.

## Unit-testing the handler, with no protocol involved

The fastest, most useful tests skip the protocol layer entirely and call
your tool functions as plain Python:

```python
# test_github_server.py
import pytest
from github_server import list_issues, create_issue

@pytest.mark.asyncio
async def test_list_issues_formats_each_as_a_line(monkeypatch):
    async def fake_get(self, url, **kwargs):
        class FakeResponse:
            def raise_for_status(self): pass
            def json(self): return [
                {"number": 1, "title": "Bug A"},
                {"number": 2, "title": "Bug B"},
            ]
        return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)

    result = await list_issues(owner="acme", repo="widgets")
    assert result == "#1: Bug A\n#2: Bug B"


@pytest.mark.asyncio
async def test_list_issues_empty_state_message(monkeypatch):
    async def fake_get(self, url, **kwargs):
        class FakeResponse:
            def raise_for_status(self): pass
            def json(self): return []
        return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)

    result = await list_issues(owner="acme", repo="widgets")
    assert "No open issues" in result
```

`@mcp.tool()`-decorated functions are still plain `async def` functions
underneath — importing and calling them directly, with the actual network
call mocked out, is ordinary `pytest` with no MCP machinery involved at all.
This is where almost all of your test coverage should live: it's fast,
doesn't need a running server, and tests the logic that actually matters.

## A thin integration test, through the real protocol

For the handful of things unit tests can't catch — a tool's schema doesn't
match what you think it does, or the server fails to start at all — use the
SDK's in-process test client instead of mocking anything:

```python
# test_integration.py
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from github_server import mcp

@pytest.mark.asyncio
async def test_list_issues_tool_is_registered():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = await client.list_tools()
        names = [t.name for t in tools.tools]
        assert "list_issues" in names
        assert "create_issue" in names
```

This spins up a real client/server pair connected over an in-memory
transport — no subprocess, no network — and exercises the actual
`tools/list` request. It's slower than the unit tests above and should be a
much smaller fraction of your suite: a handful of smoke tests confirming the
server wires up correctly, not where you test business logic.

## A testing pyramid for MCP servers

1. **Most tests: plain unit tests on handler functions**, with any outside
   API fully mocked — fast, numerous, test actual behavior.
2. **A few integration tests** using the in-process client, confirming tools
   are registered with the schemas you expect and the server starts
   cleanly.
3. **Manual Inspector sessions** for exploratory testing and debugging,
   not as a substitute for either of the above.

## Exercise

Write a unit test for `create_issue` that mocks `httpx.AsyncClient.post` to
return a fake issue response, and asserts the returned string contains both
the issue number and its URL. Then write one more test confirming that if
the mocked response's `raise_for_status()` raises (simulating a 422 from
GitHub, e.g. an empty title), the exception propagates out of `create_issue`
rather than being silently swallowed.
