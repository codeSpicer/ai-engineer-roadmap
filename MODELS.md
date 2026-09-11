# Local Models — Apple Silicon Guide (M2, 16GB)

Model picks for the LEARNING builds in Phases 2–5. These are deliberately local and free —
for real projects later you'll use hosted models (OpenAI/Anthropic/etc.), and that swap is easy
by design: every project takes a `--model` flag or a single client wrapper, and Phase 1 Project A
already taught that boundary. What transfers either way is the *tier thinking*, not the weights.

## Tiers (all via `ollama pull <name>`)

| Tier | Models | ~Size (Q4) | Role it plays | On M2 16GB |
| ---- | ------ | ---------- | ------------- | ---------- |
| Embed | `nomic-embed-text` (default) · `mxbai-embed-large` (bake-off upgrade) · `bge-m3` (multilingual) | 0.3–1.2 GB | all retrieval, all phases | instant, CPU-only |
| Fast | `llama3.2:3b` | ~2 GB | smoke tests, plumbing, CLI dev loops | very fast |
| Workhorse | `qwen3:8b` (default pick) · `qwen2.5:7b` (solid tool-calling) | ~5 GB | RAG generation, router/decompose, ReAct loop, supervisor workers | comfortable, ~10–15 tok/s |
| Strong / judge | `qwen2.5:14b` (default) · `mistral-nemo:12b` · `phi4:14b` | 7–9 GB | eval judge, DPO win-rate judge, triple extraction, critic agent | fits but tight — run alone, ~5–9 tok/s |
| Reasoning traces | `deepseek-r1:8b` · `deepseek-r1:14b` | 5–9 GB | Phase 5 §3 distillation trace source, reasoning demos | slow thinker — fine for offline/batch |

## Rules for 16GB

- **One big model resident at a time.** Run with `OLLAMA_MAX_LOADED_MODELS=1`; quit heavy apps
  before 12–14B sessions.
- **Weights budget ≈ ≤10 GB** (OS + apps need the rest). 14B Q4 fits; 24B+ does not — don't try.
- **Asymmetric judging is realistic and recommended:** generate on the workhorse tier, judge on
  the strong tier. Production systems do the same (small worker, big judge).
- **Never spend the big-model budget on embeddings** — the embedding tier stays tiny regardless.

## Role → tier cheat sheet (per project)

| Project | Generator | Judge / router / critic | Notes |
| ------- | --------- | ----------------------- | ----- |
| RAG-A | workhorse | reranker is a CPU cross-encoder, not an LLM | |
| RAG-B | workhorse | router + triple-extractor: workhorse minimum; strong tier if misroutes survive prompt fixes | weakest-model stress point of Phase 2 |
| Agents-A | workhorse (tool-calling reliability is the gate) | — | `llama3.2:3b` for plumbing only |
| Agents-B | workhorse × roles | critic benefits from strong tier | |
| Evals-A | workhorse | **strong tier as judge**; hosted fallback if it fails your human-agreement check at 14B | |
| Guards-A/B | any workhorse | ML validators (PII/toxicity) are separate small models, not your chat model | |
| FT-A/B | base 3B–7B (train on Colab T4) | win-rate judge = strong tier | merged GGUF runs on CPU |
| LLMOps-A/B | whatever the app uses | — | |
| Capstone | workhorse + strong where earned | per rows above | |

## When to stop fighting a local model

Each project's own verify step is the tripwire:

- Agents-A: model emits fake-JSON tool calls *after* prompt fixes → switch models (that's written
  into the project as a finding, not a failure).
- RAG-B: router misroutes that survive prompt iteration → move router to strong tier.
- Evals-A: judge agreement <12/15 vs your human scores even at 14B → use a hosted judge **for
  scoring runs only** and record the local-vs-hosted delta. That comparison is itself an interview answer.

Everything else stays local and free.

## Looking ahead to hosted models (real projects)

The swap is one client wrapper — but keep these habits from the local tiers, they map 1:1 to
hosted size classes: small-first cascades (Phase 5 §8), judge-version pinning (Evals-B),
asymmetric generator/judge, and cost-per-request tables (LLMOps-A).
