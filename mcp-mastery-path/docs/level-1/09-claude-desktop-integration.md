---
description: "claude_desktop_config.json registers a local server under mcpServers with just a command and args — Claude Desktop spawns it exactly like the Inspector does."
---

# 09 · Connecting Your Server to Claude Desktop

Everything so far has run through the MCP Inspector. This lesson connects
the same server to a real host application — Claude Desktop — so you can
use it in an actual conversation.

## The config file

Claude Desktop reads its MCP server list from a JSON config file,
`claude_desktop_config.json`, located at:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

If the file doesn't exist yet, create it. The relevant shape is an
`mcpServers` object, where each key is a name you choose for the server and
each value describes how to launch it:

```json
{
  "mcpServers": {
    "demo-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

`command` is the executable to run, `args` is the list of arguments passed
to it — together they're exactly the subprocess invocation Claude Desktop
will spawn, the same way the Inspector spawned `python server.py` in lesson
4. **Use an absolute path** to `server.py`; Claude Desktop doesn't
necessarily launch the process from the directory you expect.

## Environment variables, if your server needs them

If your server reads an API key or other config from the environment, add
an `env` object alongside `command` and `args`:

```json
{
  "mcpServers": {
    "demo-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "SOME_API_KEY": "your-key-here"
      }
    }
  }
}
```

Your server doesn't need any special code to read this — it's set on the
subprocess's environment exactly like any other environment variable, so
plain `os.environ["SOME_API_KEY"]` in your server picks it up.

## Restart and verify

Config changes aren't picked up live — **fully quit and reopen** Claude
Desktop (not just close the window) for it to re-read the file and spawn
your server. If the config is valid and the server starts cleanly, you'll
see a small tools/MCP indicator in the Claude Desktop UI; clicking it should
list `demo-server` and its tools.

If it doesn't show up, check Claude Desktop's MCP log file (also under the
same per-OS config directory, typically named something like
`mcp-server-demo-server.log`) — this captures anything your server wrote to
stderr plus any startup failures, and is almost always where the actual
error message is.

## Use it for real

Open a new conversation and ask something that requires the tool you built,
for example, if you still have the `add` tool from lesson 4: "What's 47
plus 128? Use the add tool." Claude Desktop's host will present your tool
to the model, the model will issue a `tools/call` exactly as you saw in the
Inspector, and you'll get a real answer computed by your own code running
on your own machine — not by the model doing arithmetic itself.

## Exercise

Register the notes/tasks server you'll build in lesson 10's project ahead
of time by adding a second entry to `mcpServers` right now, pointing at a
`notes_server.py` path that doesn't exist yet. Confirm Claude Desktop
reports a startup failure for that entry in its log (rather than silently
ignoring it) — this is exactly the error you'll want to recognize once
you've actually built that server and are debugging why it isn't showing
up.
