---
description: "Naive RAG retrieves once and hopes; agentic RAG lets the model decide when it hasn't retrieved enough and go back for more."
---

# 01 · Advanced RAG Architectures

Everything so far has used the same shape: embed a query, fetch the top-k
chunks, stuff them in a prompt, generate an answer. That's **naive RAG**, and
it breaks down on questions that need more than one lookup, questions where
the first retrieval misses because the query and the source text use
different words, or questions that span multiple documents that never
individually mention the full answer.

This lesson covers the architectures teams reach for when naive RAG stops
being enough.

## Query rewriting and expansion

The user's literal query is often a bad search query. "What changed in the
pricing model last quarter?" has no embedding neighbor in a doc that says
"Q3 2025 subscription tier restructuring." A rewriting step uses an LLM to
turn the user's question into one or more better search queries before
anything touches the vector DB.

```python
from openai import OpenAI  # any chat-completion client works here

client = OpenAI()

def rewrite_query(user_question: str, n: int = 3) -> list[str]:
    prompt = f"""Rewrite the following question as {n} different search
queries that would find relevant documents in a technical knowledge base.
Return one query per line, no numbering.

Question: {user_question}"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    lines = resp.choices[0].message.content.strip().split("\n")
    return [l.strip() for l in lines if l.strip()]

queries = rewrite_query("What changed in the pricing model last quarter?")
# -> ["Q3 2025 pricing changes", "subscription tier restructuring 2025",
#     "pricing policy update history"]
```

Run each rewritten query through retrieval, merge and deduplicate the
results (e.g. by chunk id, keeping the highest score seen), then proceed as
normal. This alone fixes a large fraction of "the answer is in there but
retrieval never found it" failures.

## Multi-hop retrieval

Some questions require chaining lookups: "Which vendor supplies the
component that caused the Q2 outage?" needs you to first find *what caused
the Q2 outage*, extract the component name, and *then* search for which
vendor supplies it. A single retrieval pass can't do this because the
second query doesn't exist until you've read the answer to the first.

A simple multi-hop loop:

```python
def multi_hop_answer(question: str, retrieve, generate, max_hops: int = 3):
    context_chunks = []
    current_query = question

    for hop in range(max_hops):
        results = retrieve(current_query, top_k=5)
        context_chunks.extend(results)

        decision = generate(f"""Question: {question}
Context so far:
{format_chunks(context_chunks)}

Can you fully answer the question from this context? Reply YES or NO.
If NO, reply with a follow-up search query on a second line.""")

        if decision.startswith("YES"):
            break
        current_query = decision.split("\n")[-1].strip()

    return generate(f"""Question: {question}
Context:
{format_chunks(context_chunks)}

Answer the question using only the context above.""")
```

Each hop retrieves, checks whether it has enough to answer, and if not,
generates the next query from what it just learned. This is strictly more
expensive (multiple LLM calls, multiple retrievals per question) so it's
worth gating: only run multi-hop for questions a cheap classifier flags as
"probably needs more than one lookup."

## Agentic RAG

Query rewriting and multi-hop are both *fixed* patterns — a hardcoded loop
shape. Agentic RAG goes further: the LLM is given retrieval as a *tool* it
can call zero, one, or many times, in whatever order it decides, interleaved
with reasoning.

```python
tools = [{
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": "Search the vector database for relevant document chunks.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}]

def agentic_rag(question: str, retrieve, client):
    messages = [{"role": "user", "content": question}]

    for _ in range(5):  # hard cap on tool-call rounds
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools,
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content  # model decided it has enough to answer

        for call in msg.tool_calls:
            query = json.loads(call.function.arguments)["query"]
            results = retrieve(query, top_k=5)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": format_chunks(results),
            })

    return "Could not resolve within tool-call budget."
```

The model decides for itself: retrieve, decide it needs a different angle,
retrieve again, or just answer directly if the question doesn't need
retrieval at all (e.g. "summarize what you just told me"). This is the
pattern behind most production "chat with your docs" agents today —
multi-hop is really a special case of agentic RAG with the loop shape fixed
in advance instead of left to the model.

## Graph-RAG, briefly

Vector search finds chunks that are *semantically similar* to a query, but
it's bad at questions about *relationships*: "which teams were affected by
every incident that touched the auth service?" isn't a similarity question,
it's a graph traversal. Graph-RAG systems extract entities and relationships
from documents into a graph (often with an LLM doing extraction: "service X
depends on service Y", "incident A affected team B") stored alongside the
vector index. A query can then do both: traverse the graph for structural
relationships, and fall back to vector search for anything the graph didn't
capture. Building a full graph-RAG pipeline is out of scope here, but know
the shape exists — when questions are fundamentally about *connections*
between entities rather than *similarity* between text, a pure vector store
is the wrong tool no matter how good your chunking is.

## How It Actually Works

1. **Why rewriting helps more than better embedding models.** Embedding
   models are trained to place paraphrases near each other, but a question
   and its answer are often *not* paraphrases of each other — "what changed"
   and "Q3 2025 restructuring" share no vocabulary and limited semantic
   overlap even though one answers the other. Rewriting closes this gap by
   using the LLM's world knowledge to guess vocabulary the source documents
   likely use, which is a different kind of signal than embedding similarity
   alone can provide.
2. **Why multi-hop needs a stopping condition, not a fixed hop count.** Most
   questions resolve in one hop; forcing every question through three hops
   triples latency and cost for no benefit. The "can you answer yet?" check
   each round is what makes this adaptive instead of wasteful.
3. **Why agentic RAG can be *worse* than multi-hop on narrow domains.** Giving
   the model full discretion over when to search means it can also decide
   *not* to search when it should have, hallucinating from parametric
   knowledge instead. Multi-hop's fixed loop is less flexible but more
   predictable — a reasonable default unless you've measured agentic RAG
   actually winning on your eval set (lesson 2 gives you the metrics to make
   that call with evidence instead of vibes).
4. **Where the cost actually goes.** Every extra hop or tool call is a full
   LLM round trip, typically 1-3 seconds and real token cost. A naive RAG
   call might cost one generation; an agentic RAG call that takes 4 tool
   rounds costs five LLM calls. Architectures in this lesson trade latency
   and cost for correctness — always confirm the question mix in production
   actually needs it before deploying the more expensive pattern everywhere.

## Exercise

Take the `multi_hop_answer` function above and adapt it to run against your
own retrieval setup (Chroma or whichever backend you've been using). Write
three test questions: one that a single retrieval pass answers fine, one
that genuinely needs two hops, and one that needs three. Log how many hops
each one actually takes, and confirm the loop stops early on the easy
question instead of always running to `max_hops`.
