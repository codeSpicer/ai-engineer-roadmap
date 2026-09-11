# Project A — Hybrid-Search Docs Q&A

**Phase:** 2 — Building AI Apps · **Skill:** RAG · **Difficulty:** Intermediate

A question-answering system over a real document corpus that answers with citations,
using **hybrid retrieval** (BM25 keyword + dense vectors with Reciprocal Rank Fusion) plus
a cross-encoder **reranker** and grounded generation. **Local-first: Ollama + Chroma, no API
keys required** — this is the full RAG loop that Phase 1 deliberately split in half
(Project A = generation, Project B = retrieval).

## Links to roadmap.sh/ai-engineer

- RAG (implementing RAG: chunking, indexing, retrieval, generation)
- Embeddings + Vector Databases (reuse of Phase 1 retrieval primitives)

## Concepts covered

Chunking strategies (fixed vs recursive vs semantic), dense retrieval (bi-encoders, cosine),
keyword retrieval (BM25: TF, IDF, length norm), Reciprocal Rank Fusion, cross-encoder
reranking (retrieve-cheap / rerank-precise), grounded generation with inline citations,
abstention via score thresholds, RAG failure taxonomy (retrieval vs generation attribution).

## Prerequisites

- Foundations Projects A & B completed (you reuse embeddings + Chroma + token discipline)
- Python 3.10+, Ollama running (`nomic-embed-text` + a chat model like `llama3.2:latest`)
- `pip install chromadb ollama rank-bm25 sentence-transformers pypdf`

## Learning objectives

- Build an end-to-end RAG pipeline that grounds answers in retrieved context with citations
- Implement dense and BM25 retrieval separately, then fuse with RRF — and show when hybrid wins
- Add a cross-encoder reranker over fused candidates and measure the delta with evidence
- Diagnose failures as retrieval problems vs generation problems from logs

## How it works (the pipeline)

```
corpus/ (PDFs, .md, wiki dump)
  │  loader.py       parse PDFs/md → Document(text, {source, page, title})
  ▼
[Documents] × N
  │  chunker.py      recursive split, ~800 chars / 150 overlap (tunable)
  ▼
[chunks + metadata] × ~800
  │  ┌─ embedder.py  ollama.embed("nomic-embed-text") → Chroma (dense index)
  │  └─ bm25.py      tokenize → BM25Okapi index (keyword index, in-memory + pickle)
  ▼
query
  │  dense: embed query → Chroma top-20 ─┐
  │  sparse: tokenize → BM25 top-20 ─────┤─ fusion.py (RRF, k=60) → top-20 fused
  ▼                                       │
rerank.py  cross-encoder (ms-marco-MiniLM-L-6-v2) scores query×passage jointly → top-5
  │
generate.py  prompt = instruction + top-5 chunks (with IDs) → Ollama chat → answer + [cites]
  │
CLI prints answer, citations, per-stage timing, and the retrieved chunk table
```

Every stage logs its inputs/outputs. That logging IS the debugging interface —
without it you cannot tell retrieval failures from generation failures.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

ollama serve                              # if not already running
ollama pull nomic-embed-text              # embedding model (Phase 1 reuse)
ollama pull llama3.2:latest               # generation model

# Put source documents in corpus/ (commit 10–30 PDFs/md to start; reuse Phase 1 wiki dump)
python -m hybrid_qa index --corpus corpus --db-dir rag_db
python -m hybrid_qa ask "what is the refund window?" --show-context
```

| Flag | Where | Default | Meaning |
| ---- | ----- | ------- | ------- |
| `--corpus` | index | `corpus/` | folder of source docs |
| `--chunk-size` | index | `800` | target chars per chunk |
| `--overlap` | index | `150` | chars shared between chunks |
| `--db-dir` | both | `rag_db/` | Chroma persistence dir |
| `--top-k` | ask | `5` | final passages fed to the LLM |
| `--retrieve-k` | ask | `20` | candidates per retriever before fusion |
| `--no-hybrid` | ask | off | dense-only ablation switch |
| `--no-rerank` | ask | off | skip reranker ablation switch |
| `--min-score` | ask | none | abstention threshold on rerank score |
| `--show-context` | ask | off | print retrieved chunks + scores + fusion ranks |
| `--trace` | ask | off | print full trajectory (query → ranks → rerank → prompt) |

Score reading (dense cosine, same bands as Phase 1):
**0.7+** genuinely relevant · **0.5–0.7** adjacent, verify · **<0.5** likely corpus gap —
with `--min-score` this becomes an explicit "no good match" abstention instead of a hallucination.

## Project layout (files you will create)

```
hybrid-search-docs-qa/
├── requirements.txt
├── corpus/                    10–30 source docs YOU choose (PDFs/md)
├── hybrid_qa/
│   ├── __main__.py            `python -m hybrid_qa` entry
│   ├── cli.py                 index / ask subcommands, timing, printing
│   ├── loader.py              PDFs/md → Document(text, metadata)
│   ├── chunker.py             recursive splitter (reuse Phase 1, add separators)
│   ├── embedder.py            batched ollama.embed() (reuse Phase 1)
│   ├── store.py               Chroma persistence (reuse Phase 1)
│   ├── bm25.py                tokenize + BM25Okapi build/query/save/load
│   ├── fusion.py              RRF over dense ranks + BM25 ranks
│   ├── rerank.py              cross-encoder scorer over fused candidates
│   ├── generate.py            grounded prompt + citation parsing
│   └── trace.py               per-query JSONL log (ranks, scores, prompt, answer)
├── evals/
│   └── golden.jsonl           20–30 Q/A pairs with known-good chunk IDs
└── README.md                  this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Corpus + golden set first (before any retrieval code)

- [ ] Collect 10–30 real documents into `corpus/` (product docs, wiki dump, papers — one domain).
- [ ] Write `evals/golden.jsonl` with 20–30 questions, each: `{"q": ..., "answer": ..., "must_hit": ["file.md#chunk"]}`.
  - Cover 4 types: exact-term (error codes, names), paraphrase (synonyms of doc wording),
    multi-fact (answer spans 2 chunks), unanswerable (nothing in corpus).
- [ ] Verify: you can state for each question which chunk(s) SHOULD win. If you can't, the corpus is wrong.

### Phase 1 — Ingestion: loader + chunker (reuse Phase 1, extend to PDFs)

- [ ] `loader.py`: parse `.md` (reuse Phase 1) + `.pdf` (pypdf: page text + page numbers into metadata).
- [ ] `chunker.py`: upgrade Phase 1 sliding window to recursive splitting
  (split on `\n\n` → `\n` → `. ` → space) with the same size/overlap knobs.
- [ ] `embedder.py` + `store.py`: copy from Phase 1, add `source + page + chunk_index` metadata.
- [ ] Verify: `index` then `ask --no-hybrid --no-rerank --show-context` returns Phase-1-quality dense results.

### Phase 2 — BM25 retriever (standalone, before fusion)

- [ ] `bm25.py`: tokenize (lowercase, split, stopword strip), build `BM25Okapi`, `save/load` via pickle.
- [ ] CLI: `ask --dense-only` vs `ask --bm25-only` (implement both flags even if temporary).
- [ ] Run the 4 question types through each alone; record which type each wins.
- [ ] Verify: exact-term queries (codes, names) rank higher under BM25; paraphrase queries rank higher under dense.
  - If this doesn't reproduce, your tokenizer or chunking is broken — fix before fusing.

### Phase 3 — RRF fusion (the hybrid core)

- [ ] `fusion.py`: `score(d) = Σ 1/(k + rank)` with `k=60`; dense top-20 + BM25 top-20 → fused top-20.
- [ ] Handle asymmetric hits (doc in one list only gets one term — correct, don't impute).
- [ ] CLI: default `ask` = fused; `--no-hybrid` = dense-only for ablation.
- [ ] Verify: on golden set, fused recall@5 ≥ max(dense recall@5, BM25 recall@5). Log ranks per retriever in `--trace`.

### Phase 4 — Cross-encoder rerank (precision stage)

- [ ] `rerank.py`: `CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')`, score query×each fused candidate jointly → top-5.
- [ ] CLI: `--no-rerank` ablation switch; `--show-context` prints pre/post-rerank order.
- [ ] Measure latency added per query (expect +100–500ms CPU for 20 candidates — record yours).
- [ ] Verify: on paraphrase + multi-fact questions, top-1 correctness improves vs fusion alone;
  on exact-term questions it should at least not regress.

### Phase 5 — Grounded generation + citations + abstention

- [ ] `generate.py`: prompt = system instruction ("answer ONLY from context, cite [id] per claim")
  + numbered chunks + user query → `ollama.chat()`.
- [ ] Parse `[chunk_id]` citations back to metadata; render `answer + Sources: file (page)`.
- [ ] `--min-score`: if best rerank score < threshold → abstain
  ("I don't have that in the corpus") instead of generating.
- [ ] Verify: unanswerable golden questions abstain; answerable ones cite chunks that actually contain the claim
  (spot-check 10 by eye — a citation to a non-supporting chunk is a grounding bug).

### Phase 6 — Ablation report (the deliverable that proves learning)

- [ ] Run full golden set in 3 configs: (1) dense-only, (2) hybrid (RRF), (3) hybrid + rerank.
- [ ] Record per question: hit/miss, rank of first correct, abstention correctness. Fill the table below.
- [ ] Write 1-page verdict: when did hybrid beat dense, when did rerank matter, what does rerank cost in ms,
  where would you set `--min-score` and why.

---

## Core experiments (fill in YOUR numbers)

### 1. Hybrid vs dense ablation ← the core objective

Run all golden questions in 3 configs, record recall@5 and top-1-correct:

| Question type (5–8 Qs each) | dense-only R@5 / top-1 | hybrid RRF R@5 / top-1 | hybrid+rerank R@5 / top-1 |
| --------------------------- | ---------------------- | ---------------------- | ------------------------- |
| exact-term (codes, names)   |                        |                        |                           |
| paraphrase                  |                        |                        |                           |
| multi-fact                  |                        |                        |                           |
| unanswerable (abstain?)     |                        |                        |                           |

**What to look for:** hybrid should dominate exact-term + mixed queries; pure paraphrase may tie.
Rerank should move top-1 more than recall@5 (it reorders, rarely rescues unfused misses).
If rerank doesn't move YOUR metrics, say so — "not worth its latency on this corpus" is a valid finding.

### 2. Break it deliberately

- Ask with `--no-hybrid` a query containing an exact rare term from the docs — watch dense miss what BM25 nails.
- Paraphrase a doc sentence with zero shared words — watch BM25 miss what dense nails.
- Ask an off-corpus question with and without `--min-score` — without it you get a cited hallucination; with it, abstention.
- Delete one source file, re-index: confirm its chunks vanish AND its golden questions now abstain (not hallucinate).

### 3. Latency forensics

Time one `ask --trace` end-to-end and decompose: query-embed ms / BM25 ms / fusion ms / rerank ms / generation ms.
Expect generation + rerank to dominate; dense lookup and RRF to be noise. State which stage you'd optimize first at 10× QPS.

### 4. Extend it (springboard to Project B)

- Add `sources` aggregation: group hits per document instead of per chunk for long answers.
- Add query rewriting: one LLM call to expand the query before retrieval; measure delta on paraphrase set.
- Swap chunk size (300 vs 1200, Phase 1 method) and re-run the ablation — does hybrid's advantage grow or shrink?

## Observations worth writing down as you go

1. **Which question type each retriever wins** — with example queries and ranks, not generic claims.
2. **RRF's robustness**: BM25 scores (0–20) and cosine scores (0–1) never needed normalization — why rank-fusion dodges that.
3. **Rerank cost vs gain**: your measured ms added vs top-1 delta. The "retrieve cheap, rerank precise" tradeoff in numbers.
4. **Abstention calibration**: the score value where your corpus separates answerable from unanswerable — per-model, per-corpus, never guessed.
5. **Retrieval-vs-generation attribution**: for each wrong answer, log whether the chunks contained the answer (retrieval bug) or not (generation bug). This habit is the whole of Phase 3 evals.

## Definition of done

- `ask` answers with inline citations that resolve to real source chunks; `--show-context` exposes the full retrieval table.
- Golden-set ablation table is filled: hybrid + rerank visibly beats dense-only on YOUR corpus, with latency noted.
- You can explain when hybrid beats pure vector, what RRF does mathematically, and why the reranker goes last.
- Unanswerable questions abstain instead of hallucinating with citations.

## Reference material

- Gauntlet-AIDP/rag-cookbook (steps 01–03): https://github.com/Gauntlet-AIDP/rag-cookbook
- tkeitzl/rag-from-scratch: https://github.com/tkeitzl/rag-from-scratch
- NirDiamant/RAG_Techniques: https://github.com/NirDiamant/RAG_Techniques
- rank-bm25: https://github.com/dorianbrown/rank_bm25 · cross-encoders: https://www.sbert.net/docs/cross_encoder.html

## Next

Project B makes retrieval **adaptive** (router + decomposition + graph + retry) on top of this pipeline.
Keep this codebase — Project B starts from it.
