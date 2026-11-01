---
description: "An audit log entry that doesn't record which tool, with what arguments, on whose behalf, and with what result isn't actually auditable — it just looks like one."
---

# 08 · Enterprise Governance: Audit Logs & Compliance

Once MCP servers sit between a model and real systems of record — customer
data, financial records, infrastructure that can be changed — "it worked in
testing" stops being enough. This lesson covers what an enterprise
deployment needs beyond the functional correctness earlier levels focused
on: who can prove what happened, and who approved it.

## What a real audit log entry needs

A log line that just says `tool called: update_customer` is close to
useless for compliance purposes. A usable audit record captures, at minimum:

```python
import time, json, uuid

def audit_log(tool_name: str, arguments: dict, caller_identity: str, result_summary: str):
    entry = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "tool": tool_name,
        "arguments": arguments,         # redact sensitive fields before logging
        "caller": caller_identity,      # the authenticated client/user, not just "a model"
        "result_summary": result_summary,
        "outcome": "success",           # or "denied" / "error"
    }
    # write to an append-only, tamper-evident store — not a rotating
    # local file a process can quietly lose on restart
    write_to_audit_store(entry)
```

The non-negotiable fields: **what** was called, **with what arguments**,
**on whose authority** (tying back to the auth work from Level 2 — the
authenticated identity behind the call, not just "the AI did it"), **when**,
and **what happened**. "On whose authority" matters even more in an
MCP context than a typical API: the acting party is an AI system a human
asked to do something, and compliance usually needs to trace the action back
to that human, not stop at "the model decided to."

## Data residency and PII

Tools that read or write personal data carry the same obligations any other
system touching that data does — MCP doesn't create new ones, but it's easy
to lose track of them once a tool is just "something the model can call."
Concretely:

- **Know which tools touch PII**, and treat their schemas and logs
  accordingly — the audit log shown above should redact or hash sensitive
  argument fields rather than logging them in the clear.
- **Respect data residency requirements** at the server level: if a
  regulation requires EU customer data to stay in the EU, that constrains
  where the *server* handling that tool can run and what it's allowed to
  call out to — not something the model or the protocol can enforce for
  you.
- **Apply the same retention and deletion rules to tool call history** that
  apply to the underlying data — an audit log that retains deleted
  customers' PII indefinitely can itself become a compliance problem.

## Approval workflows for high-risk tools

Not every tool should execute the instant the model calls it. For genuinely
high-risk actions (an irreversible database delete, a large financial
transaction, a production deployment), insert a human approval step between
the model's call and the tool's execution:

```python
@mcp.tool()
async def delete_customer_account(customer_id: str, reason: str) -> dict:
    """Request deletion of a customer account. Requires human approval
    before this actually executes."""
    approval = await request_human_approval(
        action="delete_customer_account",
        details={"customer_id": customer_id, "reason": reason},
    )
    if not approval.approved:
        return {"status": "denied", "reason": approval.denial_reason}

    await perform_deletion(customer_id)
    return {"status": "completed"}
```

This is the server-side complement to the client-side per-tool consent
pattern from Level 3's scopes-and-permissions lesson: that lesson was about
a *host* asking a user "allow this tool call?" before sending it; this is
about a *server* refusing to complete a genuinely high-risk action without
its own independent approval gate, which matters even if the calling host's
own consent prompt was somehow bypassed or misconfigured. Defense in depth,
not a single checkpoint either side can rely on alone.

## Exercise

Take one tool from any server you've built that modifies state (creates,
updates, or deletes something). Add: (1) an audit log call capturing the
fields listed above with sensitive arguments redacted, and (2) a human
approval gate modeled on the example, even if `request_human_approval` is
just a stub that prompts on the terminal for this exercise. Confirm the
tool refuses to act when approval is denied.
