# Interview Questions — Agents Project B: Multi-Agent Supervisor System

Complete the project, then quiz yourself. Answers are detailed.

## Phase 2 — Building AI Apps · Agents · Project B

**Q1. What problem does a multi-agent system solve that a single agent doesn't?**
A single agent juggles every role (planning, researching, writing, checking) in one
context window, which dilutes focus and burns tokens. A **multi-agent system** splits
work across specialized agents, each with a narrow role and its own context. This
improves quality (deep expertise per role), modularity (swap/replace one agent), and
often correctness (a dedicated critic catches the writer's errors).

**Q2. Explain the supervisor pattern and how it differs from a swarm.**
- **Supervisor**: a central orchestrator receives the goal, routes subtasks to
  specialized worker agents (planner, researcher, writer, critic), aggregates their
  results, and decides next steps. Centralized, easy to reason about, easy to gate.
- **Swarm**: agents coordinate more peer-to-peer without a single boss, handing off to
  each other based on capability. More resilient to a single point of failure but
  harder to debug and control.

For learning and production control, the supervisor is the clearer starting point.

**Q3. What is shared state and why is checkpointing important?**
**Shared state** is the common data structure all agents read/write (the plan, gathered
research, draft, critiques). It lets agents collaborate without passing everything
through the supervisor's prompt each time.

**Checkpointing** snapshots that state at each step so a run can **pause and resume** —
critical for long runs (don't lose progress on crash), for human review between steps,
and for replay/debugging. Without it, a failure mid-run means starting over.

**Q4. What is human-in-the-loop and where do you put the gate?**
Human-in-the-loop inserts a human approval checkpoint before a **critical or
irreversible** action — e.g. before publishing the final report, sending an email, or
spending money. You put the gate where the cost of a mistake is highest, not everywhere
(too slow). In this project it's before finalizing output, so a human can veto a bad
deliverable before it ships.

**Q5. Why use LangGraph (StateGraph) for this?**
LangGraph gives explicit **nodes** (agents/steps) and **edges** (transitions),
**reducers** to update shared state immutably, built-in **checkpointing** (pause/resume
from any node), and **interrupts** for human-in-the-loop. That's exactly the
stateful, resumable, gateable execution a multi-agent supervisor needs — far cleaner
than hand-rolling state machines.

**Q6. How does this extend beyond roadmap.sh's single-agent coverage?**
roadmap.sh's AI Agents node covers single-agent ReAct + tool calling (Project A). This
project goes further into **multi-agent orchestration** — supervision, shared state,
checkpointing, and human gates — which is the "team of agents" pattern senior roles expect.
