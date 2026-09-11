# Project A — RAG Evaluation Harness (with Dataset Engineering)

**Phase:** 3 — Quality & Safety · **Skill:** Evals · **Difficulty:** Intermediate

A dataset-first evaluation harness that scores a RAG system on RAG-specific metrics and
compares retrieval configurations with evidence. Front-loaded with a **Dataset Engineering** stage:
curating and synthetically generating a golden test set. **Local-first: Ragas + Ollama judge,
your Phase 2 RAG pipeline as the system under test.**

You cannot improve what you cannot measure. Every "hybrid beats dense" claim from Phase 2 was
eyeballed on a handful of queries — this project turns those claims into scored tables on a fixed
golden set, so config changes produce deltas instead of vibes. The harness then becomes infrastructure:
Evals B gates CI on it, LLMOps B gates deploys on it, and the fine-tune-vs-prompt-vs-RAG decision gets
a numbers-backed answer.

## Links to roadmap.sh/ai-engineer

- Evaluation (RAG metrics, LLM-as-a-judge)
- Dataset Engineering — folded into this skill (front-loaded stage, reused by Fine-Tuning)

## Concepts covered

Golden datasets (curated + synthetic), synthetic test-case generation + human validation, RAG metrics
(faithfulness, answer relevancy, context precision, context recall — and which half of the pipeline each
blames), LLM-as-a-judge mechanics + biases, config comparison design (one variable at a time), statistical
honesty (means, distributions, sample size), comparison reports as auditable artifacts.

## Prerequisites

- RAG Project A running (the system under test — harness imports its `ask` path)
- `pip install ragas datasets pandas ollama` (+ `deepeval` optional for cross-checking judges)
- An Ollama chat model for generation AND judging (judge can be the stronger one; record which)

## Learning objectives

- Build a labeled evaluation dataset (curated + synthetic) with known-good answers and supporting chunk IDs
- Score a RAG pipeline on faithfulness / relevancy / context precision & recall and read each metric as a diagnosis
- Compare two retrieval configs and pick a winner with a scored table, not a feeling
- Validate a synthetic subset by hand and quantify judge-vs-human agreement before trusting the judge

## How it works (the pipeline)

```
Phase 2 corpus + golden seed (20–30 Q/A from RAG-A/B evals/)
  │
  ▼
dataset.py  CURATE (hand-write Q/A + must_hit chunk IDs, 50–100 target)
  + SYNTHESIZE (LLM generates (question, answer, contexts) triples from random chunks)
  + VALIDATE (human audits a sample; reject rate logged)
  ▼
golden.jsonl  [{q, reference_answer, must_hit: [chunk IDs], type: exact/paraphrase/multi/unanswerable}]
  │
  ▼
harness.py  for each item × each CONFIG: run RAG-A ask → capture (answer, retrieved contexts)
  │  configs: dense-only | hybrid | hybrid+rerank (flags reuse RAG-A CLI)
  ▼
metrics.py  Ragas scores per item: faithfulness, answer_relevancy, context_precision, context_recall
  │  (+ retrieval-only: recall@k / MRR from must_hit — no judge needed, deterministic)
  ▼
compare.py  per-config × per-metric means + distributions → scored tables + delta report
  │
  ▼
report.md + scores.csv  auditable artifact: which config won, by how much, on which question type
```

Two scoring families on purpose: deterministic retrieval metrics (recall@k from `must_hit` — free, exact)
and judge-based quality metrics (Ragas — expensive, biased, needs validation). Never judge what you can compute.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama serve && ollama pull llama3.2:latest

# Point at your Phase 2 project; score the three configs
python -m rag_eval build-dataset --corpus ../rag-corpus --out evals/golden.jsonl --synthetic 50
python -m rag_eval score --system ../Project-A-Hybrid-Search-Docs-QA --configs dense,hybrid,full
python -m rag_eval compare --scores scores.csv --report report.md
```

| Flag | Where | Default | Meaning |
| ---- | ----- | ------- | ------- |
| `--synthetic` | build-dataset | `50` | LLM-generated cases to add to curated ones |
| `--audit-sample` | build-dataset | `20` | synthetic cases to print for human accept/reject |
| `--configs` | score | `dense,hybrid,full` | which RAG-A configs to run (one variable steps) |
| `--judge` | score | `llama3.2:latest` | model used for judge metrics (log it — judges differ) |
| `--metrics` | score | `all four` | subset: `faithfulness,relevancy,c_precision,c_recall` |
| `--report` | compare | `report.md` | auditable comparison output + scored CSV |

## Project layout (files you will create)

```
rag-eval-harness/
├── requirements.txt
├── rag_eval/
│   ├── __main__.py        `python -m rag_eval` entry
│   ├── cli.py             build-dataset / score / compare subcommands
│   ├── dataset.py         curation helpers + synthetic generator + audit printer
│   ├── harness.py         runs system-under-test per item × config, captures outputs
│   ├── metrics.py         Ragas wiring + deterministic recall@k/MRR from must_hit
│   ├── judge.py           (add-on) your hand-rolled LLM judge: rubric → prompt → parse
│   └── compare.py         means/distributions/deltas → tables + report.md
├── evals/
│   ├── golden.jsonl       the golden set (curated + validated synthetic)
│   └── audit_log.md       accept/reject per audited synthetic case + reject rate
├── scores.csv             raw per-item × config × metric scores
├── report.md              comparison verdict (regenerated, committed)
└── README.md              this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — System under test frozen (before any eval code)

- [ ] Pin your Phase 2 RAG-A commit + chunk size + models. Record them at the top of `report.md`.
  An eval without a pinned system measures nothing — every later delta is meaningless if the baseline moves.
- [ ] Verify: run 5 golden queries twice, identical answers/scores. Non-determinism noted (temperature, seed).

### Phase 1 — Curated golden set (quality over quantity)

- [ ] Hand-write 50–100 Q/A pairs over your corpus, each with `reference_answer`, `must_hit` chunk IDs,
  and a `type` tag (exact-term / paraphrase / multi-fact / unanswerable).
- [ ] Cover the 4 types evenly — an eval set of only easy paraphrases is a vanity mirror.
- [ ] Verify: RAG-A answers ≥1 question per type correctly AND fails ≥1 per type (a set the system aces
  teaches nothing; a set it fully fails measures nothing — you need headroom in both directions).

### Phase 2 — Synthetic generation + human audit (scale + honesty)

- [ ] `dataset.py`: LLM generates `(question, answer, contexts)` triples from random corpus chunks
  (prompt: "write a question this chunk answers, plus the answer, plus a paraphrase variant").
- [ ] Audit: print `--audit-sample 20`, accept/reject each by hand, log reject rate + reasons in `audit_log.md`
  (typical rejects: unanswerable from chunk alone, trivially easy, wrong reference answer).
- [ ] Keep only validated synthetic cases; record final curated:synthetic ratio.
- [ ] Verify: reject rate is nonzero (a 0% reject rate means your audit is rubber-stamping — make the generator
  try harder questions until some fail audit).

### Phase 3 — Deterministic retrieval metrics first (no judge needed)

- [ ] `metrics.py`: recall@k + MRR from `must_hit` vs retrieved chunk IDs, per config. Zero LLM calls, exact numbers.
- [ ] Run the 3 configs (dense / hybrid / full); fill the retrieval half of the table below.
- [ ] Verify: hybrid recall@5 ≥ dense recall@5 on exact-term (Phase 2 claim reproduced IN HARNESS — if it doesn't
  reproduce, your harness wiring is wrong, not the claim).

### Phase 4 — Judge metrics (Ragas) + judge validation

- [ ] Wire Ragas faithfulness / answer relevancy / context precision / context recall per item × config.
- [ ] Log the judge model + version. Re-run 10 items with a DIFFERENT judge model; record disagreement rate.
- [ ] Human-validate: score 15 items yourself on faithfulness, compute agreement with the judge
  (simple %-agreement is fine — correlation coefficients are bonus).
- [ ] Verify: judge agrees with you on ≥12/15 (if not, your rubric/prompt needs work BEFORE any config
  comparison — comparing configs with an untrusted judge is numerology).

### Phase 5 — Comparison report + own-judge add-on (the deliverables)

- [ ] `compare.py`: per-config × per-metric means + per-type splits + scored CSV + `report.md` verdict
  (winner, delta size, which types moved, whether the delta exceeds run-to-run noise — re-run one config
  twice to measure noise floor).
- [ ] Add-on `judge.py`: hand-rolled LLM judge (rubric → prompt → parse → score), run it alongside Ragas,
  record where yours disagrees with Ragas and WHY (that gap analysis is the interview talking point).
- [ ] Write the fine-tune-vs-prompt-vs-RAG one-page cheat-sheet (cost/latency/drift/data/eval per option).

---

## Core experiments (fill in YOUR numbers)

### 1. Config comparison ← the core objective

| Metric (mean over golden set) | dense-only | hybrid RRF | hybrid + rerank | run-noise (±, same config ×2) |
| ----------------------------- | ---------- | ---------- | --------------- | ----------------------------- |
| recall@5 (deterministic)      |            |            |                 |                               |
| context precision             |            |            |                 |                               |
| context recall                |            |            |                 |                               |
| faithfulness                  |            |            |                 |                               |
| answer relevancy              |            |            |                 |                               |

Plus per-TYPE splits (exact/paraphrase/multi/unanswerable) — the type table is where the story lives.
**What to look for:** retrieval metrics move with hybrid; faithfulness moves with BOTH (better context →
fewer hallucinations); relevancy barely moves (it's mostly the generator). Any delta SMALLER than your
noise column is not a finding — say so.

### 2. Break it deliberately

- Score with `--configs` pointing at an EMPTY corpus index — context recall should crater while answer
  relevancy stays oddly high (fluent wrong answers — the metric split that proves why you need all four).
- Swap in an unvalidated synthetic set (skip audit) and re-score — watch scores inflate on trivial questions.
- Judge with a tiny/weak model — record the agreement collapse vs your human scores (judge quality is load-bearing).
- Delete all unanswerable questions and re-run — watch faithfulness rise artificially (eval-set gaming, concretely).

### 3. Noise-floor measurement

Run the SAME config twice (different seed if sampling, else same). Record per-metric |run1 − run2|.
This number is your significance threshold — every claimed improvement must clear it. Most skipped step in
amateur evals; doing it is what makes your report credible.

### 4. Extend it (springboard to Project B)

- Add a latency/cost column per config (embed ms + rerank ms + judge ms) — quality-per-dollar is the real leaderboard.
- Add YOUR hand-rolled judge scores as a 4th column family; where Ragas and yours diverge, adjudicate by hand.
- Port the harness to score your Agents Project A traces (task pass → judge-scored) — same harness shape, new system.

## Observations worth writing down as you go

1. **Metric→diagnosis mapping**: one real example each of low faithfulness (generation bug) vs low context
   recall (retrieval bug) from YOUR runs — this mapping is the whole point of four metrics.
2. **Synthetic reject rate + reasons** — your audit log quoted; what the generator gets wrong systematically.
3. **Judge agreement numbers** — human-vs-judge %, judge-vs-judge %; the trust boundary of your automation.
4. **Noise floor** — the same-config-twice delta that every claim must beat.
5. **Metric that didn't move** — which config change did nothing, and why that's a finding (saves future work).

## Definition of done

- Golden set (curated + audited synthetic) committed with type tags and `must_hit` IDs.
- Scored table for 3 configs on all four RAG metrics + deterministic recall@k, with a noise column.
- `report.md` names a winner with deltas that clear noise, split by question type.
- Judge validated against human scores; synthetic audit log shows nonzero reject rate.
- Add-ons present: hand-rolled judge script + one-page tradeoff cheat-sheet.

## Related — Build your own LLM Judge + tradeoff framework

Cheap add-on using the eval infra above (good interview talking point, low build cost):

- **LLM-as-Judge from scratch** (`judge.py`) — rubric (faithfulness, relevancy, style), judge prompt,
  parse + score. Compare against Ragas to see where off-the-shelf judges disagree with yours and why.
- **Tradeoff framework: fine-tune vs prompt vs RAG** — a decision doc, not code:
  - *Prompt engineering* — cheapest, fastest; use when the knowledge/behavior already exists in the base model.
  - *RAG* — use when knowledge is external, fresh, or proprietary and changes often.
  - *Fine-tuning* — use when behavior/format/style must be baked in, latency matters, or the task resists prompting.
  - Tradeoffs: cost, latency, drift, maintenance, data needs, eval surface.

Deliverable: `judge.py` in this repo + a one-page tradeoff cheat-sheet. (Interview Q&A for both lives in
Part 6 of `Interview-Questions.md` — do it after building.)

## Reference material

- Ragas: https://github.com/explodinggradients/ragas
- DeepEval (cross-check judges): https://github.com/confident-ai/deepeval
- VickyGuo0907/ai_evaluation_project: https://github.com/VickyGuo0907/ai_evaluation_project

## Next

Project B turns this harness into a CI gate: same golden set + metrics, but failing thresholds block merges.
Keep `golden.jsonl` + `metrics.py` — Project B imports them.
