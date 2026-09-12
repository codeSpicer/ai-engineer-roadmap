# Project A — Observability + Cost Dashboard

**Phase:** 4 — Customization & Production · **Skill:** LLMOps · **Difficulty:** Intermediate

Instrument an existing LLM app (your RAG or agent) with tracing, logging, and a
token/latency/cost dashboard using self-hosted Langfuse. **Docker Compose stack, Langfuse SDK +
framework callbacks — every LLM call, retrieval step, and tool invocation becomes a span.**

Until now your timing data lived in ad-hoc CLI prints (`--trace`, per-stage ms). This project makes
it durable, queryable, and visual: the same numbers, but per-request, per-user, per-prompt-version,
retained — so regressions, cost spikes, and quality incidents become visible instead of anecdotal.
Observability is the thread that makes ALL prior phases measurable in production: eval scores mean
little without the cost/latency they arrived with, and deploys (Project B) are blind without baselines.

## Links to roadmap.sh/ai-engineer

- Production Architecture / Observability (traces, metrics, prompt management)

## Concepts covered

Traces vs spans vs logs (causal trees, not flat lines), span taxonomy for LLM apps (generation /
retrieval / rerank / tool / guard / judge), token accounting (prompt vs completion, per model pricing),
cost attribution (per request, user, prompt version), latency decomposition (p50/p99 per span),
prompt versioning + A/B comparison, baselines (what "normal" costs), alert-worthy signals (spikes,
error-rate, guard-fire-rate), PII care in logged payloads (redaction before retention).

## Prerequisites

- A working app to instrument (Phase 2 RAG-A or Agents-A — richer step structure = better spans)
- Docker + Docker Compose (Langfuse self-host); `uv pip install langfuse` (+ framework callback if LangChain)
- Phase 1 token/pricing intuition (cost math reuses it at scale)

## Learning objectives

- Trace every LLM call INCLUDING retrieval/agent/guard sub-steps as nested spans
- Build a cost + latency dashboard and record defended baselines per request type
- Version two prompts and compare quality/cost/latency side by side in the dashboard
- Define the alert rules you'd ship (spike thresholds, error budget) from YOUR measured data

## How it works (instrumentation map)

```
your app (RAG-A ask / ReAct run)
  │  @observe() wrappers / callbacks at each boundary:
  ▼
trace per request (trace_id = request id)
  ├── span: router/loop-iteration (agent) — model, tokens, ms
  ├── span: retrieval {dense ms, bm25 ms, fusion ms} + chunk IDs + scores (as span metadata!)
  ├── span: rerank {model, candidates, ms}
  ├── span: generation {model, prompt_version, prompt_tokens, completion_tokens, ms, $}
  ├── span: guards {verdicts, ms} (if guarded app)
  └── scores attached: eval metrics / user feedback → same trace (quality + cost TOGETHER)
        │
        ▼
Langfuse (Postgres + UI): filter by prompt_version / user / model;
  dashboards: $/request, p50/p99 latency, tokens/request, guard-fire-rate, score trends
```

The scores-on-traces join is the money feature: "prompt v2 cut faithfulness 0.85→0.78 while cost stayed
flat" is visible in ONE view — quality and spend stop living in different tools.

## Setup

```bash
# Langfuse self-host (one command, local Postgres inside)
git clone https://github.com/langfuse/langfuse.git && cd langfuse && docker compose up -d
# UI at localhost:3000 → create project → copy public/secret keys

export LANGFUSE_PUBLIC_KEY=... LANGFUSE_SECRET_KEY=... LANGFUSE_HOST=http://localhost:3000
uv pip install langfuse

# Instrument: wrap boundaries, tag prompt versions, run traffic, open dashboard
python -m myapp ask "what is the refund window?"      # traced automatically
python scripts/replay_golden.py --tag baseline        # 30 requests → your baseline
```

| Item | Meaning |
| ---- | ------- |
| `@observe()` / callbacks | span boundaries — generation, retrieval, rerank, tool, guard, judge |
| `prompt_version` tag | `v1` vs `v2` on every generation span (comparison dimension) |
| `replay_golden.py` | replays Evals-A golden set as tagged traffic (baseline + A/B load) |
| redaction hook | PII stripped BEFORE spans leave the app (privacy — implement + prove) |
| baselines.yml | pinned p50/cost/score per request type (Project B's deploy alarms read this) |

## Project layout (files you will create)

```
observability-dashboard/
├── docker-compose.override.yml  (if you customize the Langfuse stack)
├── instrument/
│   ├── __init__.py
│   ├── tracing.py           Langfuse init, @observe wrappers, span helpers
│   ├── redaction.py         PII strip before logging (tested, proven)
│   └── prompt_registry.py   versioned prompts: get("grounded-answer", "v2")
├── scripts/
│   ├── replay_golden.py     golden set → tagged traffic (baseline + A/B)
│   └── export_baselines.py  compute baselines.yml from Langfuse API
├── baselines.yml            pinned cost/latency/score per request type
├── ALERTS.md                alert rules + thresholds + who gets paged (deliverable)
└── README.md                this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — App + traffic source first (before any dashboards)

- [ ] Pick the app (RAG-A recommended — retrieval spans are the interesting half) and its replayable traffic:
  Evals-A golden set via `replay_golden.py` (deterministic load you already trust).
- [ ] Verify: 5 manual requests work end-to-end (instrumentation never debugs a broken app — app green first).

### Phase 1 — Span instrumentation (every boundary, with metadata)

- [ ] `tracing.py`: wrap generation / retrieval (chunk IDs + scores as metadata — NOT just timing) /
  rerank / tool / guard verdicts. One trace per request, nested spans, model + version tags on each.
- [ ] Verify: single request in Langfuse UI shows the FULL tree with timings that sum sensibly; retrieval span
  lists the actual chunk IDs (a trace without chunk IDs can't diagnose RAG — check this explicitly).

### Phase 2 — Cost math + redaction (money + privacy before sharing anything)

- [ ] Token→cost per model (prompt vs completion rates, Phase 1 pricing lesson at scale); `$` on every
  generation span; per-request rollup.
- [ ] `redaction.py`: PII probe (send email/phone/adversarial PII through) → Langfuse shows REDACTED, raw
  values nowhere in the stack (query Postgres to prove it — screenshots of absence don't count, queries do).
- [ ] Verify: cost of 30 replayed requests matches hand-computed expectation within 10% (your pricing table
  is correct before any baseline is trusted).

### Phase 3 — Baselines + prompt A/B (the comparison muscle)

- [ ] `replay_golden.py --tag v1-baseline` (30+ requests) → `export_baselines.py` → `baselines.yml`
  (p50/p99 latency, $/request, tokens/request, per request TYPE — single-hop vs multi-hop differ 3×, don't average them).
- [ ] `prompt_registry.py`: version the system prompt (`v1` → `v2`: e.g. stricter grounding instruction);
  replay both tags; compare in-dashboard AND export the numbers (quality via Evals-A scores attached to traces).
- [ ] Verify: v1-vs-v2 table filled (quality Δ, cost Δ, latency Δ) with a ship/no-ship verdict you'd defend.

### Phase 4 — Alerts + handoff (the production deliverables)

- [ ] `ALERTS.md`: rules from YOUR baselines (e.g. "$/request > 2× baseline for 15min," "guard-fire-rate spike,"
  "p99 > SLO," "faithfulness-on-sampled-traces < floor") — each with threshold source (which baseline row),
  severity, and runbook first-step.
- [ ] Prove one alert fires: replay with a sabotaged prompt (Evals-B red-team) and show the signal moving
  (screenshot + the trace IDs).
- [ ] Verify: Project B can consume `baselines.yml` + `ALERTS.md` directly as deploy-gate thresholds and canary
  alarms (handoff tested, not assumed — import them in LLMOps-B setup).

---

## Core experiments (fill in YOUR numbers)

### 1. Baseline table ← the core objective

| Request type | n | p50 latency | p99 latency | $/request | tokens/request | dominant span |
| ------------ | - | ----------- | ----------- | --------- | -------------- | ------------- |
| single-hop RAG |  |           |             |           |                |               |
| multi-hop / agentic |  |      |             |           |                |               |
| no-retrieval (direct) |  |     |             |           |                |               |
| agent multi-step |  |          |             |           |                |               |

**What to look for:** multi-hop ≈ 2–3× single-hop cost (matches Phase 2 forensics — now durable);
dominant span is generation, then rerank (same ordering as CLI prints — consistency check on your instrumentation);
per-TYPE rows differ enormously — a single blended average would lie.

### 2. Prompt A/B (v1 vs v2)

| Version | faithfulness (traces w/ scores) | $/request | p50 latency | verdict |
| ------- | ------------------------------- | --------- | ----------- | ------- |
| v1 |  |  |  |  |
| v2 (stricter grounding) |  |  |  | ship / no-ship + why |

A quality gain that doubles cost is a BUSINESS decision — state it as one (this table is the artifact
promo/review committees actually read).

### 3. Break it deliberately

- Sabotaged-prompt replay (drop grounding instruction): which dashboard panel moves FIRST (score trace?
  guard-fire-rate? cost?) — that ordering is your incident-detection playbook.
- PII probe ×3 forms (plain, obfuscated, in retrieved chunk): confirm redaction in UI + Postgres for all three
  (the chunk path is the one teams forget — prove yours).
- Kill the Langfuse stack mid-traffic: app must DEGRADE (log-and-continue), never crash on observability
  failure (observability is advisory, not load-bearing — prove the ordering).
- Replay at 5× volume: which span's p99 degrades first (usually generation queueing — capacity finding).

### 4. Cost projection

Monthly $ at 3 traffic levels (1k / 100k / 10M requests) from YOUR $/request, split by request type mix.
Name the cheapest lever per level (caching at low volume, smaller embedder/reranker mid, batching + model
right-sizing at scale). One paragraph a manager could budget from.

## Observations worth writing down as you go

1. **CLI-vs-dashboard consistency** — Phase 2 `--trace` ms vs span ms for the same query (agreement = trust).
2. **Type-split necessity** — the blended-average lie, quantified (single vs multi $/request ratio).
3. **A/B verdict reasoning** — the ship/no-ship call with quality-vs-cost math attached.
4. **Redaction proof** — the Postgres queries showing absence (privacy claims need evidence, not intent).
5. **First-moving panel** — sabotage replay: which signal leads, which lags (your future on-call runbook seed).

## Definition of done

- Every request type traced end-to-end with nested spans incl. chunk IDs + scores; Langfuse UI navigable.
- Cost math verified ±10% by hand; PII redaction proven in UI + database.
- `baselines.yml` pinned per request type; v1-vs-v2 A/B table with verdict.
- `ALERTS.md` written from baselines with a proven-firing demo; handoff to Project B tested.

## Reference material

- Langfuse: https://github.com/langfuse/langfuse · docs: https://langfuse.com/docs
- OpenTelemetry concepts (spans/traces — Langfuse implements the same model): https://opentelemetry.io/docs/concepts/signals/traces/

## Next

Project B SERVES the model and GATES deploys on everything measured here: baselines become canary alarms,
eval scores become deploy blocks. Keep `baselines.yml` + `ALERTS.md` — Project B imports them.
