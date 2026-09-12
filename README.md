# AI Engineer — Project-Based Learning Roadmap

A hands-on, project-based path to becoming an AI Engineer, learning everything from scratch.
This roadmap is **linked to [roadmap.sh/ai-engineer](https://roadmap.sh/ai-engineer)**: every skill maps to
one or more nodes on that roadmap, and several projects deliberately go *beyond* it.

## How this is organized

```
Phase (folder) -> Skill (folder) -> Project (folder with README.md + Interview-Questions.md)
```

Work top-to-bottom. Each project has its own `README.md` (concepts, prerequisites,
learning objectives, phased build steps with checkboxes, core experiments with tables to fill,
reference repos, definition of done) and `Interview-Questions.md` (in-depth Q&A grounded in
YOUR measured numbers — complete the project, then quiz yourself out loud from it).

Companions: [MODELS.md](./MODELS.md) (local model tiers for Apple-silicon laptops — which model
plays which role, and when a hosted fallback is right) and [PACING.md](./PACING.md)
(weekend-by-weekend schedule for Phases 2–5, built for a 9–5 + weekends rhythm).

## Phases & Skills

| Phase | Skills | Focus |
|-------|--------|-------|
| Phase 1 – Foundations | Foundations | Python, LLM API mechanics, prompt engineering, embeddings, vector DBs, tooling |
| Phase 2 – Building AI Apps | RAG, Agents (incl. MCP) | Build real LLM-powered applications |
| Phase 3 – Quality & Safety | Evals (incl. Dataset Eng), Guardrails | Measure and constrain those apps |
| Phase 4 – Customization & Production | Fine-Tuning (incl. Dataset Eng), LLMOps | Customize the model and ship it |
| Phase 5 – Synthesis & Frontier ([production scaling](./Phase-5-Synthesis-and-Frontier/Production-At-Scale.md)) | Capstone + frontier tracks | One deployed end-to-end system + crucial topics beyond Phases 1–4 |

## Suggested order

`Foundations -> RAG -> Agents -> Evals -> Guardrails -> Fine-Tuning -> LLMOps -> Capstone (+ 2–3 frontier tracks) -> remaining frontier`

## Mapping to roadmap.sh/ai-engineer

- **Foundations** -> Introduction, LLM basics, OpenAI API (tokens/context/pricing/JSON), Prompt Engineering, Embeddings, Vector Databases, OpenSource AI (Ollama/HF), Development Tools (LangChain/LlamaIndex)
- **RAG** -> RAG + Embeddings + Vector Databases nodes (Project B extends beyond the roadmap into Agentic/Graph RAG)
- **Agents** -> AI Agents node (ReAct, tools/function-calling) + Model Context Protocol (MCP); Project B (multi-agent) extends beyond the roadmap
- **Evals** -> Evaluation (LLM-as-judge, regression testing); Dataset Engineering folded in
- **Guardrails** -> AI Safety & Ethics node (prompt injection, bias, privacy) — hands-on enforcement
- **Fine-Tuning** -> Fine-tuning node (roadmap covers hosted fine-tuning; our projects go deeper: local QLoRA + DPO); Dataset Engineering folded in
- **LLMOps** -> Deployment / Production Architecture / Observability
- **Phase 5** -> Beyond the roadmap by design: the capstone assembles everything above into one
  deployed system (see `Phase-5-Synthesis-and-Frontier/README.md`), and frontier tracks cover what
  Phases 1–4 deliberately left out (reasoning-model post-training, long-context economics, multimodal
  docs, inference optimization, routing/cascades, ACL-aware retrieval, security red-teaming, agent evals,
  feedback flywheel).

## Consciously folded into Phase 5 (not standalone phases)

- Multimodal document intelligence (§7: vision-parse, audio pipeline, CLIP search — the production slice
  of multimodal that RAG systems actually need)
- Inference optimization (§6: runtime × quant benchmarking on YOUR stack — the applied slice)

## Gap topics — status (were open items, now placed)

Prior cohort comparison flagged two HIGHEST-priority gaps with zero content. Both now live in
`Phase-5-Synthesis-and-Frontier/` (README §1–§2 + `Interview-Questions.md` Parts 1–2) — quiz against those.

### Agentic system design / agents-at-scale / MCP vs API tradeoffs — PLACED (Phase 5 §2 + Q&A Part 2)
Design write-ups (not a coded project): agents-at-scale mechanics (concurrency, idempotency, retries,
timeouts, state, failure isolation), MCP-vs-thin-client decisions per YOUR measured hop cost, centralized
vs decentralized orchestration, cost/latency, HITL gates.
- Do alongside the capstone (design thinking while building).

### Capstone project (synthesis) — PLACED (Phase 5 §1 + Q&A Part 1)
Build LAST: one deployed, evaluated, guarded system reusing every phase (RAG + agent + eval gate +
guards + tuned component + observability + canary) + metrics page + demo. The resume centerpiece.

### Context engineering & memory systems — COVERED (Agents Project B, README deep-dive + Interview Q&A Part 6)

### LLM theory (attention, pre/post-training, lifecycle) — COVERED (Foundations Project A, reading note + Q&A)

### LLM-as-Judge + fine-tune vs prompt vs RAG tradeoff — COVERED (Evals Project A, `judge.py` add-on + Interview Q&A Part 6)

## Cross-cutting prerequisites

Python + [uv](https://docs.astral.sh/uv/) for envs and installs (`uv venv`, `uv pip install`),
Git basics, an LLM API key **or** Ollama for local models,
comfort with JSON/YAML. Fine-Tuning additionally needs a GPU (free Colab T4 works).
Local model picks per role (generator vs judge vs router) for 16GB Macs live in
[MODELS.md](./MODELS.md); the weekend pacing plan lives in [PACING.md](./PACING.md).
