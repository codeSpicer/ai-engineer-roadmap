# Project A — Input/Output Validation Guards

**Phase:** 3 — Quality & Safety · **Skill:** Guardrails · **Difficulty:** Intermediate

Wrap an LLM endpoint with input and output **validators** — PII detection, toxic-language filtering,
competitor mentions, jailbreak patterns, and format/regex enforcement — with reject/repair/reask
fail actions, exposed as a REST service. **Local-first: Guardrails AI + Hub validators, Ollama model,
FastAPI service.**

Evals (Projects A/B) MEASURE quality after the fact. Guards ENFORCE safety in the request path, on
every call: evals say "faithfulness dropped 5% last week," guards say "this response is blocked NOW."
Both layers are required — measurement without enforcement is commentary, enforcement without measurement
is blind. This project is the enforcement half for single-turn I/O; Project B extends it to dialog flow.

## Links to roadmap.sh/ai-engineer

- AI Safety & Ethics (prompt injection, bias, privacy) — hands-on enforcement, not reading

## Concepts covered

Input vs output validation (protect-the-model vs protect-the-user), validator types (PII, toxicity,
competitor, jailbreak-regex, JSON-schema/format), fail actions (reject / repair / reask — severity ×
recoverability), repair semantics (redact vs block), reask loops + bounds, defense in depth (prompt
instruction + decoding constraint + guard layer), guard latency budget, adversarial testing as DOD.

## Prerequisites

- Foundations Project A (prompt roles, JSON mode — guards sit around those same calls)
- `uv pip install guardrails-ai fastapi uvicorn` + Hub validators (`guardrails hub install ...`)
- Ollama running (any chat model)

## Learning objectives

- Intercept and validate BOTH sides of an LLM call with multiple stacked validators
- Choose the right fail action per violation class and justify each choice
- Quantify guard cost (latency added, false-positive rate on safe traffic)
- Expose the guarded model as a REST service and prove it against adversarial inputs

## How it works (the guarded call)

```
POST /generate {prompt}
  │
  ▼
INPUT GUARDS (before any model spend):
  pii_validator ── PII found? ──→ repair (redact) or reject (block), per policy
  jailbreak_regex ── injection pattern? ──→ reject (no model call wasted)
  competitor_check ── blocked mention? ──→ reject
  ▼  (clean prompt)
ollama.chat(model, messages) → raw response
  │
  ▼
OUTPUT GUARDS (before the user sees anything):
  toxicity_validator ── toxic? ──→ reject (safe completion message)
  format_validator ── valid JSON per schema? ──→ reask (bounded retry) or reject
  competitor_check ── leaked mention? ──→ reject
  ▼  (clean response)
200 {response, guard_report: {checks, actions, ms_per_guard}}
   4xx {blocked_by, reason} on reject — with WHICH guard named (debuggability)
```

`guard_report` per request is the observability contract — every block names its guard, so tuning is
evidence-driven (which guard fires most? which false-positives?).

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
guardrails hub install hub://guardrails/pii_identification hub://guardrails/toxic_language  # + others you pick
ollama serve && ollama pull llama3.2:latest

uvicorn guarded_api:app --reload
curl -X POST localhost:8000/generate -H 'Content-Type: application/json' \
  -d '{"prompt": "my email is alice@example.com, write a haiku"}'
# → PII redacted (repair), haiku returned, guard_report shows the redact
```

| Endpoint / flag | Method | Meaning |
| --------------- | ------ | ------- |
| `/generate` | POST | guarded generation: `{prompt}` → `{response, guard_report}` |
| `/health` | GET | liveness for deploy probes (LLMOps B reuse) |
| `--fail-open/--fail-closed` | server | guard-infra-error policy: fail-CLOSED blocks (safe default), fail-open passes (availability bias — justify) |
| `--dry-run` | server | log-what-would-block mode for tuning on live traffic without blocking |

## Project layout (files you will create)

```
io-validation-guards/
├── requirements.txt
├── guards/
│   ├── __init__.py
│   ├── config.py            validator registry: which guards, what order, what fail action each
│   ├── input_guards.py      PII / jailbreak-regex / competitor on the way in
│   ├── output_guards.py     toxicity / format-schema / competitor on the way out
│   ├── actions.py           reject / repair / reask implementations + reask bound
│   └── guarded_api.py       FastAPI app: /generate + /health + guard_report
├── evals/
│   └── adversarial.jsonl    attack cases (injection, PII, toxicity probes, malformed-JSON) + safe controls
└── README.md                this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Threat list first (before any guard code)

- [ ] Write `evals/adversarial.jsonl` with 30–50 cases in 5 buckets: prompt-injection ("ignore previous
  instructions…"), jailbreak variants, PII in/out (emails, phones, IDs), toxicity probes, format-breakers
  (demands non-JSON from a JSON endpoint). PLUS 20 safe controls (normal questions incl. edge-safe ones like
  "discuss email security best practices" — guards must NOT block these).
- [ ] Verify: unguarded model FAILS most attacks (run them raw, log the failures — this is your before-picture).

### Phase 1 — Input guards (protect the model + your spend)

- [ ] `input_guards.py`: PII validator (repair=redact default; reject mode for strict fields), jailbreak-regex
  set (reject), competitor-mention check (reject). Order: cheapest regex first, ML validators after.
- [ ] `--dry-run` mode: run the full adversarial set through input guards only, log block/repair/pass per case.
- [ ] Verify: injection + PII-input cases handled per policy; ALL 20 safe controls pass (any safe block is a
  false positive — fix before adding output guards).

### Phase 2 — Output guards (protect the user + downstream contracts)

- [ ] `output_guards.py`: toxicity filter (reject + safe-completion message), JSON-schema validator
  (reask once with "respond in valid JSON" + original output as context, then reject if still malformed),
  competitor check on the way out (model must not introduce what input guards removed).
- [ ] Reask bound: max 1 re-ask (unbounded reask = unbounded spend on a stubborn model — same guard philosophy
  as max-steps/max-revisions in Phase 2).
- [ ] Verify: toxicity probes blocked; malformed-JSON responses repaired via reask (log the rescue) or cleanly
  rejected; safe controls still pass end-to-end.

### Phase 3 — Service + fail-policy hardening

- [ ] `guarded_api.py`: `/generate` returns `guard_report` (per-guard verdict + ms) on success; 4xx names the
  blocking guard + reason on reject. `/health` for probes.
- [ ] `--fail-open/--fail-closed`: kill a validator dependency (bad Hub key, offline model) and prove the
  chosen policy triggers (fail-closed default — an erroring guard must not become an open door; document where
  you'd choose otherwise and why).
- [ ] Verify: full adversarial set against the RUNNING service (not imports) — results in the table below.

### Phase 4 — Tuning report (the deliverable)

- [ ] Measure per-guard latency (p50 added ms) and false-positive rate on an expanded safe set (50+ normal prompts).
- [ ] Tune: reorder (cheap first), relax the noisiest guard with evidence, re-run. Fill the tables below.
- [ ] Write 1-page policy: per-violation fail action + rationale, fail-open/closed choice, latency budget,
  review cadence for regex/validator updates (attacks evolve — guards are maintained software).

---

## Core experiments (fill in YOUR numbers)

### 1. Adversarial block table ← the core objective

| Attack bucket (cases) | blocked/repaired | missed | false positives on safe controls |
| --------------------- | ---------------- | ------ | -------------------------------- |
| prompt injection      |                  |        |                                  |
| jailbreak variants    |                  |        |                                  |
| PII in prompt         |                  |        |                                  |
| PII in response       |                  |        |                                  |
| toxicity probes       |                  |        |                                  |
| format breakers       |                  |        |                                  |

**What to look for:** injection/jailbreak should approach 100% reject; PII should REPAIR (not block) where
policy allows — a repair rate near zero means you defaulted to reject too eagerly; ANY safe-control block is
a tuning bug, not a cost of doing business.

### 2. Fail-action justification matrix

| Violation | action chosen | why not the alternatives (in YOUR words, per case) |
| --------- | ------------- | -------------------------------------------------- |
| PII in input | repair/redact | reject would nuke legitimate requests containing contact info |
| jailbreak pattern | reject | unrepairable intent — no safe continuation exists |
| malformed JSON | reask×1 → reject | recoverable mechanically; bound prevents spend spiral |
| toxicity in output | reject | model already generated it — repair-by-edit risks residual harm |

### 3. Break it deliberately

- `--fail-open` + killed validator dep → send an attack: confirm it PASSES (the open door, demonstrated —
  this is why fail-closed is default).
- Double-encode an injection (`%69%67%6e%6f%72%65…`, unicode lookalikes) — does your regex set catch it?
  (Likely not — record the miss; layered defense is why regex alone never suffices.)
- Benign prompt containing a blocked SUBSTRING ("competitor analysis of our own product") — confirm it passes
  or fix the over-block (keyword guards vs intent guards, concretely).
- Reask-loop probe: prompt engineered to ALWAYS emit invalid JSON → confirm exactly 1 reask then reject
  (bound honored, spend capped).

### 4. Latency budget

Per-guard p50 ms + total added latency on safe traffic. State the budget (e.g. "guards add Xms p50, Y% of
total request") and which guard dominates (usually the ML toxicity/PII validators — order them last).

## Observations worth writing down as you go

1. **Repair-vs-reject boundary** — the case that made you change a default, quoted.
2. **False-positive specimens** — safe prompts blocked, and the guard relaxation each drove.
3. **Regex incompleteness proof** — the encoded injection that slipped through; why layers matter.
4. **Fail-open demonstration** — the run proving an erroring guard is a security decision, not an ops detail.
5. **Guard_report value** — a tuning decision made FROM the report (which guard fires most on live-ish traffic).

## Definition of done

- Running service: safe prompts pass with `guard_report`; each attack bucket demonstrably blocked/repaired
  (table filled, misses acknowledged with reasons).
- Zero false positives on the safe-control set (or each documented + justified).
- Fail-closed proven under dependency failure; reask bound proven under stubborn-model probe.
- Policy page written: per-violation actions, fail-open/closed stance, latency budget, maintenance cadence.

## Reference material

- Guardrails AI: https://github.com/guardrails-ai/guardrails · Hub: https://guardrailsai.com/hub
- OWASP LLM Top 10 (threat vocabulary): https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NeMo Guardrails (preview of Project B's declarative layer): https://github.com/NVIDIA-NeMo/Guardrails

## Next

Project B lifts guarding from point-validators to programmable dialog/retrieval/execution rails (NeMo).
Keep `adversarial.jsonl` — Project B attacks with the same set plus conversational multi-turn variants.
