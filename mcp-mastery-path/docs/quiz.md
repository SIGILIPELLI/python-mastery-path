---
title: "Final Quiz"
description: "Test what you have learned across all four levels of MCP Mastery Path with a 21-question final quiz."
---

# Final Quiz

21 questions drawn from all four levels of this course. You need **70% (15 out of 21)** to pass —
you can retake it as many times as you like. Your best result is saved in this browser.

<div id="mp-quiz-root"></div>

<script type="application/json" id="mp-quiz-data">
[
  {
    "question": "6 AI applications and 9 tools: how many integrations are needed without MCP and with MCP?\n```python\napps, tools = 6, 9\nprint(apps * tools, apps + tools)\n```\n",
    "options": [
      "9 6",
      "15 54",
      "54 15",
      "54 54"
    ],
    "correctIndex": 2,
    "explanation": "Without a shared protocol each app integrates each tool (M x N); with MCP each side implements the protocol once (M + N). Verified by running it."
  },
  {
    "question": "Which of these three messages is a notification?\n```python\nmsgs = [{'id': 1, 'method': 'tools/list'}, {'id': 1, 'result': {}}, {'method': 'notifications/initialized'}]\nprint([i for i, m in enumerate(msgs) if 'method' in m and 'id' not in m])\n```\n",
    "options": [
      "[2]",
      "[0]",
      "[1]",
      "[0, 2]"
    ],
    "correctIndex": 0,
    "explanation": "A notification has a method but no id, so no reply is expected. Verified by running it."
  },
  {
    "question": "A host connects to four MCP servers. How many MCP client instances does it hold?",
    "options": [
      "Four servers share one pipe, so one client",
      "Two",
      "One shared client",
      "Four, one per server, because each client has a strict 1:1 relationship with one server"
    ],
    "correctIndex": 3,
    "explanation": "The aggregation of capabilities is host-layer code above the clients."
  },
  {
    "question": "What does list_tools report for this tool's required arguments?\n```python\nimport asyncio\nfrom mcp.server.fastmcp import FastMCP\nmcp = FastMCP('demo')\n@mcp.tool()\ndef add(a: int, b: int = 2) -> int:\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\nprint(asyncio.run(mcp.list_tools())[0].inputSchema['required'])\n```\n",
    "options": [
      "['b']",
      "['a']",
      "[]",
      "['a', 'b']"
    ],
    "correctIndex": 1,
    "explanation": "Only parameters without defaults are required, and the schema is generated from the type hints. Verified by running it against the real MCP Python SDK (mcp 1.30)."
  },
  {
    "question": "Who normally triggers an MCP prompt?",
    "options": [
      "The model on its own",
      "The user, who picks it by name such as a slash command",
      "The transport",
      "The server on a timer"
    ],
    "correctIndex": 1,
    "explanation": "Tools are model-controlled and resources application-controlled; prompts are user-triggered."
  },
  {
    "question": "Why must a stdio server never print() to stdout?",
    "options": [
      "stdout is the JSON-RPC channel, so stray text corrupts the stream; log to stderr instead",
      "stdout is closed",
      "It would be shown to the user twice",
      "print is slow"
    ],
    "correctIndex": 0,
    "explanation": "The client fails to parse the stray line and can lose sync on the next message."
  },
  {
    "question": "How is a local server registered with Claude Desktop?",
    "options": [
      "Through the model's settings",
      "In a .env file",
      "Under mcpServers in claude_desktop_config.json with a command and args, using an absolute path, then fully restarting the app",
      "With a URL only"
    ],
    "correctIndex": 2,
    "explanation": "The host spawns it exactly as the Inspector would."
  },
  {
    "question": "What is the default Streamable HTTP endpoint of a Python FastMCP server?\n```python\nfrom mcp.server.fastmcp import FastMCP\ns = FastMCP('x').settings\nprint(f'http://{s.host}:{s.port}{s.streamable_http_path}')\n```\n",
    "options": [
      "http://0.0.0.0:80/",
      "http://localhost:8080/rpc",
      "http://127.0.0.1:8000/mcp",
      "http://127.0.0.1:3000/sse"
    ],
    "correctIndex": 2,
    "explanation": "A single endpoint handles POST for client messages and GET for the SSE stream. Verified by running it against the real MCP Python SDK (mcp 1.30)."
  },
  {
    "question": "How does a remote MCP server authenticate its callers per the spec?",
    "options": [
      "OAuth 2.1, with the client sending Authorization: Bearer <token> on every request",
      "It does not, since the user trusts it",
      "Basic auth in the URL",
      "A model-generated password"
    ],
    "correctIndex": 0,
    "explanation": "A stdio server is trusted because the user chose to launch it; a remote one has no such guarantee."
  },
  {
    "question": "How does a resource template appear to a client?\n```python\nimport asyncio\nfrom mcp.server.fastmcp import FastMCP\nmcp = FastMCP('n')\n@mcp.resource('notes://{note_id}')\ndef get_note(note_id: str) -> str:\n    \"\"\"One note.\"\"\"\n    return 'text'\nprint([t.uriTemplate for t in asyncio.run(mcp.list_resource_templates())], asyncio.run(mcp.list_resources()))\n```\n",
    "options": [
      "['notes://{note_id}'] ['notes://{note_id}']",
      "[] ['notes://1']",
      "['notes://{note_id}'] []",
      "[] []"
    ],
    "correctIndex": 2,
    "explanation": "A template shows up in resources/templates/list as a pattern, not in resources/list. Verified by running it against the real MCP Python SDK (mcp 1.30)."
  },
  {
    "question": "What is distinctive about sampling?",
    "options": [
      "The server asks the client's LLM to generate text, so the server needs no model or key of its own, and the user stays in the loop",
      "It runs only in the Inspector",
      "It replaces authentication",
      "The client asks the server for a tool"
    ],
    "correctIndex": 0,
    "explanation": "sampling/createMessage flips the usual direction."
  },
  {
    "question": "What does a Literal type become in a tool's input schema?\n```python\nimport asyncio\nfrom typing import Literal\nfrom mcp.server.fastmcp import FastMCP\nmcp = FastMCP('t')\n@mcp.tool()\ndef create_ticket(priority: Literal['low', 'high']) -> str:\n    \"\"\"Create.\"\"\"\n    return 'ok'\nprint(asyncio.run(mcp.list_tools())[0].inputSchema['properties']['priority']['enum'])\n```\n",
    "options": [
      "['low', 'high']",
      "['priority']",
      "[]",
      "['string']"
    ],
    "correctIndex": 0,
    "explanation": "An enum stops the model sending a value that was never valid. Verified by running it against the real MCP Python SDK (mcp 1.30)."
  },
  {
    "question": "What is the fastest way to unit-test a tool handler?\n```python\nfrom mcp.server.fastmcp import FastMCP\nmcp = FastMCP('t')\n@mcp.tool()\ndef add(a: int, b: int) -> int:\n    \"\"\"Add.\"\"\"\n    return a + b\nassert add(2, 3) == 5\nprint('plain function call, no protocol')\n```\n",
    "options": [
      "open a browser",
      "plain function call, no protocol",
      "run a subprocess",
      "start the Inspector"
    ],
    "correctIndex": 1,
    "explanation": "The decorator returns the original function, so ordinary pytest can call it directly. Verified by running it against the real MCP Python SDK (mcp 1.30)."
  },
  {
    "question": "Two servers both expose search. How do you keep both reachable?\n```python\ncatalog = {'docs': ['search'], 'tickets': ['search']}\nprint(sorted(f'{s}__{t}' for s, ts in catalog.items() for t in ts))\n```\n",
    "options": [
      "['search']",
      "['docs', 'tickets']",
      "['search__docs', 'search__tickets']",
      "['docs__search', 'tickets__search']"
    ],
    "correctIndex": 3,
    "explanation": "Prefixing each tool with its server name avoids a silent overwrite. Verified by running it."
  },
  {
    "question": "What does the client see when a tool raises an exception?\n```python\nimport asyncio\nfrom mcp.server.fastmcp import FastMCP\nfrom mcp.shared.memory import create_connected_server_and_client_session as connect\nmcp = FastMCP('t')\n@mcp.tool()\ndef boom() -> str:\n    \"\"\"Fails.\"\"\"\n    raise RuntimeError('no such file')\nasync def main():\n    async with connect(mcp._mcp_server) as c:\n        r = await c.call_tool('boom', {})\n        print(r.isError)\nasyncio.run(main())\n```\n",
    "options": [
      "It raises in the client",
      "None",
      "False",
      "True"
    ],
    "correctIndex": 3,
    "explanation": "The failure comes back as a normal result with isError true so the model can read it and decide what to do. Verified by running it against the real MCP Python SDK (mcp 1.30)."
  },
  {
    "question": "Who chooses the progressToken for a progress notification?",
    "options": [
      "The client; the server echoes it back so progress can be matched to the call",
      "The server",
      "The model",
      "The transport"
    ],
    "correctIndex": 0,
    "explanation": "report_progress sends notifications/progress with the client's token."
  },
  {
    "question": "Are roots enforced by the protocol?",
    "options": [
      "Only on Windows",
      "No, they are advisory; a well-behaved server checks them, so also restrict the process at the operating-system level",
      "Yes, the transport enforces them",
      "Yes, the client enforces them"
    ],
    "correctIndex": 1,
    "explanation": "A malicious server can ignore them."
  },
  {
    "question": "A tool's description tells the model to also read .env files. What is this attack called?",
    "options": [
      "Session affinity",
      "Rate limiting",
      "Elicitation",
      "Tool poisoning, delivered through the tool's own description"
    ],
    "correctIndex": 3,
    "explanation": "Connecting to a server is a trust decision about its author."
  },
  {
    "question": "Which design best limits the damage of a successful injection?",
    "options": [
      "Separate read and write tools with separate least-privilege credentials, and an approval gate on state-changing tools",
      "Hiding tool names",
      "Removing all descriptions",
      "One admin token for everything"
    ],
    "correctIndex": 0,
    "explanation": "Least privilege is the structural defence."
  },
  {
    "question": "Which tool calls are safe to cache?",
    "options": [
      "create_issue",
      "Read-only, idempotent ones such as get_issue or search, with an explicit allow-list and a short TTL",
      "Only tools with side effects",
      "Everything by default"
    ],
    "correctIndex": 1,
    "explanation": "A cached create_issue is a bug, not an optimisation."
  },
  {
    "question": "Why do the lessons tell you to install the SDK as mcp<2?",
    "options": [
      "Because mcp<2 is faster",
      "mcp 2.x removes stdio",
      "Pip refuses newer versions",
      "In mcp 2.x the module mcp.server.fastmcp no longer exists (FastMCP was renamed MCPServer), so the course's 1.x code raises ModuleNotFoundError"
    ],
    "correctIndex": 3,
    "explanation": "The code in this course and the verification of these quizzes use the 1.x API (tested with 1.30)."
  }
]
</script>

## Coding challenges

Try these on your own computer, then compare your output. Nothing you write is sent anywhere.

### A notes MCP server tested with a real in-memory client

Build the Level 1 notes server with the real MCP Python SDK: three tools and a resource that renders the notes as a markdown checklist. Unknown ids are returned as data, not raised. The script talks to its own server through an in-memory client, so it runs with no Inspector and no network. Install with pip install "mcp<2" (written against the 1.x API and tested with mcp 1.30).

**Starter code**

```python
import asyncio, json
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session as connect

mcp = FastMCP("notes-server")
NOTES = []

# TODO: add_note(text) -> dict {"id", "text", "done": False}; the id is the highest existing id + 1 (1 when empty)
# TODO: list_notes(include_done=True) -> list of notes, hiding done ones when include_done is False
# TODO: complete_note(note_id) -> the updated note, or {"error": "No note with id N"} (return it, do not raise)
# TODO: a resource notes://all returning a markdown checklist: "- [ ] text (#id)" or "- [x] text (#id)"

async def call(client, name, args):
    result = await client.call_tool(name, args)
    return [json.loads(block.text) for block in result.content]   # one JSON block per returned item

async def main():
    async with connect(mcp._mcp_server) as client:
        print([t.name for t in (await client.list_tools()).tools])
        print(await call(client, "add_note", {"text": "Buy groceries"}))
        print(await call(client, "add_note", {"text": "Call the dentist"}))
        print(await call(client, "complete_note", {"note_id": 2}))
        print(await call(client, "complete_note", {"note_id": 9}))
        print(await call(client, "list_notes", {"include_done": False}))
        print((await client.read_resource("notes://all")).contents[0].text)

asyncio.run(main())
```

**Expected output**

```text
['add_note', 'list_notes', 'complete_note']
[{'id': 1, 'text': 'Buy groceries', 'done': False}]
[{'id': 2, 'text': 'Call the dentist', 'done': False}]
[{'id': 2, 'text': 'Call the dentist', 'done': True}]
[{'error': 'No note with id 9'}]
[{'id': 1, 'text': 'Buy groceries', 'done': False}]
- [ ] Buy groceries (#1)
- [x] Call the dentist (#2)
```

<details><summary>Show solution and explanation</summary>

<pre><code>import asyncio, json
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session as connect

mcp = FastMCP(&quot;notes-server&quot;)
NOTES = []

@mcp.tool()
def add_note(text: str) -&gt; dict:
    &quot;&quot;&quot;Add a note and return the stored record.&quot;&quot;&quot;
    note = {&quot;id&quot;: max((n[&quot;id&quot;] for n in NOTES), default=0) + 1, &quot;text&quot;: text, &quot;done&quot;: False}
    NOTES.append(note)
    return note

@mcp.tool()
def list_notes(include_done: bool = True) -&gt; list[dict]:
    &quot;&quot;&quot;List notes, optionally hiding the ones already done.&quot;&quot;&quot;
    return [n for n in NOTES if include_done or not n[&quot;done&quot;]]

@mcp.tool()
def complete_note(note_id: int) -&gt; dict:
    &quot;&quot;&quot;Mark a note as done. Unknown ids are reported as data, not raised.&quot;&quot;&quot;
    for n in NOTES:
        if n[&quot;id&quot;] == note_id:
            n[&quot;done&quot;] = True
            return n
    return {&quot;error&quot;: f&quot;No note with id {note_id}&quot;}

@mcp.resource(&quot;notes://all&quot;)
def all_notes() -&gt; str:
    &quot;&quot;&quot;Every note as a markdown checklist.&quot;&quot;&quot;
    return &quot;\n&quot;.join(f&quot;- [{&#x27;x&#x27; if n[&#x27;done&#x27;] else &#x27; &#x27;}] {n[&#x27;text&#x27;]} (#{n[&#x27;id&#x27;]})&quot; for n in NOTES)

async def call(client, name, args):
    result = await client.call_tool(name, args)
    return [json.loads(block.text) for block in result.content]   # one JSON block per returned item

async def main():
    async with connect(mcp._mcp_server) as client:
        print([t.name for t in (await client.list_tools()).tools])
        print(await call(client, &quot;add_note&quot;, {&quot;text&quot;: &quot;Buy groceries&quot;}))
        print(await call(client, &quot;add_note&quot;, {&quot;text&quot;: &quot;Call the dentist&quot;}))
        print(await call(client, &quot;complete_note&quot;, {&quot;note_id&quot;: 2}))
        print(await call(client, &quot;complete_note&quot;, {&quot;note_id&quot;: 9}))
        print(await call(client, &quot;list_notes&quot;, {&quot;include_done&quot;: False}))
        print((await client.read_resource(&quot;notes://all&quot;)).contents[0].text)

asyncio.run(main())
</code></pre>

<p>The highest id plus one keeps ids unique, complete_note reports a missing id as a normal result the model can read, and list_notes(include_done=False) hides finished notes. The resource turns the same state into a markdown checklist. Run against the real MCP Python SDK 1.30 and its output checked.</p>
</details>

### A gateway with namespacing, an approval gate and an audit log

Build the core of the Level 4 gateway in front of two real in-memory MCP servers that both expose a tool called search. Register every tool as server__tool, deny a sensitive tool unless approved without calling the backend, report a failing backend call as an error outcome and record every outcome in an audit list. Install with pip install "mcp<2" (tested with mcp 1.30).

**Starter code**

```python
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session as connect

docs = FastMCP("docs")
@docs.tool()
def search(query: str) -> str:
    """Search the documentation."""
    return f"3 results for {query}"

tickets = FastMCP("tickets")
@tickets.tool()
def search(query: str) -> str:
    """Search tickets."""
    return f"1 ticket matching {query}"
@tickets.tool()
def close_ticket(ticket_id: int) -> str:
    """Close a ticket."""
    if ticket_id != 7:
        raise ValueError(f"no ticket {ticket_id}")
    return "closed 7"

SENSITIVE = {"tickets__close_ticket"}

class Gateway:
    # TODO: load(): for every session, list its tools and register them as "<server>__<tool>" -> (server, tool)
    # TODO: call(full_name, arguments, caller, approved=False):
    #   unknown name        -> log "error" with text "unknown tool"
    #   name in SENSITIVE and not approved -> log "denied" with text "approval required" (do not call the backend)
    #   otherwise call the backend tool; log "success", or "error" when the result has isError
    #   every outcome is appended to self.audit as "<caller> <name> <outcome>" and returned as "<outcome>: <text>"
    pass

async def main():
    async with connect(docs._mcp_server) as d, connect(tickets._mcp_server) as t:
        gw = Gateway({"docs": d, "tickets": t})
        await gw.load()
        print(sorted(gw.catalog))
        print(await gw.call("docs__search", {"query": "oauth"}, "alice"))
        print(await gw.call("tickets__search", {"query": "vpn"}, "alice"))
        print(await gw.call("tickets__close_ticket", {"ticket_id": 7}, "bob"))
        print(await gw.call("tickets__close_ticket", {"ticket_id": 7}, "bob", approved=True))
        print(await gw.call("tickets__close_ticket", {"ticket_id": 99}, "bob", approved=True))
        print(await gw.call("search", {"query": "x"}, "carol"))
        print(*gw.audit, sep="\n")

asyncio.run(main())
```

**Expected output**

```text
['docs__search', 'tickets__close_ticket', 'tickets__search']
success: 3 results for oauth
success: 1 ticket matching vpn
denied: approval required
success: closed 7
error: Error executing tool close_ticket: no ticket 99
error: unknown tool
alice docs__search success
alice tickets__search success
bob tickets__close_ticket denied
bob tickets__close_ticket success
bob tickets__close_ticket error
carol search error
```

<details><summary>Show solution and explanation</summary>

<pre><code>import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session as connect

docs = FastMCP(&quot;docs&quot;)
@docs.tool()
def search(query: str) -&gt; str:
    &quot;&quot;&quot;Search the documentation.&quot;&quot;&quot;
    return f&quot;3 results for {query}&quot;

tickets = FastMCP(&quot;tickets&quot;)
@tickets.tool()
def search(query: str) -&gt; str:
    &quot;&quot;&quot;Search tickets.&quot;&quot;&quot;
    return f&quot;1 ticket matching {query}&quot;
@tickets.tool()
def close_ticket(ticket_id: int) -&gt; str:
    &quot;&quot;&quot;Close a ticket.&quot;&quot;&quot;
    if ticket_id != 7:
        raise ValueError(f&quot;no ticket {ticket_id}&quot;)
    return &quot;closed 7&quot;

SENSITIVE = {&quot;tickets__close_ticket&quot;}

class Gateway:
    def __init__(self, sessions):
        self.sessions, self.catalog, self.audit = sessions, {}, []

    async def load(self):
        for server, session in self.sessions.items():
            for tool in (await session.list_tools()).tools:
                self.catalog[f&quot;{server}__{tool.name}&quot;] = (server, tool.name)

    def _log(self, name, caller, text, outcome):
        self.audit.append(f&quot;{caller} {name} {outcome}&quot;)
        return f&quot;{outcome}: {text}&quot;

    async def call(self, full_name, arguments, caller, approved=False):
        if full_name not in self.catalog:
            return self._log(full_name, caller, &quot;unknown tool&quot;, &quot;error&quot;)
        if full_name in SENSITIVE and not approved:
            return self._log(full_name, caller, &quot;approval required&quot;, &quot;denied&quot;)
        server, tool = self.catalog[full_name]
        result = await self.sessions[server].call_tool(tool, arguments)
        return self._log(full_name, caller, result.content[0].text, &quot;error&quot; if result.isError else &quot;success&quot;)

async def main():
    async with connect(docs._mcp_server) as d, connect(tickets._mcp_server) as t:
        gw = Gateway({&quot;docs&quot;: d, &quot;tickets&quot;: t})
        await gw.load()
        print(sorted(gw.catalog))
        print(await gw.call(&quot;docs__search&quot;, {&quot;query&quot;: &quot;oauth&quot;}, &quot;alice&quot;))
        print(await gw.call(&quot;tickets__search&quot;, {&quot;query&quot;: &quot;vpn&quot;}, &quot;alice&quot;))
        print(await gw.call(&quot;tickets__close_ticket&quot;, {&quot;ticket_id&quot;: 7}, &quot;bob&quot;))
        print(await gw.call(&quot;tickets__close_ticket&quot;, {&quot;ticket_id&quot;: 7}, &quot;bob&quot;, approved=True))
        print(await gw.call(&quot;tickets__close_ticket&quot;, {&quot;ticket_id&quot;: 99}, &quot;bob&quot;, approved=True))
        print(await gw.call(&quot;search&quot;, {&quot;query&quot;: &quot;x&quot;}, &quot;carol&quot;))
        print(*gw.audit, sep=&quot;\n&quot;)

asyncio.run(main())
</code></pre>

<p>Namespacing keeps both search tools reachable and lets the gateway route to the right backend with the original tool name. The approval gate runs before any backend call, the isError result becomes an error outcome instead of a crash, and every decision lands in the audit list with who asked. Run against the real MCP Python SDK 1.30 and its output checked.</p>
</details>
