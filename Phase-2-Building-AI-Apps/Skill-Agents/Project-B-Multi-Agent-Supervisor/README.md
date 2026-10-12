# Project B — Multi-Agent Supervisor System

**Phase:** 2 — Building AI Apps · **Skill:** Agents · **Difficulty:** Intermediate–Advanced

A supervisor agent that orchestrates specialized agents (planner, researcher, writer, critic)
to produce a deliverable, with shared state, handoffs, and a **human-in-the-loop gate**.
Extends _beyond_ roadmap.sh's single-agent coverage. **Local-first: Ollama + LangGraph,
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

- Agents Project A DONE (you finished it 2026-09-28 — carry over: `tools.py` + `dispatch` error-as-string
  contract, `SYSTEM`-prompt discipline, `--max-steps` guard thinking, trace-narration habit).
  Copy `tools.py` verbatim into this project — do not rewrite it.
- Python 3.11+ via uv (`uv venv --python 3.11` — system Python 3.9 is too old for current LangGraph).
- LangGraph basics (`StateGraph`, reducers, `SqliteSaver`, `interrupt`); `uv pip install langgraph langgraph-checkpoint-sqlite ollama`
- Ollama with `qwen3.5:4b` (already pulled for Project A — reuse it; upgrade to `qwen3:8b` only if
  supervisor misroutes survive prompt fixes — tier guide: root `MODELS.md`)

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
uv venv --python 3.11 && source .venv/bin/activate
uv pip install -r requirements.txt        # langgraph + langgraph-checkpoint-sqlite + ollama
ollama serve                              # if not already running (model already pulled for Project A)

# Scaffold: copy Project A's proven tools in — researcher tool access, verbatim
cp ../Project-A-ReAct-Tool-Agent-with-MCP/react_agent/tools.py ./supervisor_team/pa_tools.py

# End-to-end: produces report.md + trajectory log
python -m supervisor_team run "research vector databases, produce a cited brief" --thread t1
# Kill it mid-run (Ctrl+C), then prove resume works:
python -m supervisor_team resume --thread t1
# Human gate triggers before finalize — approve / edit / reject from the CLI prompt
```

`requirements.txt`:

```
langgraph
langgraph-checkpoint-sqlite
ollama
```

| Flag              | Where      | Default  | Meaning                                             |
| ----------------- | ---------- | -------- | --------------------------------------------------- |
| `--thread`        | run/resume | required | checkpoint thread ID (pause/resume key)             |
| `--max-revisions` | run        | `2`      | critic→writer loops before forced finalize-or-fail  |
| `--auto-approve`  | run        | off      | skip human gate (ablation only — never the default) |
| `--show-state`    | run        | off      | print shared state after every node                 |
| `--resume`        | resume     | —        | reload checkpoint thread and continue               |

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

**Sat AM, ~1–2h. Do this in a text editor — no Python, no LangGraph yet.**

Write `evals/briefs.md` with 3–5 goal prompts, each naming its OWN acceptance criteria.
This file is Project A's `evals/tasks.md` grown up: same idea (expected behavior stated BEFORE
code), but the "expected tool sequence" becomes a checkable deliverable spec.

Concrete starter — adapt the topics, keep the shape:

```markdown
# Briefs (acceptance criteria checked from report.md + trajectory alone)

## B1 — "Research vector databases, produce a cited brief"

- plan followed (trajectory shows planner → researcher → writer → critic in order)
- ≥5 distinct sources cited in report.md
- critic verdict APPROVE before the gate
- human decision: approve
```

Then 2–4 more at the same shape, varying the pressure: one topic your `qwen3.5:4b` knows well
(easy path), one obscure topic (forces real `web_search` use), one with an explicit constraint
("under 300 words", "must compare 3 options" — tests the writer/critic loop).

- [x] Write `evals/briefs.md` with 3–5 goal prompts, each with acceptance criteria:
      e.g. "cited brief on X: ≥5 distinct sources, plan followed, critic verdict APPROVE, human approved."
- [x] Verify: criteria are checkable from `report.md` + trajectory alone. Vague criteria ("good report") → rewrite.
      The test: hand this file to a stranger — could they score your `report.md` pass/fail without asking you anything?

**Done looks like:** `evals/briefs.md` committed, every criterion decidable from artifacts alone.

### Phase 1 — Workers standalone (no orchestration yet)

**Sat PM + Sun, ~4–6h. The big build weekend — but still zero LangGraph imports.**

Each worker is a thin wrapper around the ONE pattern you already mastered: build messages,
call `ollama.chat(model="qwen3.5:4b", ...)`, return structured text. If Phase 2 of Project A
clicked, this is the same muscle with different system prompts.

Build order (each independently testable — do them in this order):

1. **`state.py` first (~30 min).** The `AgentState` TypedDict + reducers. Reducer cheat sheet:
   - `research: Annotated[list, operator.add]` — APPEND (many findings accumulate)
   - `critiques: Annotated[list, operator.add]` — APPEND (history of criticism)
   - `draft: str` — plain overwrite, BUT bump `draft_version` alongside (versioning is manual)
   - `revision_rounds: int` — overwrite with `state["revision_rounds"] + 1`
   - Everything else (`goal`, `plan`, `next`, `human_decision`) — plain overwrite
2. **`workers.py` planner + writer (~1h).** Pure prompt functions: planner takes `goal` → returns
   a `[steps]` list; writer takes `plan + research` → returns draft text. Test both from a REPL
   with canned dicts — no graph needed.
3. **Researcher (~1h).** Imports `pa_tools` (your copied `tools.py`) and runs a MINI ReAct loop:
   reuse the shape of Project A's `loop.run()` — prompt → `ollama.chat(tools=...)` →
   `dispatch()` → observation → repeat, capped at ~5 steps. This is why Phase 3 of Project A
   matters: the researcher's tool errors must come back as retryable strings, not crashes.
4. **Critic (~1h).** Takes `draft` → returns `{"verdict": "APPROVE" | "REVISE", "notes": "..."}`
   via `format="json"` (same trick as Project A's structured output). The kill-test: feed it a
   deliberately bad draft (invented citation, off-brief section) and confirm REVISE with SPECIFIC
   notes naming the defect. A critic that APPROVEs garbage is the #1 silent failure of this
   project — prove yours bites NOW, not in Phase 5.

- [ ] `workers.py`: four role prompts (planner/researcher/writer/critic), each callable directly with fake state.
      Researcher gets Project A `tools.py` (search/read). Critic outputs `{"verdict": APPROVE|REVISE, "notes": ...}` JSON.
- [ ] `state.py`: TypedDict + reducers — `research`/`critiques` APPEND, `draft` overwrites WITH version bump,
      `revision_rounds` increments. Reducer choice IS the collaboration contract.
- [ ] Verify: run each worker by hand on canned state; critic REVISEs a deliberately bad draft with specific notes.

**Trap to avoid:** the critic that rubber-stamps. If `APPROVE` comes back on your poisoned draft,
weaken the draft FURTHER or sharpen the critic prompt — do not proceed until REVISE fires with specifics.

**Done looks like:** `python -c "from supervisor_team.workers import planner, researcher, writer, critic"`
runs all four on canned state; the bad-draft REVISE is saved as your first trajectory specimen.

### Phase 2 — Graph + supervisor routing (no gate, no checkpoint yet)

**Weekend 2, ~4–5h. First LangGraph code — deliberately WITHOUT persistence, so routing bugs
can't hide behind checkpoint confusion.**

Two-step construction (resist wiring everything at once):

1. **Linear smoke path first (~1h).** Hardcode the sequence planner → researcher → writer →
   critic → END with plain `add_edge` calls. Run brief B1. If the happy path doesn't produce a
   `report.md`, the bug is in worker wiring, NOT routing — fix it here while routing is out of
   the picture.
2. **Supervisor routing (~2–3h).** Add `supervisor.py`: reads state, emits
   `{"next": "planner|researcher|writer|critic|END", "reason": "..."}` via `format="json"`,
   wired as a conditional edge with all workers returning to supervisor. The `reason` string is
   not decoration — it's your Phase-5 misroute evidence and your interview answer. Bound it:
   `revision_rounds > max-revisions` → forced END (this is Project A's `--max-steps` guard,
   one level up).

- [ ] `graph.py`: nodes + supervisor conditional-edge router ("given state, next = ?" with reason).
      Linear smoke path first: planner → researcher → writer → critic → END, then enable real routing.
- [ ] Bound: `revision_rounds > max-revisions` → forced END with failure note (multi-agent max-steps equivalent).
- [ ] Verify: one goal runs end-to-end; trajectory shows supervisor decisions with reasons you agree with.
      Collect the first misroute (wrong next-agent) — prompt-fix from it.

**Compile WITHOUT a checkpointer** (`graph.compile()` bare). Persistence arrives in Phase 3 —
adding it now mixes two failure surfaces.

**Misroute triage (your `qwen3.5:4b` will misroute — plan for it):** log the verbatim `reason`
string, sharpen the supervisor prompt from THAT string (not from theory), re-run. If misroutes
survive two prompt iterations, that's the documented tripwire for upgrading the supervisor call
to `qwen3:8b` — record it as a finding, same as Project A's model-swap experiment.

**Done looks like:** B1 runs supervisor-routed end-to-end, trajectory narratable node-by-node,
first misroute logged with its prompt fix.

### Phase 3 — Checkpointing: prove pause/resume (not just enable it)

**Weekend 2 Sun or Weekend 3 Sat, ~2–3h. Small phase — mostly one wiring change + the kill test.**

The change itself is small: `SqliteSaver.from_conn_string("checkpoints.sqlite")` passed to
`graph.compile(checkpointer=...)`, plus `{"configurable": {"thread_id": ...}}` threaded through
every `invoke` from `cli.py`. The LEARNING is the kill test — "resume works" must be proven from
trajectory timestamps, never assumed from "it didn't crash."

Kill-switch protocol (follow it exactly — this is the experiment):

1. `run --thread t1` on a brief with a slow researcher (obscure topic = several `web_search` calls).
2. Ctrl+C mid-research. Note the wall-clock time.
3. `resume --thread t1` — SAME id (a new id silently starts a fresh thread; that's the #1
   "resume doesn't work" false alarm).
4. Open the trajectory: completed nodes must appear ONCE with pre-kill timestamps; post-resume
   entries continue the sequence. Any repeated planner/researcher node = resume proved FALSE —
   debug the thread plumbing before proceeding.

- [ ] Wire `SqliteSaver`; `--thread` IDs every run.
- [ ] Kill-switch test: `run` → Ctrl+C mid-research → `resume --thread <same>` → completes with NO repeated
      completed nodes (prove from trajectory timestamps, not faith).
- [ ] Verify: trajectory after resume shows continuity (state intact, no re-planning, no lost research).

**Done looks like:** kill-test trajectory saved, zero repeated nodes highlighted, resume declared
PROVEN (not "seems to work").

### Phase 4 — Human-in-the-loop gate (the irreversible-step guard)

**Weekend 3, ~3–4h. The phase with the most new LangGraph API surface — take it slow.**

`gate.py` holds an `interrupt()` node placed between critic-APPROVE and finalize. Mechanics that
bite (all three are in the linked LangGraph guide — read that section before coding):

- `interrupt()` needs the Phase-3 checkpointer or it raises — another reason Phase 3 comes first.
- The node function re-runs from the top on resume: keep everything before `interrupt()` side-effect-free.
- The human's decision arrives as the `interrupt()` return value — write it into
  `state["human_decision"]` yourself; it doesn't land in state automatically.

Exercise all three paths on REAL drafts (not toy inputs): approve a good B1 draft, edit a
mediocre one (your edit text becomes the finalized version — confirm it in `report.md`), reject
a bad one with a reason and watch the writer address THAT reason (consumes a revision round).
`--auto-approve` exists ONLY for the Phase-5 ablation — never your default run mode.

- [ ] `interrupt()` before finalize: CLI shows draft + latest critique → human: `approve` / `edit:<text>` / `reject:<reason>`.
      Approve → finalize; edit → finalize edited version; reject → back to writer with reason (consumes a revision round).
- [ ] `--auto-approve` ablation flag (for the experiment below — default stays gated).
- [ ] Verify: all three paths exercised at least once (approve a good draft, edit a mediocre one, reject a bad one
      and watch the writer address the reason).

**Done looks like:** three gate transcripts saved (one per path), the reject→rewrite visibly
addressing your reason string.

### Phase 5 — Trajectory report (the deliverable)

**Weekend 3 Sun, ~2–3h. No new code — run everything, fill every table, write the verdict.**

Run ALL briefs gated, plus one `--auto-approve` run per brief for experiment 2. The annotated
trajectory is graded on specificity: per node, what it READ from state, what it WROTE, and WHY
the supervisor routed there next (quote the `reason` strings — they're the whole point of
supervisor routing). The 1-page verdict must name a supervisor failure mode you OBSERVED
(misroute with verbatim reason + your prompt fix), your gate catch rate, and what you'd change
before running unsupervised.

- [ ] Run all briefs; fill the table below (gated runs; plus one auto-approved run per brief for comparison).
- [ ] Save one fully annotated trajectory: per node, what it read from state, what it wrote, why the supervisor
      routed there next.
- [ ] Write 1-page verdict: where tokens/steps went, supervisor failure modes observed, gate catch rate,
      what you'd change before trusting this unsupervised.
- [ ] Do the memory-architecture write-up + `Interview-Questions.md` Part 6 (context-engineering deep-dive),
      then the full Q&A Parts 1–5 out loud against your trajectories.

**Done looks like:** brief table filled, gate-ablation row quoted with a real caught defect,
cost table (experiment 4) showing team-wins-quality / loses-cost, Q&A answerable from YOUR runs.

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

- **Context engineering** — what to put in the prompt/window per step (not prompt _tweaking_, but _engineering_
  the right context: retrieval, compression, summarization, scratchpad).
- **Memory types** — short-term (in-context), working (scratchpad/state), long-term (vector store / KV / graph).
  When to use each; write-through vs read-through.
- **Memory architectures** — buffering, summarization-based compaction, semantic recall, self-editing memory (MemGPT-style).
- **Failure modes** — context overflow, stale memory, distraction, cost of over-long context.

Deliverable: a short written comparison of memory strategies and when you'd pick each, plus a note on how this
project's checkpointing maps to "long-term memory." (Interview Q&A for this is Part 6 of
`Interview-Questions.md` — do the Q&A after writing the comparison.)

## Reference material

- LangGraph from scratch pt.1 (state/channels/reducers, checkpointers, `interrupt()` GOTCHAS — read
  before Phase 4): https://matt-harrison.com/posts/9-5-26-langgraph-part-1/
- LangChain DeepAgents Playbook (Level 3.5, Supervisor/Swarm): https://github.com/sdivyanshu90/LangChain-DeepAgents-Playbook
- ashishpatel26/500-AI-Agents-Projects (LangGraph multi-agent): https://github.com/ashishpatel26/500-AI-Agents-Projects
- LangGraph docs (StateGraph, checkpointer, interrupt): https://langchain-ai.github.io/langgraph/

## Next

Phase 3 puts this team under test: eval harnesses (does the brief actually meet criteria?) and guardrails
(does the researcher refuse malicious instructions?). Keep the trajectory logs — evals consume them.
