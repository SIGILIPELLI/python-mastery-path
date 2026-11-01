---
description: "Every tool definition you send costs context window and latency on every single turn — a 15-server setup with no trimming can burn thousands of tokens before the model reads your actual question."
---

# 02 · Tool Selection & Namespacing at Scale

Connect three servers and tool names mostly stay readable: `add_note`,
`list_issues`, `web_search`. Connect twelve, and you'll hit two very
different problems at once: names collide (two servers both expose a tool
called `search`), and the combined tool list becomes large enough to hurt
both latency and the model's ability to pick the right tool. This lesson is
about both.

## The collision problem

Picking up the tool index from the previous lesson:

```python
def build_tool_index(catalog: dict[str, list]) -> dict[str, str]:
    index = {}
    for server_name, tools in catalog.items():
        for tool in tools:
            index[tool.name] = server_name  # silently overwrites on collision!
    return index
```

If `notes` and `github` both register a tool called `search`, whichever
server is processed last in the loop silently wins, and the other server's
`search` tool becomes permanently unreachable — with no error, no warning,
nothing in the logs. This is the kind of bug that works perfectly in every
test with two servers and breaks the moment someone adds a third.

## Namespacing: prefix by server

The straightforward fix is to never expose raw tool names across server
boundaries — always prefix with the server name at the point where you
build the model-facing catalog:

```python
NAMESPACE_SEP = "__"  # double underscore reads cleanly and rarely collides with real names

def build_namespaced_catalog(catalog: dict[str, list]) -> dict[str, dict]:
    """Returns {namespaced_name: {"server": server_name, "tool": original_tool}}"""
    namespaced = {}
    for server_name, tools in catalog.items():
        for tool in tools:
            full_name = f"{server_name}{NAMESPACE_SEP}{tool.name}"
            namespaced[full_name] = {"server": server_name, "tool": tool}
    return namespaced
```

Now `notes__search` and `github__search` coexist without ambiguity, and
routing becomes a direct lookup instead of a guess:

```python
async def call_namespaced_tool(client, namespaced_catalog, full_name: str, arguments: dict):
    entry = namespaced_catalog[full_name]
    session = client.sessions[entry["server"]]
    original_name = entry["tool"].name
    return await session.call_tool(original_name, arguments)
```

The model only ever sees `notes__search` and `github__search` as distinct
tool names in the list you send it — the underlying servers never know
their tools were renamed, since you call back with the *original* name on
`call_tool`.

## Why tool count is a real cost, not just clutter

Every tool definition — name, description, full JSON Schema for its
parameters — gets serialized into the request the model sees on every
single turn of the conversation. A server with eight well-documented tools
might contribute 1,500-2,500 tokens of schema before the model has read a
word of the actual user message. Multiply that by twelve servers and you can
burn a meaningful fraction of a model's context window on tool definitions
alone, on every turn, whether or not any of those tools get used.

There's a correctness cost too, not just a token cost: tool-selection
accuracy measurably degrades as the candidate list grows, because the model
has to discriminate between more semantically similar options under the
same context budget.

## Trimming the active tool set

The fix isn't fewer servers — it's not sending every tool from every
connected server on every turn. Two practical strategies:

**Static allow-lists per task.** If your host already knows the user is in
a "manage my GitHub issues" workflow, only include the `github__*` tools
plus maybe `notes__*`, and skip `search__*` entirely for that turn.

```python
def filter_catalog(namespaced_catalog: dict, allowed_servers: set[str]) -> dict:
    return {
        name: entry for name, entry in namespaced_catalog.items()
        if entry["server"] in allowed_servers
    }
```

**Relevance filtering.** For a general-purpose assistant that can't predict
the task in advance, a lightweight retrieval step over tool
names+descriptions (even simple keyword matching, or embedding similarity
against the user's message — the same idea as the search techniques in a
vector-database course) picks the top-K most plausibly relevant tools for
this specific turn instead of sending all of them.

```python
def keyword_filter(namespaced_catalog: dict, query: str, top_k: int = 10) -> dict:
    query_words = set(query.lower().split())
    scored = []
    for name, entry in namespaced_catalog.items():
        desc = (entry["tool"].description or "").lower()
        score = sum(1 for w in query_words if w in desc or w in name.lower())
        scored.append((score, name, entry))
    scored.sort(key=lambda x: -x[0])
    return {name: entry for _, name, entry in scored[:top_k]}
```

Neither approach needs to be perfect — missing a relevant tool occasionally
is a worse user experience, but twelve servers' worth of unfiltered schema
on every turn is a worse one *by default, every single time*.

## Exercise

Take the `MultiServerClient` from the previous lesson and add a
`get_catalog_for(task_hint: str)` method that combines namespacing with the
keyword filter above, returning at most 8 tools. Test it by connecting to
three toy servers with overlapping tool names (reuse or extend the notes
server, add two more with at least one deliberately colliding tool name),
and confirm both tools survive namespacing and that an irrelevant server's
tools get filtered out for an on-topic query.
