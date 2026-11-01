---
description: "A prompt template is for when the USER wants to trigger a known, reusable request explicitly — not for something the model should decide to do on its own."
---

# 07 · Prompts: Reusable Prompt Templates

## What a prompt template actually is

A **prompt** in MCP is a reusable, parameterized piece of prompt text that a
server offers — think of it as a saved, fill-in-the-blanks request. Where a
tool is something the *model* decides to call mid-conversation, a prompt is
something the *user* typically invokes explicitly, the way you'd pick a
saved template from a menu rather than describe what you want from scratch
every time.

Hosts commonly surface prompts as quick-actions or slash-commands in their
UI — the user sees a list of available prompts by name and picks one,
rather than the model silently choosing to use one.

## Defining a prompt

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.prompt()
def code_review(language: str, focus: str = "general code quality") -> str:
    """Generate a code review request for a given language and focus area."""
    return (
        f"Please review the following {language} code, focusing on "
        f"{focus}. Point out specific issues with line references, and "
        f"suggest concrete fixes rather than general advice."
    )
```

`@mcp.prompt()` works the same way `@mcp.tool()` does: the function's type
hints become the prompt's argument schema, and the docstring becomes its
description. `language` is required (no default), `focus` is optional (it
has a default value). A client calling `prompts/get` with
`{"language": "Python"}` gets back the fully-rendered prompt text with
`focus` filled in from its default.

## Arguments with defaults vs. without

```python
@mcp.prompt()
def summarize(text: str, max_sentences: int = 3) -> str:
    """Summarize a block of text in a target number of sentences."""
    return f"Summarize the following text in at most {max_sentences} sentences:\n\n{text}"
```

Here `text` must be supplied every time; `max_sentences` falls back to `3`
when the caller doesn't specify it. This is exactly how optional tool
arguments behave too — the same Python defaults mechanism drives both.

## Prompt or tool — which one?

Ask: is this something the user explicitly chooses to trigger, with a
roughly fixed shape each time ("review this code," "summarize this text,"
"write a commit message for this diff")? That's a prompt. Is it something
the model should decide to reach for on its own, based on reasoning about
what the user's actual request needs? That's a tool.

A "generate a weekly status report" request the user runs the same way
every Friday is a good prompt — it's a known, repeatable shape of request.
A "look up this customer's order history" request that the model should
trigger automatically whenever it's relevant to the conversation is a tool
— the model needs to decide when it applies, not the user.

## Exercise

Write a prompt `explain_error(error_message: str, language: str = "Python")`
that returns a request asking for a plain-English explanation of the given
error message and, if applicable, a likely fix, in the context of the given
language. Confirm in the Inspector that `prompts/get` with just an
`error_message` argument still works correctly, falling back to the
`language` default.
