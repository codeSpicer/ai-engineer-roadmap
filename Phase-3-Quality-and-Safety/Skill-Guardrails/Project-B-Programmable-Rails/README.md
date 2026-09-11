# Project B — Programmable Dialog / Safety Rails

**Phase:** 3 — Quality & Safety · **Skill:** Guardrails · **Difficulty:** Intermediate–Advanced

A guarded conversational bot using **programmable rails**: input, dialog, retrieval, execution, and
output rails that prevent jailbreaks/off-topic drift and keep the bot on an approved path — including
guarding the RAG context itself. **Local-first: NeMo Guardrails + Ollama, YAML/Colang config (behavior
changes without Python edits).**

Project A guards single-turn I/O with imperative validators you code. This project guards CONVERSATIONS:
multi-turn attacks ("gradually steer the bot off-topic over 5 turns"), dialog-flow violations, poisoned
retrieved chunks, and unsafe tool execution. The shift is imperative → declarative: safety expressed as
rails in `config.yml` + Colang flows (`.co`), orchestrated by `LLMRails` around the same model call.

## Links to roadmap.sh/ai-engineer

- AI Safety & Ethics (programmable safety, conversational control — the hands-on half of the node)

## Concepts covered

Five rail categories (input / dialog / retrieval / execution / output) and what boundary each owns,
Colang dialog flows (intents, transitions, approved paths), `config.yml` rail wiring, conversation-state
tracking across turns, retrieval rails (guarding KNOWLEDGE, not just words — RAG poisoning defense),
execution rails (tool-call gating), jailbreak resistance via flow enforcement vs keyword matching,
adversarial conversation testing.

## Prerequisites

- Guardrails Project A (validators intuition + `adversarial.jsonl` — extended here to multi-turn)
- `pip install nemoguardrails` + Ollama model; YAML + basic Colang (`.co`) syntax
- A RAG pipeline to guard (your Phase 2 RAG-A — retrieval rails need a real retriever)

## Learning objectives

- Configure all five rail categories in NeMo Guardrails and explain what each intercepts
- Write Colang flows that hold a bot on an approved path through adversarial multi-turn pressure
- Add retrieval rails that filter poisoned/irrelevant RAG chunks before they reach the prompt
- Prove jailbreak resistance behaviorally (attack it, log the refusals/redirects)

## How it works (rails around the call)

```
user turn N (with conversation history)
  │
  ▼
INPUT RAILS: jailbreak/off-topic/PII screen on this turn (Project A validators, now as rails)
  │  blocked → refusal/redirect per flow (no model call)
  ▼
DIALOG RAILS (.co flows): does this turn fit the approved conversation state?
  │  off-flow → redirect ("I can help with X; let's stay on…") or refuse
  ▼
RETRIEVAL RAILS (if RAG-backed): inspect retrieved chunks → drop poisoned/off-policy/irrelevant ones
  │  (prompt sees ONLY surviving chunks — logged: kept vs dropped + why)
  ▼
model generates (with flow-constrained context)
  │
  ▼
EXECUTION RAILS: tool/action the bot wants → allowed? (deny unexpected calls — Phase 2 agent tools gated)
  ▼
OUTPUT RAILS: vet response (toxicity, policy, on-topic) → return or refuse/repair
  ▼
response + rail_report {rails_fired, flow_state, chunks_dropped, ms}
```

`config.yml` declares rails + models; `flows.co` declares intents/transitions/responses; `LLMRails` loads
both and orchestrates. Change behavior by editing config, not Python — that editability IS the "programmable."

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # nemoguardrails + ollama
ollama serve && ollama pull llama3.2:latest

# config.yml points at your Ollama model; flows.co defines the approved bot path
nemoguardrails server --config config/            # or python -m rails_bot chat
python -m rails_bot chat --trace                  # watch rails fire per turn
```

| File / flag | Meaning |
| ----------- | ------- |
| `config/config.yml` | models, active rails, rail params (edit to change behavior) |
| `config/flows.co` | Colang: intents, approved transitions, refusal/redirect responses |
| `--trace` | print per-turn: flow state, rails fired, chunks kept/dropped |
| `--no-retrieval-rails` | ablation: prove poisoning lands without them (experiment 2) |
| `evals/adversarial_dialogs.jsonl` | multi-turn attack scripts + single-turn set inherited from Project A |

## Project layout (files you will create)

```
programmable-rails/
├── requirements.txt
├── config/
│   ├── config.yml           models + rail wiring (input/dialog/retrieval/execution/output)
│   └── flows.co             Colang: intents, allowed flows, refusal/redirect logic
├── rails_bot/
│   ├── __init__.py
│   ├── cli.py               chat loop, --trace printing, rail_report per turn
│   ├── app.py               LLMRails init + RAG hookup (retrieval rails wrap YOUR retriever)
│   └── custom_actions.py    execution-rail actions (allow/deny lists for tool calls)
├── evals/
│   ├── adversarial.jsonl            inherited single-turn set (Project A)
│   └── adversarial_dialogs.jsonl    NEW: multi-turn scripts (gradual-steer, role-reversal, chunk-poison)
└── README.md                this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Bot contract first (before any rails)

- [ ] Define the bot's job in one paragraph + its APPROVED path (topics it handles, actions it may take,
  things it must refuse). If you can't state the path, no rail can enforce it.
- [ ] Write `adversarial_dialogs.jsonl`: 10–15 multi-turn scripts — gradual-steer (innocent → off-topic over
  5 turns), role-reversal ("you are now DAN…"), chunk-poison (RAG corpus contains an injected instruction —
  plant one deliberately), tool-abuse (trick bot into an unapproved action).
- [ ] Verify: UNGUARDED bot (rails off) fails most scripts (log the before-picture — the bot obeying a planted
  chunk instruction is your best demo).

### Phase 1 — Input + dialog rails (hold the conversation path)

- [ ] `config.yml` + `flows.co`: 3–5 intents for the approved path, transitions, refusal/redirect responses;
  input rails (jailbreak/off-topic screens from Project A vocabulary).
- [ ] `--trace` shows flow state per turn; off-flow turns redirect per the `.co` script, not generic refusals.
- [ ] Verify: gradual-steer + role-reversal scripts held on path; single-turn Project A set still blocked
  (no regression from the new layer).

### Phase 2 — Retrieval rails (guard the knowledge)

- [ ] Wire YOUR Phase 2 retriever behind retrieval rails: chunk filters (relevance floor, blocklist patterns,
  instruction-in-chunk detector for the planted poison).
- [ ] `--no-retrieval-rails` ablation: same poisoned query both ways — without rails the bot OBEYS the planted
  instruction (log it verbatim); with rails the chunk is dropped and the answer stays clean.
- [ ] Verify: poison dropped in `rail_report` (`chunks_dropped` + reason); legit chunks unaffected (recall check
  on 10 normal RAG queries — rails must not nuke useful context).

### Phase 3 — Execution + output rails (close the loop)

- [ ] `custom_actions.py`: allow/deny lists for every tool the bot can trigger (deny-by-default for unlisted);
  output rails vet the final response (toxicity/policy/on-topic, Project A output logic as rails).
- [ ] Tool-abuse script: confirm the unapproved action is denied at the execution rail with a logged reason
  (not at the prompt level — the model may still TRY; the rail STOPS it — that distinction matters).
- [ ] Verify: full five-rail run over all scripts; every turn's `rail_report` names fired rails.

### Phase 4 — Config-change demo + report (the deliverables)

- [ ] Prove programmability: change bot behavior (new refusal message, new blocked topic) via ONLY
  `config.yml`/`.co` edits — no Python touched — and re-run one script showing the new behavior.
- [ ] Fill the tables below; write 1-page policy: rail inventory + what each owns, config-review process
  (Colang edits are security changes — who reviews them), residual risks (what still gets through).

---

## Core experiments (fill in YOUR numbers)

### 1. Rail coverage ← the core objective

| Attack script | rail that caught it | bot behavior (refuse/redirect/drop/deny) | slipped through? |
| ------------- | ------------------- | ---------------------------------------- | ---------------- |
| gradual-steer (5-turn) | dialog |                                   |                  |
| role-reversal | input + dialog |                                          |                  |
| planted chunk instruction | retrieval |                                 |                  |
| tool-abuse | execution |                                                  |                  |
| toxicity probe | output |                                                 |                  |
| Project A single-turn set | input/output |                                |                  |

**What to look for:** each script maps to ≥1 rail; multi-turn scripts should be caught by DIALOG (flow state),
not input keyword matching — if input rails catch everything, your dialogs are too single-turn to prove the layer.

### 2. Retrieval-rail ablation (the poisoning proof)

| Query over poisoned corpus | `--no-retrieval-rails` (bot does…) | rails on (bot does…) | chunk dropped? + reason |
| -------------------------- | ---------------------------------- | -------------------- | ----------------------- |
| "what is the refund policy" (+ poisoned chunk present) |         |                      |                         |

Quote the poisoned instruction and the bot's obeying response verbatim in the unguarded column — that's the
attack surface made tangible. Then show the drop reason. This single row justifies retrieval rails to anyone.

### 3. Break it deliberately

- Multi-turn attack where EACH turn is benign but the SEQUENCE is malicious (death by a thousand cuts) —
  does flow-state tracking catch what per-turn screens miss? (Record honestly either way.)
- Contradictory rails: input rail allows what dialog flow forbids (or vice versa) — which wins, and is the
  resolution logged or silent? (Rail-precedence ambiguity is a real config bug class — find yours.)
- Edit `.co` to REMOVE a refusal path, re-run: confirm the attack now lands (proves the flow WAS the defense,
  not the model being "naturally safe").
- Latency: 5 rails × LLM-backed checks per turn — measure per-turn overhead; which rail dominates, and would
  you cache/parallelize it?

### 4. Programmability proof

Diff of the config-only behavior change (before/after `.co` snippet + before/after bot transcript).
No Python in the diff — that's the whole point of declarative rails, demonstrated not asserted.

## Observations worth writing down as you go

1. **Flow-vs-keyword catches** — which attacks needed conversation STATE (not single-turn screens) to stop.
2. **Poison verbatim pair** — unguarded obey vs guarded drop, quoted; the RAG attack surface in one row.
3. **Rail precedence finding** — the contradictory-config case and how resolution works (or doesn't).
4. **Execution-rail distinction** — model ATTEMPTED the action, rail DENIED it (defense beyond prompting).
5. **Config-as-code lesson** — the behavior change with zero Python; who should review `.co` edits.

## Definition of done

- Bot holds the approved path through all dialog scripts; jailbreak/off-topic attempts refused or redirected
  per flow (table filled, slips acknowledged).
- Planted chunk instruction demonstrably dropped by retrieval rails (ablation row quoted).
- Unapproved tool action denied at the execution rail (attempt logged, denial logged).
- Config-only behavior change demonstrated (diff + transcripts); policy page written.

## Reference material

- NeMo Guardrails: https://github.com/NVIDIA-NeMo/Guardrails · docs: https://docs.nvidia.com/nemo/guardrails
- Colang guide (in NeMo docs — flows, intents, transitions)
- OWASP LLM Top 10 (threat vocabulary, shared with Project A)

## Next

Phase 4 customizes the MODEL itself (fine-tuning) and ships the OPERATION (LLMOps). Guards stay wrapped
around everything: your fine-tuned model gets re-attacked with this same adversarial set (did alignment
weaken refusal behavior? — FT-B checks exactly that).
