# Project B — Multi-Agent Supervisor System

**Phase:** 2 — Building AI Apps · **Skill:** Agents · **Difficulty:** Intermediate–Advanced

A supervisor agent that orchestrates specialized agents (planner, researcher, writer, critic)
to produce a deliverable, with shared state, handoffs, and a **human-in-the-loop gate**.
Extends *beyond* roadmap.sh's single-agent coverage. **Local-first: Ollama + LangGraph,
SQLite checkpointer (no external services).**

Why a team instead of one bigger agent: a single agent juggles every role in one context window
(planning + researching + writing + checking), which dilutes focus and burns tokens on irrelevant
history. Specialists each get a narrow role prompt and see only their slice; the supervisor routes
and aggregates. A dedicated critic catches the writer's errors the writer can't see.

## Links to roadmap.sh/ai-engineer

- AI Agents node (extended)
- Extends beyond the roadmap into multi-agent orchestration

## Concepts covered

Supervisor vs swarm orchestration, role-specialized worker agents, shared state (TypedDict +
reducers), graph-based execution (LangGraph StateGraph: nodes/edges/conditional routing),
checkpointing (pause/resume/replay), interrupts / human-in-the-loop gates, trajectory inspection,
context/memory mapping (checkpoint state as persistent memory), multi-agent failure modes
(supervisor bottleneck, state corruption, runaway delegation).

## Prerequisites

- Agents Project A (agent loop intuition + reusable `tools.py`)
- LangGraph basics (`StateGraph`, reducers, `MemorySaver`/`SqliteSaver`, `interrupt`)
- Async Python basics; `uv pip install langgraph langgraph-checkpoint-sqlite ollama`

## Learning objectives

- Coordinate multiple specialized agents toward one goal via a supervisor node
- Manage shared state across agents with reducers + checkpointing (pause/resume proven, not claimed)
- Insert a human approval gate before the irreversible step and handle approve / edit / reject
- Read a full multi-agent trajectory and attribute each decision to a node

## How it works (the graph)

```
user goal ("research <topic>, produce a cited brief")
  │
  ▼
supervisor node (LLM router: reads state → emits next: planner | researcher | writer | critic | END)
  │  conditional edges from supervisor; each worker returns to supervisor
  ├─ planner     → writes plan: [steps] into state.plan
  ├─ researcher  → uses tools.py tools (search/read) → appends findings to state.research
  ├─ writer      → drafts from plan + research → state.draft (versioned: draft_v1, v2…)
  └─ critic      → reviews draft → state.critiques[] (+ verdict: APPROVE | REVISE:<notes>)
         │  REVISE → supervisor → writer again (bounded: max 2 revision rounds)
         │  APPROVE → supervisor → interrupt gate
         ▼
interrupt BEFORE finalize (human-in-the-loop):
  pause → human sees draft + critiques → approve (finalize) | edit (new draft → finalize) | reject (back to writer)
  │  checkpoint persists everything; process can die here and resume with --resume <thread_id>
  ▼
finalize node → report.md + trajectory.jsonl
```

State (`AgentState`): `goal, plan, research[], draft, draft_version, critiques[], next, revision_rounds, human_decision`.
Checkpointer: `SqliteSaver` — every node completion persists; resume = reload thread by ID.

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
ollama serve && ollama pull llama3.2:latest

# End-to-end: produces report.md + trajectory log
python -m supervisor_team run "research vector databases, produce a cited brief" --thread t1
# Kill it mid-run (Ctrl+C), then prove resume works:
python -m supervisor_team resume --thread t1
# Human gate triggers before finalize — approve / edit / reject from the CLI prompt
```

| Flag | Where | Default | Meaning |
| ---- | ----- | ------- | ------- |
| `--thread` | run/resume | required | checkpoint thread ID (pause/resume key) |
| `--max-revisions` | run | `2` | critic→writer loops before forced finalize-or-fail |
| `--auto-approve` | run | off | skip human gate (ablation only — never the default) |
| `--show-state` | run | off | print shared state after every node |
| `--resume` | resume | — | reload checkpoint thread and continue |

## Project layout (files you will create)

```
multi-agent-supervisor/
├── requirements.txt
├── supervisor_team/
│   ├── __main__.py        `python -m supervisor_team` entry
│   ├── cli.py             run / resume subcommands, human-gate prompt
│   ├── state.py           AgentState TypedDict + reducers (append/overwrite/version)
│   ├── graph.py           StateGraph: nodes, conditional edges, checkpointer wiring
│   ├── supervisor.py      router prompt → next-agent decision (+ reason)
│   ├── workers.py         planner / researcher / writer / critic prompts + tool access
│   ├── gate.py            interrupt handler: approve / edit / reject paths
│   └── trace.py           trajectory log (node, state diff, ms, model calls)
├── evals/
│   └── briefs.md          3–5 goal prompts with acceptance criteria each
└── README.md              this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Brief spec first (before any graph code)

- [ ] Write `evals/briefs.md` with 3–5 goal prompts, each with acceptance criteria:
  e.g. "cited brief on X: ≥5 distinct sources, plan followed, critic verdict APPROVE, human approved."
- [ ] Verify: criteria are checkable from `report.md` + trajectory alone. Vague criteria ("good report") → rewrite.

### Phase 1 — Workers standalone (no orchestration yet)

- [ ] `workers.py`: four role prompts (planner/researcher/writer/critic), each callable directly with fake state.
  Researcher gets Project A `tools.py` (search/read). Critic outputs `{"verdict": APPROVE|REVISE, "notes": ...}` JSON.
- [ ] `state.py`: TypedDict + reducers — `research`/`critiques` APPEND, `draft` overwrites WITH version bump,
  `revision_rounds` increments. Reducer choice IS the collaboration contract.
- [ ] Verify: run each worker by hand on canned state; critic REVISEs a deliberately bad draft with specific notes.

### Phase 2 — Graph + supervisor routing (no gate, no checkpoint yet)

- [ ] `graph.py`: nodes + supervisor conditional-edge router ("given state, next = ?" with reason).
  Linear smoke path first: planner → researcher → writer → critic → END, then enable real routing.
- [ ] Bound: `revision_rounds > max-revisions` → forced END with failure note (multi-agent max-steps equivalent).
- [ ] Verify: one goal runs end-to-end; trajectory shows supervisor decisions with reasons you agree with.
  Collect the first misroute (wrong next-agent) — prompt-fix from it.

### Phase 3 — Checkpointing: prove pause/resume (not just enable it)

- [ ] Wire `SqliteSaver`; `--thread` IDs every run.
- [ ] Kill-switch test: `run` → Ctrl+C mid-research → `resume --thread <same>` → completes with NO repeated
  completed nodes (prove from trajectory timestamps, not faith).
- [ ] Verify: trajectory after resume shows continuity (state intact, no re-planning, no lost research).

### Phase 4 — Human-in-the-loop gate (the irreversible-step guard)

- [ ] `interrupt()` before finalize: CLI shows draft + latest critique → human: `approve` / `edit:<text>` / `reject:<reason>`.
  Approve → finalize; edit → finalize edited version; reject → back to writer with reason (consumes a revision round).
- [ ] `--auto-approve` ablation flag (for the experiment below — default stays gated).
- [ ] Verify: all three paths exercised at least once (approve a good draft, edit a mediocre one, reject a bad one
  and watch the writer address the reason).

### Phase 5 — Trajectory report (the deliverable)

- [ ] Run all briefs; fill the table below (gated runs; plus one auto-approved run per brief for comparison).
- [ ] Save one fully annotated trajectory: per node, what it read from state, what it wrote, why the supervisor
  routed there next.
- [ ] Write 1-page verdict: where tokens/steps went, supervisor failure modes observed, gate catch rate,
  what you'd change before trusting this unsupervised.

---

## Core experiments (fill in YOUR numbers)

### 1. Brief acceptance table ← the core objective

| Brief (goal) | plan followed? | sources (count) | critic rounds | human decision | resume tested? |
| ------------ | -------------- | --------------- | ------------- | -------------- | -------------- |
| 1. …         |                |                 |               |                |                |
| 2. …         |                |                 |               |                |                |
| 3. …         |                |                 |               |                |                |

**What to look for:** critic rounds should cluster at 1–2; 0 rounds means the critic is rubber-stamping
(weaken the draft deliberately to check it bites); hitting max-revisions means writer↔critic thrash —
read that trace, it's your best debugging lesson.

### 2. Gate ablation: gated vs `--auto-approve`

Run the same brief both ways. Record: defects shipped ungated that the gate caught (wrong facts, missing
citations, off-brief sections). One caught defect justifies the gate's existence — quote it verbatim.

### 3. Break it deliberately

- Kill the process mid-run → `resume`: confirm zero repeated nodes from the trajectory.
- `--max-revisions 0` with a bad first draft — confirm forced END with failure note, not infinite writer↔critic loop.
- Feed the critic a draft with an invented citation — does it catch it? (If not, your critic prompt is the bug.)
- Corrupt one state field mid-run (empty `research`, `--show-state` to watch) — which downstream node fails first,
  and does the supervisor recover or derail?

### 4. Supervisor vs single-agent cost

Run one brief on this team AND as a single Project-A agent with all tools. Compare: total tokens,
wall-clock, acceptance criteria met. The team should win quality and lose cost — record both numbers.
If the team loses both, your roles are too fine-sliced (try merging writer+planner).

## Observations worth writing down as you go

1. **Supervisor misroutes** — verbatim reason strings and your router-prompt fixes.
2. **Critic bite rate** — how often REVISE vs APPROVE; evidence it's not rubber-stamping.
3. **Gate catches** — the exact defects a human caught that no node did (the case for human-in-the-loop).
4. **Resume proof** — timestamps showing no repeated work across the kill boundary.
5. **State-design lessons** — which reducer choice (append vs overwrite vs version) prevented a real bug.

## Definition of done

- The team produces a coherent multi-step deliverable (`report.md`) meeting the brief's acceptance criteria.
- A working human gate stands before finalize; approve/edit/reject all demonstrated.
- A killed run resumes from its checkpoint thread with no repeated completed nodes (trajectory-proven).
- Brief table is filled; you can narrate any run node-by-node from the trajectory alone.

## Related deep-dive — Context Engineering & Memory Systems

This project touches memory (shared state + checkpointing) but doesn't name it as a first-class topic.
Treat the following as a **standalone study piece** (cheap, no full project) — it's a 2026 hiring buzzword
and worth being explicit about:

- **Context engineering** — what to put in the prompt/window per step (not prompt *tweaking*, but *engineering*
  the right context: retrieval, compression, summarization, scratchpad).
- **Memory types** — short-term (in-context), working (scratchpad/state), long-term (vector store / KV / graph).
  When to use each; write-through vs read-through.
- **Memory architectures** — buffering, summarization-based compaction, semantic recall, self-editing memory (MemGPT-style).
- **Failure modes** — context overflow, stale memory, distraction, cost of over-long context.

Deliverable: a short written comparison of memory strategies and when you'd pick each, plus a note on how this
project's checkpointing maps to "long-term memory." (Interview Q&A for this is Part 6 of
`Interview-Questions.md` — do the Q&A after writing the comparison.)

## Reference material

- LangChain DeepAgents Playbook (Level 3.5, Supervisor/Swarm): https://github.com/sdivyanshu90/LangChain-DeepAgents-Playbook
- ashishpatel26/500-AI-Agents-Projects (LangGraph multi-agent): https://github.com/ashishpatel26/500-AI-Agents-Projects
- LangGraph docs (StateGraph, checkpointer, interrupt): https://langchain-ai.github.io/langgraph/

## Next

Phase 3 puts this team under test: eval harnesses (does the brief actually meet criteria?) and guardrails
(does the researcher refuse malicious instructions?). Keep the trajectory logs — evals consume them.
