# Phase 5 — Synthesis & Frontier

**Phase:** 5 — Synthesis & Frontier · **Difficulty:** Advanced · **Build this LAST (mostly)**

Companions in this folder: `Interview-Questions.md` (Parts 1–3: capstone, agents-at-scale, and the
full-arc synthesis — do it against your live build) and `Production-At-Scale.md` (how the capstone
and frontier techniques run as production products — read after the capstone is live).

Phases 1–4 taught isolated skills. Phase 5 does the two things that turn skills into a hireable
profile: (1) a **capstone** that fuses every phase into one deployed, evaluated system — the single
best portfolio artifact, and explicitly the highest-priority gap in this roadmap; (2) **frontier
tracks** for the crucial topics the four phases deliberately left out (multimodal docs, reasoning-model
training, long-context economics, inference optimization, routing, security red-teaming, agent evals,
the feedback flywheel). Each track is scoped to a concrete deliverable, not a reading list.

## How to use this phase

- **Capstone (§1) goes last** — after Phases 1–4. It reuses their code; building it earlier means
  rebuilding it later.
- **Frontier tracks (§2–§11) feed the capstone.** Pick the 2–3 tracks your capstone idea needs FIRST
  (e.g. multimodal docs for a PDF-assistant capstone, routing for a cost-sensitive one), build the
  capstone with them inside, then do the rest in any order.
- **Every track ends in an artifact** (table, demo, config, or doc) you can show. No track is "read about X."

## Links to roadmap.sh/ai-engineer

- Beyond the roadmap by design. The closest nodes: Production Architecture (capstone assembles it),
  AI Agents + RAG (frontier extends both), Fine-tuning (reasoning-model track extends it).
- Closes the roadmap's own gap list: capstone + agentic-system-design were the two HIGHEST-priority
  "no content exists" items — they live here now (§1, §2). Interview Q&A for both lives in this
  folder (`Interview-Questions.md`, Parts 1–2) — do that Q&A alongside these builds.

---

## §1 — Capstone: one deployed, evaluated, guarded system (CENTERPIECE — build last)

**Why first on your resume:** one polished system integrating RAG + agents + evals + guards (+ a tuned
component) demonstrates end-to-end engineering; four disconnected phase projects demonstrate coursework.
Recruiters understand one product in a glance.

**Pick a problem with a real user and measurable success** — domain Q&A bot, research assistant with
citations, internal support copilot. Requirements: needs RETRIEVAL (not answerable from weights), needs
MULTI-STEP work (agent earns its keep), has SAFETY stakes (guards matter), and you can define METRICS
up front (faithfulness, task success, $/request, p99).

**Reuses (phase → component — import, don't rebuild):**

| Capstone layer | From | What you import |
| -------------- | ---- | --------------- |
| Knowledge | Phase 2 RAG-A/B (+ §7 multimodal if PDFs are scanned) | hybrid retriever, reranker, graph if multi-hop |
| Reasoning/action | Phase 2 Agents-A/B | ReAct loop or supervisor team + MCP tools |
| Quality measurement | Phase 3 Evals-A | golden set method + judge harness, extended to YOUR task |
| Merge blocking | Phase 3 Evals-B | thresholds + workflow, retargeted at capstone metrics |
| Safety | Phase 3 Guards-A/B | validators + rails around every I/O boundary |
| Model | Phase 4 FT-A/B (or base + guards if tuning didn't earn it) | SFT/DPO checkpoint with win-rate + refusal receipts |
| Operations | Phase 4 LLMOps-A/B | traces, baselines, serving, canary + rollback |

**Build phases:**

- [ ] **0. Scope + metrics doc (1 page):** user, problem, why RAG+agent (not prompting alone — headroom
  proof), metrics with targets (faithfulness ≥ X, task-success ≥ Y, $/request ≤ Z, p99 ≤ W), adversarial
  set for the safety story. If metrics aren't writable now, the scope is wrong.
- [ ] **1. Assemble the system:** retrieval + agent + generation wired end-to-end, UNGUARDED, UNGATED —
  prove the happy path on 10 pilot tasks with traces. Ugly allowed; working required.
- [ ] **2. Guard it:** validators + rails (Phase 3) around all boundaries; run YOUR adversarial sets
  (single-turn + dialog + poisoned-chunk) against the ASSEMBLED system (composition creates new holes —
  log the one your unit-guarded parts missed).
- [ ] **3. Tune-or-justify:** either a fine-tuned/DPO component with before/after receipts, or a written
  "tuning didn't earn it" verdict with the headroom numbers (both are defensible; unevidenced is not).
- [ ] **4. Harness + gate:** golden set for the CAPSTONE TASK (not RAG subtask), scored table, CI gate
  blocking merges, red-teamed (one sabotage that goes red, logged).
- [ ] **5. Serve + canary:** deploy via YOUR LLMOps-B path (probes, digest-pinned image, canary with
  auto-rollback on YOUR baselines). Keep it live — a URL beats screenshots.
- [ ] **6. Write-up + demo:** README with problem, architecture diagram, phase-reuse table, metrics
  (eval scores + cost/latency + win-rate), live demo link, honest limitations + "what I'd improve."
  Feature this on your resume/reading page. Do `Interview-Questions.md` Part 1 against it.

**Definition of done:** live URL + green CI on main + canary demonstrated + metrics page + adversarial table +
a 5-minute demo you can narrate (happy path, one attack blocked, one trace read, one metric explained).

---

## Frontier tracks (crucial, uncovered in Phases 1–4)

### §2 — Agentic systems at scale (design exercises)

**Why crucial:** interviews for mid/senior roles probe "design an agent for 10k req/day" — concurrency,
idempotency, retries, timeouts, state, failure isolation, cost/latency, HITL placement. No phase built this
muscle; design write-ups do.
**Do:**
- [ ] Write-up 1: "customer-support agent, 10k req/day" — orchestration choice (supervisor vs swarm, with
  YOUR Phase-2 cost table cited), per-step timeouts + retry-with-backoff policy, idempotency keys on every
  write tool, state store, failure-isolation boundaries, cost math from YOUR $/request rows.
- [ ] Write-up 2: "MCP vs thin API wrappers for OUR tools" — decide per tool in YOUR stack when the protocol
  earns its hop (shared/multi-language → MCP; single-use → thin client), with YOUR MCP latency measurement.
- [ ] Do `Interview-Questions.md` Part 2 against YOUR write-ups.
**Deliverable:** two architecture docs with explicit tradeoff tables. **Extends:** Agents-A/B + LLMOps-A/B.

### §3 — Reasoning-model post-training (GRPO intuition + distillation)

**Why crucial:** 2025–26's defining shift — reasoning models (R1-style) trained with outcome-based RL
(GRPO/RLOO), and small models DISTILLED from their traces. Fine-tuning phases never touched RL or reasoning.
**Do:**
- [ ] Read the GRPO intuition (group-sampled advantages, no critic model — contrast with PPO from DPO Q&A)
  and write a 1-page "DPO vs GRPO, when each" note.
- [ ] Distill: collect chain-of-thought traces from a strong reasoning model on 200 of YOUR domain tasks →
  SFT YOUR small model on (question, trace, answer) → before/after on held-out REASONING accuracy (not format).
  Local trace source: `deepseek-r1:8b` (or `:14b`, alone on 16GB) emits readable reasoning traces — no API
  budget needed (see root `MODELS.md`).
- [ ] Report the distillation tax (general capability + refusal re-checks — same discipline as FT-A/B).
**Deliverable:** distilled checkpoint + reasoning-accuracy table + DPO-vs-GRPO note. **Extends:** FT-A/B.

### §4 — Long context vs RAG (the stuff-or-retrieve tradeoff)

**Why crucial:** 128k–1M windows + prompt caching changed the economics — sometimes stuffing beats retrieving,
and "lost in the middle" punishes naive stuffing. No phase measured this boundary.
**Do:**
- [ ] Lost-in-the-middle probe: place the answer chunk at 5 positions in a 100k prompt, record accuracy per
  position on YOUR tasks (quote the curve).
- [ ] Caching: enable prompt caching on YOUR system prompt + stable prefix; measure $/request and TTFT delta.
  (The $ delta needs a hosted API — Anthropic/OpenAI. Fully-local proxy: measure TTFT on a warm vs cold Ollama
  context for the same long prefix; the accuracy and latency halves of this track are local either way.)
- [ ] Tradeoff table: same 20 questions via (a) full-context stuff, (b) YOUR RAG pipeline — accuracy, cost,
  latency per route, with a routing rule ("<N tokens stable prefix → stuff; else retrieve").
**Deliverable:** position-accuracy curve + caching delta + routing rule with numbers. **Extends:** RAG-A/B, LLMOps-A.

### §5 — Production retrieval upgrades

**Why crucial:** real corpora need more than dense+BM25: access control (users must NOT retrieve docs they
can't read — the enterprise RAG blocker), better ranking signals, poison resistance.
**Do (pick two):**
- [ ] ACL-aware retrieval: permission tags in chunk metadata → pre-filter by user role; prove with a test
  (unauthorized query returns nothing, authorized returns hits — the compliance demo).
- [ ] Late-interaction rerank (ColBERT-style) OR embedding bake-off on MTEB-flavored YOUR-golden eval:
  swap `nomic-embed-text` vs `mxbai-embed-large` vs BGE-M3, scored recall table (Phase-1 method, grown up).
- [ ] Corpus provenance: write-path controls (who can add docs) + scheduled poison-scan; re-run YOUR
  poisoning ablation against the hardened path.
**Deliverable:** ACL proof log + embedding comparison table (or ColBERT delta). **Extends:** RAG-A/B, Guards-B.

### §6 — Inference optimization (benchmark YOUR stack)

**Why crucial:** serving cost IS model choice + runtime + quantization. LLMOps-B served; it never benchmarked.
**Do:**
- [ ] Benchmark YOUR fine-tune across runtimes (Ollama vs llama.cpp vs vLLM if GPU): tokens/s, TTFT, peak RAM
  at 1/4/16 concurrency — one table.
- [ ] Quantization ladder: Q8 → Q4_K_M → Q3 on YOUR held-out (task accuracy + a human-read sample per rung) —
  find YOUR cliff (where quality falls off, quoted).
- [ ] Write the serving recommendation for YOUR capstone (runtime + quant + concurrency limit, with the rows).
**Deliverable:** benchmark table + ladder table + one-paragraph serving spec. **Extends:** FT-A/B, LLMOps-B.

### §7 — Multimodal document intelligence

**Why crucial:** real documents are scanned PDFs, tables, figures, slide decks — Phase-2 RAG assumes clean
text, so every real corpus breaks it. Document understanding is the most common "RAG failed in production" cause.
**Do (pick one pipeline, end to end):**
- [ ] Vision-parse: 20 scanned/table-heavy PDFs → vision model (Qwen-VL-class local or API) → markdown with
  tables preserved → YOUR RAG index → golden Q/A over table cell values (the query class text-RAG scores zero on).
- [ ] Meeting-notes pipeline: Whisper audio → transcript → chunk → corpus (timestamps as metadata; cite with
  timestamps — new citation flavor).
- [ ] Image search add-on: CLIP embeddings beside text embeddings; mixed query demo ("find the diagram of X").
**Deliverable:** parsed corpus + table-question accuracy table + before/after vs text-only extraction.
**Extends:** RAG-A/B (new corpus modality), Evals-A (new question type).

### §8 — Model routing & cost engineering (cascades, caches)

**Why crucial:** biggest models for every query is a budget fire; routing is how production stays solvent.
Touched in theory (agentic design), never built.
**Do:**
- [ ] Cascade: small model answers → confidence gate (YOUR Evals-A rubric as the gate) → escalate to big model
  on fail; measure escalation rate, quality parity vs big-only, $/request delta on YOUR golden set.
- [ ] Semantic cache: exact + near-duplicate query cache (embedding threshold) in front of YOUR RAG; hit-rate
  and savings at YOUR replayed volume.
- [ ] Monthly math v2: recompute LLMOps-A projections WITH cascade + cache (the "10× traffic ≈ X× cost" update).
**Deliverable:** cascade parity table + cache hit-rate + updated budget paragraph. **Extends:** RAG-A/B, LLMOps-A.

### §9 — Security red-teaming (beyond guardrails)

**Why crucial:** guards defend known classes; red-teaming FINDS the unknowns. Supply-chain (poisoned HF
models/datasets), indirect injection via tools (MCP server content as attack vector), sandbox escapes.
**Do:**
- [ ] Indirect-injection suite: 10 attacks delivered THROUGH tool outputs / retrieved chunks / MCP responses
  (never the user prompt) against YOUR agent + guards; log which layer caught each (or didn't).
- [ ] Tool-sandbox review: attempt the Phase-2 breakouts again (path escape, unlisted tool, exfiltration via
  tool args) against HARDENED config; document residual escapes with owners.
- [ ] Supply-chain checklist for YOUR artifacts (base-model hash pinned? dataset sources logged? GGUF built by
  you or downloaded? — each with status).
**Deliverable:** indirect-attack table + sandbox review + signed checklist. **Extends:** Guards-A/B, Agents-A.

### §10 — Agent evals (trajectories, not just answers)

**Why crucial:** Phase-3 evals score RAG outputs; agent QUALITY lives in trajectories (tool choice, step
efficiency, recovery). Ungraded trajectories rot exactly like ungraded RAG did.
**Do:**
- [ ] Trajectory rubric: per-task scores for tool-selection correctness, step efficiency (vs YOUR optimal-step
  annotations), recovery quality, final-answer grounding — applied to 15 saved YOUR-agent traces (hand-score 5,
  judge-score 15, agreement check — Evals-A method, new object).
- [ ] Function-calling accuracy subset (Berkeley leaderboard style, 20 cases over YOUR tools): selection + args
  exactness per model (ties to YOUR model-swap table).
- [ ] Gate one agent metric in YOUR Evals-B workflow (e.g. "recovery-rate on error tasks ≥ floor").
**Deliverable:** trajectory scoreboard + tool-accuracy table + one gated agent metric. **Extends:** Agents-A/B, Evals-A/B.

### §11 — Feedback flywheel (serve → collect → DPO → redeploy)

**Why crucial:** the loop that compounds: production ratings become preference pairs become a better model
through YOUR gates. Every phase built separately; nobody closed the loop.
**Do:**
- [ ] Collect: thumbs-up/down + correction capture on YOUR served app (traces carry the feedback — LLMOps-A
  join), 100+ rated outputs.
- [ ] Convert: corrections → (prompt, chosen=corrected, rejected=original) DPO pairs via YOUR audit bar;
  train; win-rate vs deployed model.
- [ ] Redeploy THROUGH the gates (eval gate green → canary → promote) and log the full loop time (rating to
  production in X days — the flywheel velocity metric).
**Deliverable:** flywheel run log (counts, win-rate, loop time) + the redeployed model. **Extends:** FT-B,
LLMOps-A/B, Evals-B.

---

## Suggested order (and what feeds what)

```
frontier picks for YOUR capstone idea (2–3 tracks, e.g. §7+§5 for a docs-assistant)
        │
        ▼
§1 CAPSTONE (with §2 write-ups alongside — design thinking while building)
        │
        ▼
remaining frontier tracks (any order — each is self-contained)
        │
        ▼
root Q&A files as the final oral exam (`Interview-Questions.md` Parts 1–3, in this folder)
```

**Portfolio order:** capstone FIRST (demo + metrics), then one frontier artifact that shows range (red-team
report, benchmark table, or flywheel log), then phase projects as depth links.

## Reference material (entry points, not exhaustive)

- Microsoft GraphRAG (community-detection scale-up of §5 graphs): https://github.com/microsoft/graphrag
- vLLM + LoRA serving (multi-adapter, §6 depth): https://docs.vllm.ai/
- LiteLLM gateway (multi-provider failover, §8 companion): https://github.com/BerriAI/litellm
- OWASP LLM Top 10 + AI Exchange (threat vocabulary, §9): https://owasp.org/www-project-top-10-for-large-language-model-applications/
- τ-bench / SWE-bench (agent-eval inspiration, §10): https://github.com/sierra-research/tau-bench
- EU AI Act risk tiers + model cards (governance reading for regulated-domain capstones): https://artificialintelligenceact.eu/
