---
description: "The capstone combines everything from this level: tools that mutate state, a resource that reads it back, and JSON-file persistence across restarts."
---

# 10 · Project — A Local Notes/Tasks MCP Server

This project pulls together everything from Level 1: tools, a resource, and
a real connection to Claude Desktop, applied to a small but genuinely useful
server — a notes/tasks manager backed by a local JSON file.

## Spec

Build a server named `notes-server` with these three tools and one
resource:

**`add_note(text: str) -> dict`**
Adds a new note with the given text. Generates a unique ID (an incrementing
integer is fine), stores it as not-yet-complete, and returns the full note
record as a dict: `{"id": ..., "text": ..., "done": False}`.

**`list_notes(include_done: bool = True) -> list[dict]`**
Returns all stored notes as a list of records. When `include_done=False`,
filters out notes already marked done.

**`complete_note(note_id: int) -> dict`**
Marks the note with the given ID as done (`"done": True`) and returns the
updated record. If no note with that ID exists, return a dict like
`{"error": f"No note with id {note_id}"}` instead of raising — tool results
should communicate failure as data the model can read and relay, not as an
unhandled exception.

**Resource `notes://all`**
Returns all notes rendered as a single markdown document — one line per
note, something like:

```text
- [ ] Buy groceries (#1)
- [x] Call the dentist (#2)
```

## Persistence

Notes must survive a server restart, so store them in a JSON file on disk
(e.g. `notes.json` next to your server script) rather than only in memory.
A reasonable structure:

```python
import json
from pathlib import Path

NOTES_FILE = Path(__file__).parent / "notes.json"

def load_notes() -> list[dict]:
    if not NOTES_FILE.exists():
        return []
    return json.loads(NOTES_FILE.read_text())

def save_notes(notes: list[dict]) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2))
```

Each tool should load the current notes, make its change, save, and return
the relevant result — you decide the exact shape of `load_notes` /
`save_notes` and how `add_note` picks the next ID (the highest existing ID
plus one is a reasonable approach, since IDs may not always start at 1 after
notes get removed in a future version of this server).

## Build it

Scaffold the server the same way as lesson 4, with the three
`@mcp.tool()`-decorated functions and one `@mcp.resource("notes://all")`
function described above, wired to the persistence functions. The core
server setup (`FastMCP("notes-server")`, the `if __name__ == "__main__":
mcp.run()` block) is exactly what you've already built twice this level —
reuse it rather than re-deriving it.

## Verify it end to end

1. In the MCP Inspector, call `add_note` two or three times with different
   text, then `list_notes()` and confirm all of them come back.
2. Call `complete_note` on one of the IDs, then `list_notes(include_done=False)`
   and confirm the completed one is filtered out while it still shows up
   with `include_done=True`.
3. Read the `notes://all` resource and confirm the markdown checklist
   format matches what you'd expect from the current state.
4. Restart the Inspector (which restarts your server process) and confirm
   `list_notes()` still returns the same notes — proving the JSON file
   persistence actually works, not just the in-memory state of a single run.
5. Register it in `claude_desktop_config.json` per lesson 9, restart Claude
   Desktop, and ask it to add a note and then list your notes, in a real
   conversation.

## Exercise

Extend the server with a fourth tool, `delete_note(note_id: int) -> dict`,
that removes a note entirely (not just marks it done) and returns either
the removed record or an error dict if the ID doesn't exist — matching the
same not-found-as-data convention `complete_note` uses. Confirm it works in
the Inspector, including the case of deleting an ID that was never added.
