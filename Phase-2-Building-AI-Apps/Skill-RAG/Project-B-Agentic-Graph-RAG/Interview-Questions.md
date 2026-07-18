# Interview Questions — RAG Project B: Agentic / Graph RAG

Complete the project, then quiz yourself. Answers are detailed.

## Phase 2 — Building AI Apps · RAG · Project B

**Q1. What is the limitation of "always retrieve then generate" (naive RAG) that this project addresses?**
Naive RAG retrieves the same way for every query: embed the question, pull top-k,
generate. It fails when (a) the question needs **multiple retrievals** (multi-hop:
"A's sister's employer?" requires several lookups), (b) retrieval is unnecessary
(factual greetings, math), or (c) a single vector search can't find the answer because
the facts are connected relationally, not semantically. This project makes retrieval
*adaptive* and adds graph structure to handle connected facts.

**Q2. What is dynamic retrieval routing?**
Instead of always retrieving, a router classifies each query and chooses a path:
- **answer-directly**: no retrieval (greetings, simple math, already-known facts) —
  saves latency/cost.
- **retrieve**: standard single-pass RAG.
- **multi-hop**: decompose and traverse (see below).

The router is typically an LLM call with a classification prompt or a small classifier.
The payoff is efficiency and correctness: you don't waste retrieval on trivial queries,
and you escalate complex ones to the right strategy.

**Q3. What is query decomposition and when is it needed?**
Query decomposition splits a complex question into simpler sub-questions, retrieves
for each, then synthesizes. Example: "What did the company that acquired X in 2023
report as revenue?" → (1) Who acquired X in 2023? (2) What was their revenue? Each
sub-query retrieves independently; answers chain together.

It's needed for **multi-hop** questions where a single embedding can't capture the
full intent, and where the answer depends on composing several facts.

**Q4. How does a knowledge graph help RAG, and how is it traversed?**
A knowledge graph stores **entities as nodes and relationships as edges** (e.g.
(Alice)-[works_at]->(Acme)-[located_in]->(Berlin)). For multi-hop questions, you
traverse edges to gather connected context that pure vector search would miss — vector
search finds "similar text," not "things related by a specific relationship."

Traversal: extract entities/relationships from docs into a graph store (Neo4j or
in-memory NetworkX), then for a query, identify seed entities and walk edges (BFS/DFS)
to collect multi-hop context before vector search. This grounds answers in explicitly
connected facts.

**Q5. What is self-correction / retry, and why is it important in agentic RAG?**
After generating, the agent checks confidence (e.g. faithfulness score, missing
citations, "I don't know" detection). On low confidence, it **retries with a different
strategy** — rephrase the query, switch retriever, broaden graph traversal, or fetch
more context. This loop turns a brittle one-shot pipeline into a system that recovers
from bad retrieval, which is what makes it "agentic" rather than scripted.

**Q6. How does this project extend beyond roadmap.sh, and what's the risk of agentic RAG?**
It goes beyond the standard RAG node into Agentic RAG + Graph RAG. Risk: more moving
parts = more latency, more cost, and harder debugging. The router can make wrong
decisions (skip retrieval it needed). Mitigation: log the full trajectory so you can
trace *why* a query took a given path (the project's definition of done requires this).
