---
description: "Treat everything in this lesson as the trajectory as of late 2026, not a settled destination — this is the fastest-moving layer of the whole course."
---

# 09 · Where MCP Is Headed

Every other lesson in this course describes the spec and ecosystem as they
exist today. This one is deliberately different: a snapshot of where things
are trending, written with the honesty that a protocol this actively
developed will keep moving. Read it as "worth watching," not "guaranteed."

## Public server registries and directories

As the number of MCP servers in the wild has grown, so has demand for a way
to discover trustworthy ones without word-of-mouth — public directories and
registry efforts that index available servers, show their capabilities, and
in some cases attach provenance or verification signals, are an active area
of ecosystem investment. The practical implication for you: as these mature,
"build it yourself" and "find a vetted existing server" are both
increasingly real options for common integrations, and part of a
responsible build-vs-use decision will mean checking whether a well-
maintained server for what you need already exists before writing a new
one.

## Elicitation maturing

Elicitation — a primitive letting a *server* ask the user a question mid-task
and get a direct answer back, rather than only returning results to the
model and hoping the conversation surfaces what it needs — is a newer
addition to the spec than tools, resources, and prompts, and tooling and SDK
support for it is still catching up to those more established primitives.
Where it's heading: richer structured elicitation (not just free-text
prompts, but typed forms a host can render properly), and wider adoption in
servers that need information the model itself doesn't have and shouldn't
guess at — credentials, confirmations, disambiguating choices.

## Broader cross-vendor adoption

MCP started as an Anthropic-led open standard, but the stated goal — and the
visible trend — is a protocol that works the same regardless of which AI
provider's model a host happens to be using. Growing support for MCP across
other model providers and agent frameworks is the direction this has been
moving; the practical bet worth making today is that a well-built MCP server
is an investment in infrastructure that outlives any single model provider
relationship, not a Claude-specific integration.

## Multi-modal resources

Early resource content was overwhelmingly text. As agent use cases expand
into images, audio, and other media, expect resource and tool result types
to keep expanding to carry that content natively through the protocol rather
than requiring awkward base64-in-text workarounds — some of this groundwork
already exists in the spec today, with the direction being wider, more
ergonomic support across SDKs.

## What to actually do with this lesson

Don't build around any single prediction here as if it were already settled
— build servers that follow the spec as it exists today, keep them loosely
enough coupled to specific SDK internals that upgrading is realistic, and
revisit this lesson's claims periodically against the actual, current
specification rather than trusting this snapshot to stay accurate
indefinitely. The most durable skill from this whole course isn't memorizing
today's primitive list — it's understanding the protocol's design well
enough to keep up as it evolves.

## Exercise

Go find the current, official MCP specification changelog or release notes
(search for "Model Context Protocol specification changelog"). Pick one
change from the most recent few entries and write two or three sentences on
what problem it solves and whether it confirms, extends, or contradicts any
of the trends described above. This lesson will age — practice checking it
against the real source rather than taking it as fixed.
