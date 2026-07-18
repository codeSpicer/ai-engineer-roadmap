# AI Engineer — Project-Based Learning Roadmap

A hands-on, project-based path to becoming an AI Engineer, learning everything from scratch.
This roadmap is **linked to [roadmap.sh/ai-engineer](https://roadmap.sh/ai-engineer)**: every skill maps to
one or more nodes on that roadmap, and several projects deliberately go *beyond* it.

## How this is organized

```
Phase (folder) -> Skill (folder) -> Project (folder with README.md)
```

Work top-to-bottom. Each project has its own `README.md` with concepts, prerequisites,
learning objectives, build steps, reference repos, and a "definition of done."

## Phases & Skills

| Phase | Skills | Focus |
|-------|--------|-------|
| Phase 1 – Foundations | Foundations | Python, LLM API mechanics, prompt engineering, embeddings, vector DBs, tooling |
| Phase 2 – Building AI Apps | RAG, Agents (incl. MCP) | Build real LLM-powered applications |
| Phase 3 – Quality & Safety | Evals (incl. Dataset Eng), Guardrails | Measure and constrain those apps |
| Phase 4 – Customization & Production | Fine-Tuning (incl. Dataset Eng), LLMOps | Customize the model and ship it |

## Suggested order

`Foundations -> RAG -> Agents -> Evals -> Guardrails -> Fine-Tuning -> LLMOps`

## Mapping to roadmap.sh/ai-engineer

- **Foundations** -> Introduction, LLM basics, OpenAI API (tokens/context/pricing/JSON), Prompt Engineering, Embeddings, Vector Databases, OpenSource AI (Ollama/HF), Development Tools (LangChain/LlamaIndex)
- **RAG** -> RAG + Embeddings + Vector Databases nodes (Project B extends beyond the roadmap into Agentic/Graph RAG)
- **Agents** -> AI Agents node (ReAct, tools/function-calling) + Model Context Protocol (MCP); Project B (multi-agent) extends beyond the roadmap
- **Evals** -> Evaluation (LLM-as-judge, regression testing); Dataset Engineering folded in
- **Guardrails** -> AI Safety & Ethics node (prompt injection, bias, privacy) — hands-on enforcement
- **Fine-Tuning** -> Fine-tuning node (roadmap covers hosted fine-tuning; our projects go deeper: local QLoRA + DPO); Dataset Engineering folded in
- **LLMOps** -> Deployment / Production Architecture / Observability

## Consciously excluded (optional background reading)

- Multimodal AI (vision, audio, speech, image generation)
- Standalone Inference Optimization (partially covered inside LLMOps)

## Gap topics to add (from cohort comparison — interview-relevant)

These are not yet full projects but are tracked here so they don't get lost. Highest
priority items first.

### Agentic system design / agents-at-scale / MCP vs API tradeoffs — HIGHEST PRIORITY
No content exists for this today. This is the "real engineering" gap (designing agent
systems that hold up at scale), and what mid/senior AI eng interviews increasingly probe.
Treat as a study + design-exercise piece, not necessarily a coded project:
- Agents at scale: concurrency, idempotency, retries, timeouts, state/persistence, failure isolation.
- MCP vs API wrappers: when a formal protocol (MCP) earns its overhead vs a thin client/SDK.
- Design tradeoffs: orchestration patterns, cost/latency, observability, human-in-the-loop gates.
- Deliverable: 1–2 architecture write-ups (e.g. "design a customer-support agent for 10k req/day")
  with explicit tradeoff discussion. Build last, after Agents + LLMOps.

### Capstone project (synthesis) — HIGHEST PRIORITY
Zero synthesis project exists; the roadmap ends at Phase 4 serving with nothing tying
RAG + agents + evals + fine-tuning into one system. This is the single best portfolio
artifact — one polished capstone beats four disconnected phase projects.
- Build it LAST, reusing pieces from every earlier phase (RAG retrieval + agent orchestration
  + eval gate + a fine-tuned or guarded component).
- Deliverable: one deployed, evaluated, documented system + a metrics-for-evaluation section.
  This is the project to feature on your /reading page and resume.

### Context engineering & memory systems — MEDIUM-HIGH
See the deep-dive note in Agents Project B. Name it explicitly; don't leave it implied.

### LLM theory (attention, pre/post-training, lifecycle) — reading only
See the reading note in Foundations Project A. Articulate, don't build.

### LLM-as-Judge + fine-tune vs prompt vs RAG tradeoff — MEDIUM
See the add-on note in Evals Project A. Cheap on top of existing eval infra.

## Cross-cutting prerequisites

Python + virtual environments, Git basics, an LLM API key **or** Ollama for local models,
comfort with JSON/YAML. Fine-Tuning additionally needs a GPU (free Colab T4 works).
