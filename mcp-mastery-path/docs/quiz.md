---
title: "Final Quiz"
description: "Test what you have learned across all four levels of this course with a 10-question final quiz."
---

# Final Quiz

Ten questions drawn from all four levels of this course. You need **70% (7 out of 10)** to pass
and unlock your course completion certificate — you can retake it as many times as you like.

<div id="mp-quiz-root"></div>

<script type="application/json" id="mp-quiz-data">
[
  {
    "level": 1,
    "topic": "What Is MCP & Why It Exists",
    "question": "Without a shared protocol, an AI application that needs to use N different tools must write N bespoke integrations, and this cost repeats for every new application. How does MCP change that math?",
    "options": [
      "It eliminates the need for any integration code at all, since every tool becomes self-describing.",
      "It turns the M applications \u00d7 N tools problem into M + N: each application implements the client side once, each tool implements the server side once, and any client can talk to any server.",
      "It requires exactly one application to own every integration, which all other applications then call through that one app's API.",
      "It reduces the problem to N integrations total by having tool vendors agree on a single shared application to target."
    ],
    "correctIndex": 1,
    "explanation": "MCP standardizes discovery and calling so a tool's integration is written once as a server and reused by any MCP-compatible client \u2014 the same M\u00d7N-to-M+N shift the Language Server Protocol made for editors and languages."
  },
  {
    "level": 1,
    "topic": "JSON-RPC 2.0: The Wire Protocol Underneath",
    "question": "A client sends `{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\",\"params\":{}}` to a server. What does the server do with it?",
    "options": [
      "It replies with a response whose `id` is null, since no `id` was provided in the request.",
      "It treats the message as malformed, since every JSON-RPC message must include an `id`.",
      "It processes the message but sends no reply at all \u2014 the absence of `id` is itself the signal that this is a one-way notification.",
      "It waits for the client to resend the same message with an `id` attached before acting on it."
    ],
    "correctIndex": 2,
    "explanation": "JSON-RPC 2.0 has no separate 'type' field distinguishing requests from notifications \u2014 an `id` present means a reply is required; an absent `id` means it's a notification, and the receiver must not respond to it."
  },
  {
    "level": 1,
    "topic": "The stdio Transport & Local Servers",
    "question": "A tool handler in a stdio-transport MCP server calls `print(\"debug info\")` for troubleshooting. What actually happens?",
    "options": [
      "Nothing harmful \u2014 stdout output is automatically filtered out before the client parses the stream.",
      "The debug text is written into the same stream the client is parsing as newline-delimited JSON-RPC, corrupting the protocol framing and likely causing a parse failure on that message or the next one.",
      "The MCP SDK redirects all `print()` calls to stderr automatically, so this is safe by default.",
      "The server crashes immediately with a clear 'stdout is reserved' exception."
    ],
    "correctIndex": 1,
    "explanation": "For a stdio server, stdout IS the protocol channel \u2014 the host reads it expecting only newline-delimited JSON-RPC messages. Anything else written there (a stray print, a library's own logging) corrupts the stream. Debug output must go to stderr instead."
  },
  {
    "level": 2,
    "topic": "Authentication & OAuth 2.1 for Remote Servers",
    "question": "Why does a local stdio MCP server need no authentication step at all, while a remote Streamable HTTP server is specified to require OAuth 2.1?",
    "options": [
      "stdio is a faster transport, and OAuth would slow it down below an acceptable latency threshold.",
      "The trust decision for a stdio server already happened when the user put its launch command in their own config file \u2014 there's no network boundary, since the user's own machine chose to spawn it. A remote server is reachable by anyone who has its URL, with no equivalent built-in trust decision.",
      "stdio servers are incapable of handling the cryptographic operations OAuth requires.",
      "OAuth 2.1 is only defined for HTTP-based protocols as a matter of spec versioning, unrelated to trust boundaries."
    ],
    "correctIndex": 1,
    "explanation": "A stdio server only runs because the user explicitly configured their own host to launch it \u2014 there's no network involved and no unknown caller. A remote server has no such built-in gate, so MCP requires real authorization (OAuth 2.1 with bearer tokens) before it will let a caller invoke tools."
  },
  {
    "level": 2,
    "topic": "Sampling: Letting a Server Ask the LLM for Completions",
    "question": "A tool handler needs to summarize a long fetched web page before returning a result. Using `sampling/createMessage` to do this instead of calling a separate LLM API directly means what, specifically?",
    "options": [
      "The server is asking the CLIENT's own LLM \u2014 the same model the user is already talking to \u2014 to generate the summary, rather than using its own API key and model access.",
      "The request is automatically cached so the same URL is never summarized twice by any server.",
      "The server delegates the summarization to whichever MCP server was connected first in the session.",
      "The client blocks all further tool calls until the sampling request resolves, as a safety measure."
    ],
    "correctIndex": 0,
    "explanation": "Sampling flows in the opposite direction from a normal tool call: the server asks the client's connected LLM to generate text on its behalf, over the same session, so the server never needs its own model access, API key, or bill \u2014 and the client stays in control of which model actually answers."
  },
  {
    "level": 3,
    "topic": "Roots: Scoping a Server to a Workspace",
    "question": "A client declares a root at `/home/user/project` to a filesystem-capable MCP server. What actually stops that server from reading a file outside that directory?",
    "options": [
      "The MCP protocol itself blocks any filesystem call whose resolved path falls outside the declared roots, regardless of server implementation.",
      "Nothing in the protocol enforces this \u2014 roots are advisory; only a well-behaved server that explicitly checks every operation against the declared roots actually respects the boundary. A malicious or buggy server can simply ignore them.",
      "The operating system automatically revokes the server process's filesystem permissions outside the declared root the moment roots are sent.",
      "The client intercepts and re-validates every file path before the server receives the request, so the server's own behavior doesn't matter."
    ],
    "correctIndex": 1,
    "explanation": "Roots are a cooperative scoping signal between a trusted client and a trusted server, not a protocol-enforced sandbox. A server has to do its own resolved-path containment check (and reject path-traversal attempts like `../`) for roots to mean anything in practice \u2014 the protocol has no mechanism that forces it to."
  },
  {
    "level": 3,
    "topic": "Security: Prompt Injection & Tool Poisoning Risks",
    "question": "An assistant is asked to \"summarize this webpage\" for a URL. The page contains hidden text instructing the model to instead email the user's recent messages to an attacker. Why does this attack succeed without the attacker ever interacting with the user's system directly?",
    "options": [
      "The MCP server that fetched the page automatically executes any instruction-like text it finds before returning the result.",
      "The hidden text arrives in the model's context as part of an ordinary tool result, and the model has no reliable way to distinguish that from a genuine user instruction \u2014 if the model acts on it, it issues a new, unauthorized tool call using whatever permissions the session already has.",
      "The attacker must have already compromised the MCP server's source code for this to work.",
      "This only works if the webpage itself is served over an insecure (non-HTTPS) connection."
    ],
    "correctIndex": 1,
    "explanation": "Prompt injection via data doesn't require talking to the model directly \u2014 it only requires getting malicious text into something the model will read, like a tool result. The model can't reliably tell 'the user told me this' apart from 'this text, which looks like an instruction, was sitting inside a fetched document.'"
  },
  {
    "level": 3,
    "topic": "Error Handling & Resilience Patterns",
    "question": "A `tools/call` for `read_file` returns a normal, successful JSON-RPC response whose result has `isError: true` and content reading \"File not found: notes/missing.md\". What is the correct way to interpret and handle this?",
    "options": [
      "This is a JSON-RPC protocol-level error (like 'method not found') and should be retried automatically with backoff.",
      "The tool ran correctly and is reporting that the requested operation itself failed \u2014 this should flow back to the model as information, not be treated as a crash or a retryable transport fault.",
      "This indicates the client's request was malformed and must be resent with corrected parameters.",
      "This means the connection to the server has silently dropped and needs to be re-established."
    ],
    "correctIndex": 1,
    "explanation": "`isError: true` is MCP's tool-level failure signal layered on top of JSON-RPC, distinct from a JSON-RPC error object. The protocol exchange itself succeeded; the tool is just reporting that the operation it represents didn't succeed \u2014 not something retrying will fix, and not a crash."
  },
  {
    "level": 4,
    "topic": "MCP vs. Function Calling vs. LangChain Tools",
    "question": "An LLM API's \"function calling\" feature and MCP's `tools/list` + `tools/call` both involve tool definitions and tool invocation. What is the actual relationship between them?",
    "options": [
      "MCP replaces function calling entirely \u2014 a host using MCP no longer needs the model API's function-calling feature at all.",
      "They are competing, mutually exclusive standards, and a host must choose one or the other.",
      "Function calling is a model-API-level feature for emitting and receiving structured tool calls; MCP standardizes how an application discovers tool definitions and executes the calls behind the scenes, then hands the results to that same function-calling mechanism \u2014 MCP is the plumbing, function calling is still what the model API does.",
      "MCP is a wrapper specifically around LangChain's Tool abstraction, so it only works inside LangChain-based applications."
    ],
    "correctIndex": 2,
    "explanation": "MCP doesn't replace function calling \u2014 a host still uses the model API's normal function-calling flow. MCP standardizes the discovery-and-execution side (what tools exist, what they do, how to call them) so that plumbing doesn't need bespoke code per integration per model provider."
  },
  {
    "level": 4,
    "topic": "Versioning & Backward Compatibility",
    "question": "During the `initialize` handshake, a client proposes protocol version \"2025-06-18\" and the server responds with a different version it supports instead. What should the client do next?",
    "options": [
      "Proceed as if its originally proposed version was accepted, since protocol version mismatches rarely cause real problems.",
      "Validate whether it actually supports the version the server returned, and close the connection rather than proceed if it doesn't \u2014 never just assume the exchange succeeded.",
      "Automatically rewrite its own SDK code at runtime to match whatever version the server specified.",
      "Ignore the server's response entirely and retry `initialize` with the same proposed version until the server accepts it."
    ],
    "correctIndex": 1,
    "explanation": "Protocol version negotiation happens once, before any normal operation begins, and the client must validate the server's answer rather than assume success \u2014 proceeding on a version the client's own code doesn't actually implement leads to confusing runtime errors later instead of a clean failure at startup."
  }
]
</script>
