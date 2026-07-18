# Interview Questions — LLMOps Project A: Observability + Cost Dashboard

Complete the project, then quiz yourself. Answers are detailed.

## Phase 4 — Customization & Production · LLMOps · Project A

**Q1. What do you trace in an LLM application and why?**
You trace **every LLM call and its sub-steps** as spans: inputs, outputs, model name,
token counts (prompt + completion), latency, and cost. For RAG/agents you also trace
retrieval (which chunks, scores) and agent steps (tool calls, reasoning). Why: without
traces you're blind — you can't tell if a bad answer came from retrieval, the model, or
a tool failure, and you can't debug production incidents.

**Q2. What is a span, and how do traces differ from plain logging?**
A **span** is a single unit of work (one LLM call, one tool invocation) with timing and
metadata, nested under a **trace** (one end-to-end request). Unlike flat logs, traces
show the *causal tree* — parent/child timing and order — so you see exactly where time
and tokens went. This is essential for multi-step agents where a single user request
spans many internal calls.

**Q3. Why track cost and latency per request, and what's a baseline for?**
Per-request cost/latency lets you find outliers (one query burning 10× tokens) and
attribute spend. A **baseline** (recorded normal cost/latency) is your reference for
detecting regressions — if a prompt change doubles latency or a retrieval change triples
cost, the baseline makes it visible. You can't optimize what you haven't measured.

**Q4. Why version prompts and compare them?**
Prompts are code. Changing a system prompt shifts quality, cost, and latency. Versioning
(plus the dashboard comparing versions) lets you A/B a new prompt against the old one on
real metrics and **roll back** if it regressed. Without versioning, prompt tweaks are
untracked experiments you can't reproduce or revert.

**Q5. Why self-host Langfuse via Docker instead of a SaaS?**
Self-hosting keeps your (potentially sensitive) prompt/response data in your own
infrastructure — important for privacy/compliance and cost control on a learning project.
Docker Compose makes it a one-command local stack. In production you'd weigh this against
managed SaaS convenience; the concepts (tracing, cost dashboards) are identical.

**Q6. How does observability connect to the earlier phases?**
- **RAG/Agent traces** reuse retrieval + agent concepts (Phase 2) — you're now *watching*
  them run.
- **Cost** ties to tokenization/pricing (Phase 1 Project A).
- **Prompt versioning** ties to prompt engineering (Phase 1).
- **Baselines** become the comparison point for the **eval gate** (Phase 3 Evals B) and
  **deployment** (LLMOps B). Observability is the thread that makes all prior work
  measurable in production.
