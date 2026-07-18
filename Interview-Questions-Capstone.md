# Interview Questions — Gap Topic: Capstone Project (Synthesis)

HIGHEST PRIORITY. Build LAST, after every phase. This is your single best portfolio
artifact. Quiz yourself on the design before and after building.

## Gap Topic — Capstone (Pairs with everything)

**Q1. Why is the capstone more valuable than four disconnected phase projects?**
One polished system that **integrates RAG + agents + evals + fine-tuning/guardrails**
demonstrates end-to-end engineering, not just isolated skills. Recruiters screening your
/reading page or resume see *one coherent product* they can understand in a glance,
versus four half-projects. Depth + integration beats breadth here.

**Q2. What pieces should the capstone reuse from earlier phases?**
- **RAG retrieval** (Phase 2 RAG A/B) — the knowledge layer.
- **Agent orchestration** (Phase 2 Agents A/B) — the reasoning/action layer (MCP tools,
  supervisor if multi-step).
- **Eval gate** (Phase 3 Evals A/B) — quality measurement + CI gate.
- **Guardrails** (Phase 3 Guardrails A/B) — safety on I/O or dialog.
- **Fine-tuning** (Phase 4 Fine-Tuning A/B) — optional: a fine-tuned/aligned component,
  or just a guarded base model.
- **Observability + serving** (Phase 4 LLMOps A/B) — deploy it, trace it, gate deploys.

**Q3. How would you pick a problem and metrics for evaluation?**
Pick a problem with a clear user need and measurable success — e.g. a domain Q&A bot,
a research assistant, or an internal tool. Define metrics up front: faithfulness/
relevancy (evals), cost/latency per request (observability), task-success or win-rate,
and an eval-gated CI so quality is enforced. "Metrics for evaluation" is explicit in the
cohort's Week 10 — don't ship without them.

**Q4. What would you put in the capstone's README / portfolio page?**
- The problem and why it matters.
- Architecture diagram (retrieval → agent → guardrails → generation → eval gate).
- Which phase components you reused (shows range).
- Metrics: eval scores, cost/latency baselines, win-rate.
- A demo + how to run it (deployed link preferred).
- Honest limitations and what you'd improve. This is the artifact to feature prominently.

**Q5. How does the capstone tie back to the agentic system-design gap (Week 8)?**
A real capstone *is* a small agentic system: it has retrieval, orchestration, failure
modes, and scale considerations. Building it forces you to make the Week 8 design
tradeoffs concretely (MCP vs API, human-in-the-loop, cost/latency) — which is exactly
why building the capstone last, after the system-design study, makes both stronger.
