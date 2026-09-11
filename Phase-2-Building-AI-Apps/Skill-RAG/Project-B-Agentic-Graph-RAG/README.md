# Project B — Agentic / Graph RAG

**Phase:** 2 — Building AI Apps · **Skill:** RAG · **Difficulty:** Intermediate–Advanced

A RAG assistant that **decides how to retrieve**: whether to retrieve at all, which method to use,
and whether to retry — plus **knowledge-graph traversal** for multi-hop questions.
Built directly on top of Project A's hybrid pipeline. This extends *beyond* what roadmap.sh covers.
**Local-first: Ollama + Chroma + NetworkX (in-memory graph, Neo4j optional).**

Naive RAG retrieves the same way for every query. This project fixes the three cases where that breaks:
(a) retrieval is unnecessary (greetings, math, chitchat), (b) one vector search can't compose
several facts (multi-hop), (c) first-pass retrieval was bad and needs a second try (self-correction).

## Links to roadmap.sh/ai-engineer

- RAG (advanced) + AI Agents (dynamic retrieval decisions)
- Extends beyond the roadmap into Agentic RAG and Graph RAG

## Concepts covered

Dynamic retrieval routing (classify-then-act), query decomposition (split → retrieve → chain),
entity/relation extraction, knowledge graphs (nodes/edges, BFS traversal), hybrid graph+vector
context assembly, confidence-gated retry (self-correction), full trajectory tracing
(why-did-this-query-take-this-path), agentic cost/latency/debuggability tradeoffs.

## Prerequisites

- RAG Project A completed and working (this project imports its retriever + reranker + generator)
- `pip install networkx spacy` (Neo4j optional — default is in-memory NetworkX so zero infra)
- An Ollama chat model for router / extractor / generator (`llama3.2:latest` minimum — but router /
  decompose / triple-extract are where small models crack first; `qwen3:8b` routes noticeably more
  reliably, and the 12–14B tier is the fallback if misroutes survive prompt fixes. Tier guide: root `MODELS.md`)

## Learning objectives

- Let an agent choose the retrieval strategy per query (direct / single-pass / multi-hop) and prove it saves work
- Build and traverse a small knowledge graph that answers a multi-hop question Project A cannot
- Add confidence-gated retry that recovers from bad first-pass retrieval
- Trace every decision (route, sub-queries, graph path, retry reason) in a per-query log

## How it works (the pipeline)

```
query
  │
  ▼
router.py  (LLM classifier: DIRECT | SINGLE | MULTI_HOP)
  │  logs: route + reason + confidence
  ├─ DIRECT ───────────────→ generate.py (no retrieval, answer from model)
  │
  ├─ SINGLE ───────────────→ Project A pipeline (hybrid RRF → rerank → top-5)
  │                            → confidence check ── pass → generate
  │                                                 └─ fail → RETRY (see below)
  │
  └─ MULTI_HOP ──→ decompose.py (LLM splits into sub-questions)
                     │  sub-q1 → hybrid retrieve → fact 1
                     │  sub-q2 (+ fact 1) → hybrid retrieve → fact 2 ...
                     ├─ graph.py: seed entities → BFS traverse (≤2 hops) → relation paths
                     └─ assemble: sub-answers + graph paths + vector chunks → generate
                            → confidence check ── pass → generate
                                                 └─ fail → RETRY

RETRY (self-correction, max 2 rounds):
  rephrase query → wider traversal (2 hops → 3) / larger k (20 → 40) / BM25-heavy fusion
  → re-retrieve → re-check. Log every attempt; give up honestly if still failing.

trace.jsonl per query: {route, sub_queries, graph_path, ranks, scores, retries, prompt, answer}
```

The trace log is the definition of done — "you can trace why a given query took a given path."

## Setup

```bash
# Start from your Project A repo — copy it or build in place
cp -r ../Project-A-Hybrid-Search-Docs-QA ./agentic-graph-rag && cd agentic-graph-rag
pip install -r requirements.txt   # + networkx
ollama pull llama3.2:latest

# Build the graph once from the same corpus
python -m agentic_rag build-graph --corpus corpus --graph graph.pkl
python -m agentic_rag ask "which company acquired X in 2023 and what was their revenue?" --trace
```

| Flag | Where | Default | Meaning |
| ---- | ----- | ------- | ------- |
| `--trace` | ask | off | print full trajectory (route → sub-qs → graph path → retries) |
| `--route` | ask | auto | force `direct/single/multi` (debug override) |
| `--max-retries` | ask | `2` | self-correction rounds before honest give-up |
| `--hops` | ask | `2` | max graph BFS depth |
| `--show-graph` | ask | off | print matched entities + traversed edges |
| `--graph` | both | `graph.pkl` | persisted NetworkX graph path |

## Project layout (files you will create — Project A files reused, not rewritten)

```
agentic-graph-rag/
├── <everything from Project A: hybrid_qa/, corpus/, evals/>   # reused as-is
├── agentic_rag/
│   ├── __main__.py        `python -m agentic_rag` entry
│   ├── cli.py             ask / build-graph subcommands
│   ├── router.py          LLM classifier → DIRECT | SINGLE | MULTI_HOP (+ reason)
│   ├── decompose.py       complex Q → ordered sub-questions
│   ├── extract.py         chunk text → (entity, relation, entity) triples via LLM
│   ├── graph.py           NetworkX build / save / load / BFS traverse
│   ├── confidence.py      rerank-score + citation-coverage → pass/fail + reason
│   ├── retry.py           rephrase + widen (k, hops, BM25 weight) strategies
│   └── trace.py           per-query JSONL trajectory log
├── evals/
│   ├── golden.jsonl       extend Project A set (see Phase 0)
│   └── graph.pkl          built entity graph (regenerable)
└── README.md              this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Multi-hop golden set first (before any agent code)

- [ ] Extend Project A's `golden.jsonl` with 10–15 new questions in 3 new buckets:
  - **no-retrieval** (5): greetings, simple math, "what can you do" — must route DIRECT.
  - **multi-hop** (5–8): answer needs 2+ facts chained (e.g. "company that acquired X → their revenue").
    Each must be UNANSWERABLE by single-pass Project A (verify by running it — record the failure).
  - **retry-triggering** (3–5): paraphrased/underspecified queries where first-pass top-1 is wrong but
    rephrased second-pass hits (find these by running Project A and keeping its misses).
- [ ] Verify: Project A fails the multi-hop set (wrong or partial answers logged). If it passes, write harder questions.

### Phase 1 — Router (classify-then-act)

- [ ] `router.py`: single LLM call, system prompt with 3 route definitions + 2 few-shot examples each,
  forced JSON output `{"route": ..., "reason": ..., "confidence": 0-1}` (native `format="json"`).
- [ ] Wire: DIRECT → straight to generator; SINGLE/MULTI → existing Project A path (router-only, no graph yet).
- [ ] CLI `--route` force-override for debugging misroutes.
- [ ] Verify: 100% of no-retrieval questions route DIRECT; 0% of multi-hop questions route DIRECT.
  Log every misroute with its reason string — prompt-fix from those, not from theory.

### Phase 2 — Query decomposition (multi-hop without graph yet)

- [ ] `decompose.py`: LLM call → ordered sub-questions, each answerable by one retrieval
  (e.g. "Who acquired X in 2023?" → "What was <answer1>'s 2023 revenue?").
- [ ] Chain: retrieve sub-q1 → inject answer into sub-q2 → retrieve → synthesize final answer with citations per hop.
- [ ] Verify: at least 2 multi-hop golden questions now pass that failed in Phase 0 — via decomposition alone.
  Record which still fail (these motivate the graph).

### Phase 3 — Knowledge graph: extract → build → traverse

- [ ] `extract.py`: per chunk, LLM triple extraction `[(head, relation, tail)]` with source-chunk IDs attached.
  Start with 20–50 chunks (not the whole corpus) — graph quality over coverage.
- [ ] `graph.py`: triples → NetworkX `DiGraph` (nodes=entities, edges=relations + `source_chunk` attr);
  `save/load` via pickle; `traverse(seed_entities, max_hops=2)` BFS returning paths.
- [ ] Seed-entity linking: simple exact/alias match of query nouns against node names (no embedding linker yet —
  note this as a limitation with an example miss).
- [ ] Verify: `build-graph` then `--show-graph` on a multi-hop query prints a real path
  (e.g. `X -[acquired_by]-> Acme -[revenue_2023]-> $Y`) whose edges cite real chunks.

### Phase 4 — Graph + vector assembly (the hybrid context)

- [ ] Assemble: graph paths (explicit relations) + vector top-k (supporting prose) → numbered context → generator.
- [ ] Rule: graph paths first (precise), vector chunks after (context) — record this ordering decision.
- [ ] Verify: the Phase-2 still-failing multi-hop questions now pass; single-hop golden answers don't regress
  (re-run full Project A set — graph path must not pollute simple queries).

### Phase 5 — Confidence gate + retry (what makes it "agentic")

- [ ] `confidence.py`: fail if (best rerank score < threshold) OR (answer has zero resolvable citations)
  OR (router confidence < 0.5 on a SINGLE route). Return reason string.
- [ ] `retry.py` strategies in order: (1) LLM rephrase → re-retrieve, (2) widen `k` 20→40 + hops 2→3,
  (3) BM25-heavy fusion. Max 2 rounds, then honest abstention with logged attempts.
- [ ] Verify: retry-triggering golden questions flip from fail→pass on round 2; log shows the reason + strategy.
  Also verify a still-unanswerable query abstains after 2 rounds (not infinite loop).

### Phase 6 — Trajectory report (the deliverable)

- [ ] Every `ask --trace` emits one JSONL line with route, sub-queries, graph path, ranks, retry history.
- [ ] Run the FULL extended golden set; fill the table below.
- [ ] Write 1-page verdict: which queries took which path and why, router accuracy, retry rescue rate,
  added latency per path, and the failure you still can't fix (entity-linking misses are the honest answer).

---

## Core experiments (fill in YOUR numbers)

### 1. Path-vs-baseline ← the core objective

| Question bucket | Project A (single-pass) correct | Agentic correct | Path taken (direct/single/multi/retry) |
| --------------- | ------------------------------- | --------------- | -------------------------------------- |
| no-retrieval (5) |                              |                 |                                        |
| single-hop (Project A set) |                    |                 |                                        |
| multi-hop (5–8) |                                 |                 |                                        |
| retry-triggering (3–5) |                          |                 |                                        |

**What to look for:** multi-hop flips fail→pass; no-retrieval gets FASTER/cheaper (no retrieval at all);
single-hop stays flat (router must not regress the easy stuff). Any single-hop regression is a router bug.

### 2. Graph ablation: decomposition-only vs decomposition+graph

Disable graph (`--route single` + decompose only) vs full multi path on the multi-hop set.
Record which questions NEED the graph (relation-chained) vs which decomposition alone solves.
This is your answer to "when does Graph RAG earn its complexity."

### 3. Break it deliberately

- Force `--route direct` on a factual question — watch confident hallucination with zero citations.
- Ask a multi-hop question whose middle entity is phrased differently from the graph ("Acme Corp" vs "Acme") —
  watch seed-linking miss and the graph path come back empty (the entity-linking limitation, concretely).
- Set `--max-retries 0` on a retry-triggering question — watch it fail where default rescues it.
- Point at an empty `--graph` path — confirm graceful fallback to vector-only, not a crash.

### 4. Latency forensics

Time one query per path: DIRECT ms / SINGLE ms / MULTI ms / MULTI+retry ms.
Expect DIRECT ≪ SINGLE < MULTI ≪ retry-chain. State the per-path cost and where you'd put a timeout
at 10k req/day (this feeds the Phase-2 gap topic on agentic system design).

## Observations worth writing down as you go

1. **Router confusion pairs** — which queries it misroutes and the reason strings; your prompt fixes.
2. **Decomposition vs graph boundary** — example question each side of it.
3. **Entity-linking misses** — the concrete alias that broke traversal; why exact-match linking is the weak link.
4. **Retry rescue rate** — X of Y first-pass failures rescued, by which strategy; cost in ms per rescue.
5. **Complexity bill** — lines of code + latency added vs questions fixed. Agentic RAG is a tradeoff, not a free win.

## Definition of done

- A multi-hop question Project A demonstrably fails is answered correctly with a logged graph path + citations.
- No-retrieval questions skip retrieval entirely (faster, logged as DIRECT).
- Failed first-pass retrieval retries with a different strategy and the retry is visible in `--trace`.
- Extended golden table is filled; you can narrate why any query took its path from the trace alone.

## Reference material

- Gauntlet-AIDP/rag-cookbook (steps 04 Graph RAG, 05 Agentic RAG): https://github.com/Gauntlet-AIDP/rag-cookbook
- NirDiamant/RAG_Techniques (advanced notebooks): https://github.com/NirDiamant/RAG_Techniques
- NetworkX: https://networkx.org/ · Neo4j (optional scale-up): https://neo4j.com/docs/

## Next

Agents skill next: the router/retry loop here IS a single-purpose agent. Project A (ReAct) generalizes it.
