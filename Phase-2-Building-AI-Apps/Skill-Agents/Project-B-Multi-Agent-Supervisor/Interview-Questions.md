# Interview Questions — Multi-Agent Supervisor System (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual code and the numbers you measured** — brief tables, trajectories,
resume proofs, gate catches, cost comparisons. Quote your brief table; that separates "drew boxes and
arrows" from "ran a team."

---

## Part 1: Fundamentals — "Why a team instead of one agent?"

**Q1. What problem does a multi-agent system solve that a single ReAct agent doesn't? Give me a failure you SAW in Project A that a team fixes.**

**Answer:** A single ReAct agent (Project A) holds EVERY role in one context window and one prompt: planning
the approach, executing searches, drafting, and self-checking — with full history regurgitated every step.
Three concrete pains you measured in Project A that motivate the split: (a) ROLE CONFUSION — the trace shows
the model planning while it should be executing (or vice versa); one prompt can't hold "be creative" and "be
adversarial" sharply at once. (b) CONTEXT BLOAT — step 8's prompt contains steps 1–7 verbatim, tokens scaling
quadratically; specialists see only their slice. (c) NO REDUNDANCY — the writer can't catch its own errors;
a dedicated critic with a different prompt (and different failure modes) catches what the writer is blind to.

The team (`workers.py`: planner / researcher / writer / critic) gives each role a narrow prompt, narrow state
slice, and narrow success criterion. Quality goes up (depth per role + adversarial review), cost goes up too
(more LLM calls — your Q16 table states both). "Split when the single-agent trace shows role-confusion or
context bloat" is the honest trigger — not "multi-agent is better" in the abstract.

**Q2. Walk me through one brief end to end, naming every file that touches it.**

**Answer:** Take "research vector databases, produce a cited brief" with `--show-state`:
(1) `cli.py run --thread t1` creates the thread and invokes `graph.py`'s StateGraph with initial
`AgentState{goal}` from `state.py`; (2) SUPERVISOR node (`supervisor.py`) reads state → emits
`{"next": "planner", "reason": "no plan yet"}` → conditional edge routes; (3) PLANNER (`workers.py`)
writes `state.plan=[steps]` → returns to supervisor; (4) supervisor → RESEARCHER (has Project A `tools.py`:
search/read) → appends findings to `state.research[]` via the APPEND reducer; (5) supervisor → WRITER →
`state.draft` (overwrite + version bump to `draft_v1`); (6) supervisor → CRITIC → appends
`{"verdict": REVISE, "notes": [...]}` to `state.critiques[]`; (7) supervisor reads REVISE →
routes WRITER again (`revision_rounds=1`, bounded by `--max-revisions 2`); (8) second CRITIC → APPROVE →
supervisor → `gate.py` INTERRUPT: checkpoint persists, CLI shows draft + critique, human approves →
(9) FINALIZE writes `report.md` + `trace.py` appends the trajectory JSONL. `trace.py` logs every node (state
diff, ms, model calls) — narrate any run node-by-node from that log alone.

**Q3. Supervisor vs swarm — what's the actual structural difference, and why did you start with supervisor?**

**Answer:** SUPERVISOR (`supervisor.py` + conditional edges in `graph.py`): ONE central router sees the full
state and decides `next` after every step; workers never call each other — all traffic hub-and-spoke through
the supervisor. SWARM: peer-to-peer handoffs — the researcher decides "hand to writer now" without asking a
boss; no single node has global view. Tradeoff: supervisor is EASY TO REASON ABOUT (every routing decision is
one logged `reason` string in one place — your misroute debugging in Q8 works because of this), easy to GATE
(one choke point before finalize), but a BOTTLENECK and single point of failure (supervisor prompt bug derails
everything; every step pays a router LLM call). Swarm is resilient and parallel-friendly but debugging is
distributed — "why did the writer run twice?" has no single log line. For learning AND production control,
centralized routing with a logged reason is the right start; decentralize only with evidence the supervisor is
the bottleneck (your cost table would show router-call share).

---

## Part 2: Orchestration — "Routing, roles, and revision bounds"

**Q4. How does the supervisor decide what's next? What exactly does it read and emit?**

**Answer:** `supervisor.py` is an LLM call over COMPACT state (goal + plan status + research count + draft
version + latest critique verdict + revision_rounds — NOT full research text, that's context economics), with
a system prompt listing the legal transitions (planner→researcher→writer→critic→{writer|gate|END}) and 1–2
few-shot routings. Output is forced JSON `{"next": ..., "reason": "..."}`. The conditional edge in `graph.py`
dispatches on `next`. Your misroute collection (Q8) is the eval: each wrong `next` logged with its reason
string, prompt-fixed from the verbatim string. Known confusion pair to quote: critic-APPROVE-with-nits vs
REVISE — does the supervisor send nits back to the writer (wasting a revision round) or to the gate? Record
which way yours errs and the prompt line you changed.

**Q5. Why four roles — planner, researcher, writer, critic? What breaks if you merge or split further?**

**Answer:** Each role isolates a CONFLICTING objective: planner optimizes COMPLETENESS of approach, researcher
optimizes RECALL of evidence, writer optimizes FLUENCY of draft, critic optimizes CORRECTNESS adversarially.
Merging writer+critic collapses the adversarial tension (self-review is rubber-stamping — your Q10 critic-bite
measurement degrades); merging planner+writer recreates Project A's role-confusion. Splitting further
(fact-checker + stylist + sourcer…) multiplies LLM calls per brief with diminishing returns — your cost table
(Q16) shows the per-role token share, so you can point at which split would be pure overhead. The four-role
split is minimal-viable-separation: plan / gather / produce / verify — the same four phases as any engineering
doc process, which is why it generalizes. If your data shows one role contributing nothing (e.g. planner on
trivial briefs), say so — "planner is skippable for single-source briefs" is a finding, not a failure.

**Q6. The writer↔critic loop could spin forever. What EXACTLY bounds it, and what happens at the bound?**

**Answer:** `revision_rounds` in state, incremented per critic→writer cycle, checked against
`--max-revisions 2` (your `--max-revisions 0` break-run proves the mechanism: forced END with a failure note,
no infinite loop). At the bound the supervisor routes to END-with-failure (or to the human gate with a
"unresolved critiques" flag — state your choice and why). This is Project A's `--max-steps` guard lifted to
the team level: unbounded agency converts to bounded spend + debuggable trace. Production reading: the bound
is a COST control (each round = writer call + critic call + full-state context) and the thrash case (writer
ignores critique, critic repeats REVISE — your table should contain one) is the most instructive trace you own:
read it to learn whether the bug is writer-obedience or critique-vagueness ("be better" critiques never
converge — critiques must be ACTIONABLE, cite the offending passage).

---

## Part 3: State & Checkpointing — "The collaboration contract"

**Q7. What is shared state mechanically, and why are reducers the real design decision?**

**Answer:** `state.py` defines `AgentState` (TypedDict: `goal, plan, research[], draft, draft_version,
critiques[], next, revision_rounds, human_decision`) — the ONLY channel workers share; workers never message
each other directly. REDUCERS define the write semantics per field and ARE the collaboration contract:
`research`/`critiques` APPEND (parallel-safe accumulation, nothing lost), `draft` OVERWRITES with version bump
(single current truth + history via `draft_v1/v2` — no silent clobbering), `revision_rounds` INCREMENTS
(monotonic bound). Wrong reducer = real bug class: APPEND on `draft` leaves workers reading stale versions
(your corrupt-state break-run demonstrates which downstream node fails first); OVERWRITE on `research` loses
findings across resume. In interviews: "reducers are the concurrency + persistence contract; the TypedDict is
just the shape." LangGraph enforces them at every node commit — that's what makes resume SAFE (replayed state
merges identically, not approximately).

**Q8. Checkpointing: what is persisted, when, and prove resume works — don't just claim it.**

**Answer:** `graph.py` wires `SqliteSaver`; LangGraph persists the FULL state snapshot after EVERY node
completion, keyed by `--thread` ID. Proof protocol (your kill-switch test): `run --thread t1` → Ctrl+C
mid-research → `resume --thread t1` → completes. The PROOF is in the trajectory: post-resume log shows state
intact (plan present, research[] preserved with pre-kill timestamps), NO repeated completed nodes (no second
planner entry, no re-search of completed queries), continuation from the exact next node. Quote the timestamps.
What checkpointing buys: crash recovery (long runs survive), human-gate pausing (process can DIE at the
interrupt and resume tomorrow — the gate is just a named pause), replay/debugging (re-run from any node with
edited state). Without it every failure mid-run restarts from zero — at team-scale cost (5+ LLM calls per
brief) that's not an inconvenience, it's a budget fire.

**Q9. Your corrupt-state break-run: you emptied `research` mid-run. Which node failed first, and did the supervisor recover or derail?**

**Answer:** (Quote YOUR run.) Expected shape: writer fails first (drafts from empty research → thin,
citation-free draft) OR critic catches it (REVISE with "no sources" notes — the good outcome). Supervisor
behavior is the actual test: a good router sees `research=[]` + writer output and routes BACK to researcher
(recovery — state-aware routing works); a brittle one pushes the empty draft to the gate (derail — routing
ignores state content, only stage order). Either result is a finding: recovery proves state-conditioned
routing; derail proves your supervisor prompt needs a "validate preconditions before advancing" rule (add it,
re-run, record the fix). This experiment is the state-management equivalent of Project A's error-as-
observation test — the system meeting violated expectations and showing its character.

---

## Part 4: Human-in-the-Loop — "The gate before the irreversible step"

**Q10. What is human-in-the-loop here, precisely — and why THIS position in the graph?**

**Answer:** `gate.py` calls LangGraph `interrupt()` AFTER critic-APPROVE and BEFORE finalize: the run pauses
(checkpointed — safe to walk away), CLI presents draft + latest critique, human chooses
approve → finalize as-is / edit:<text> → finalize edited version / reject:<reason> → back to writer
(consuming a revision round). Position rationale: the gate sits where MISTAKE COST is highest — finalize
publishes `report.md`, the deliverable the world sees; everything upstream is cheap revision. Gating every
node would strangle throughput (human latency per step); gating nothing ships critic-missed defects (your
ablation Q11 has the receipt). Rule: gate IRREVERSIBLE or EXTERNAL actions (publish, send, spend, deploy) —
internal drafts stay machine-speed. Your three-path verification (approve a good draft, edit a mediocre one,
reject a bad one and watch the writer address the reason) proves all branches, not just the happy path.

**Q11. Gate ablation: same brief, gated vs `--auto-approve`. What did the human catch?**

**Answer:** (Quote YOUR defect, verbatim.) Expected shape: the ungated run ships something the critic passed
but a human rejects — invented citation the critic didn't verify, off-brief section, wrong emphasis, stale
fact. One quoted defect justifies the gate's existence more than any theory: "auto-approve shipped [X]; the
gate caught it because [Y]." Also record the COST: gate adds human-latency (minutes–hours) to every brief —
so the verdict includes WHEN you'd remove it (low-stakes internal drafts, after critic bite-rate earns trust
over N briefs) and when never (external publish, money, safety-relevant content). "Gated by default,
auto-approve as a measured ablation, never as the default" is the production posture.

**Q12. Approve / edit / reject — what does each do to state, exactly?**

**Answer:** APPROVE: sets `human_decision=approve`, routes to finalize untouched. EDIT: human text becomes the
new `draft` (version bump — the human is just another writer node with full authority, and the edit is logged
in the trajectory like any state diff). REJECT with reason: appends the reason to `critiques[]`
(indistinguishable from a critic REVISE downstream — deliberate design, so the writer handles human feedback
through the same path), increments `revision_rounds`, routes to writer. Elegance worth stating: the gate
doesn't need special downstream plumbing because rejection REUSES the revision machinery — three human choices,
one existing loop. Your rejected-then-fixed trace (writer visibly addressing the human reason) is the demo.

---

## Part 5: Memory, Cost & Production — "Context engineering, bills, and breakage"

**Q13. How does this project's state/checkpointing map to "memory systems" and "context engineering"? (2026 buzzword question — nail it.)**

**Answer:** Three mappings, precise: (a) CHECKPOINTED STATE = long-term/working memory persisted — the team
resumes tomorrow with yesterday's research intact, which is exactly "memory across sessions"; your kill-switch
proof IS a memory-persistence demo. (b) SUPERVISOR'S COMPACT VIEW = context engineering in action — the router
sees summaries/counts/verdicts, NOT full research text; workers see slices (writer: plan + research, critic:
draft + notes). Deciding WHAT each node sees is context engineering (right information, no drowning) as
opposed to prompt engineering (wording). (c) FULL HISTORY NOWHERE — no node holds the entire trajectory;
the trajectory log is write-only audit, not context. Failure modes transfer directly: context OVERFLOW (full
research into the supervisor prompt — your bloat measurement), STALE memory (checkpoint resumed after corpus
changed — research references deleted docs), DISTRACTION (old critiques attended to as current). "We did
context engineering when we chose the supervisor's state projection; the checkpoint file is our long-term
memory" — then point at the code lines. (Deep dive: Part 6 below — Q19–Q23.)

**Q14. Single Project-A agent vs this team on the SAME brief: tokens, wall-clock, quality. Who wins what?**

**Answer:** (Quote YOUR comparison.) Expected shape: team wins QUALITY (acceptance criteria met: more sources,
critic-enforced citations, plan adherence) and loses COST (3–5× tokens: supervisor router calls + 4 workers +
revision rounds; longer wall-clock from sequential LLM calls). The honest version includes the crossover:
on SIMPLE briefs the single agent ties quality at 1/4 cost (team overhead unjustified — merge roles or stay
single); on COMPLEX briefs the team pulls ahead (role focus + redundancy pay off). If your team lost BOTH,
roles are too fine-sliced (merge writer+planner, re-run — record the fix). Decision rule for interviews:
"start single, split when traces show role-confusion or context bloat, and keep this comparison table as the
ongoing justification."

**Q15. What are the multi-agent-specific failure modes — the ones that DON'T exist for single agents?**

**Answer:** Four, each with YOUR specimen: (a) SUPERVISOR BOTTLENECK/misroute — one bad router prompt derails
all workers; symptom: wrong `next` with confident reason (your misroute log). (b) STATE CORRUPTION — one node
writes garbage, ALL downstream consume it (your empty-research run); single agents corrupt only their own
history. (c) REVISION THRASH — writer↔critic ping-pong consuming rounds without convergence (your max-
revisions trace); needs actionable-critique discipline or a circuit breaker. (d) RESPONSIBILITY DIFFUSION —
every node's output assumes "someone else will check it" (researcher returns thin findings assuming the critic
catches thinness; critic assumes the gate catches all) — symptom: defects passing EVERY machine stage to the
human. Mitigations: precondition checks in the supervisor prompt, critique-actionability standards, per-node
output contracts (researcher must return ≥N sourced findings or declare failure). Name one specimen each.

**Q16. What breaks at 10k briefs/day that works in your 3-brief eval?**

**Answer:** Same graph, new constraints: COST (your per-brief token count × 10k × model price = the budget
line — router calls on every step are now a line item to optimize, e.g. small-model router + big-model
workers); HUMAN GATE throughput (humans can't approve 10k briefs — gate sampling: approve all high-stakes,
spot-check low-stakes, auto-approve only below a trust threshold EARNED from bite-rate data); CHECKPOINT STORE
(SQLite file → Postgres-backed saver with TTL and thread GC); SUPERVISOR LATENCY (sequential router call per
step sets the floor — parallelize independent workers, e.g. two researchers concurrently, via multi-edge fan-
out); EVAL CONTINUITY (brief acceptance criteria become the Phase 3 eval harness running per-deploy, not
per-demo). The graph shape survives; every node gets metered, bounded, and the gate becomes a policy (what
fraction needs humans) instead of a CLI prompt. This is the agents-at-scale gap topic from the roadmap — name it.

**Q17. How do you eval a multi-agent team? (Grading one answer is easy; grading a collaboration is hard.)**

**Answer:** Three layers, all in YOUR report: (a) OUTCOME per brief — acceptance criteria from `evals/briefs.md`
(plan followed? sources ≥N? critic APPROVE? human decision?) — the table in your README. (b) PROCESS audits —
sample trajectories reviewed node-by-node: was each routing decision justified by its reason string? did the
critic bite on the planted bad draft? did resume preserve continuity? (c) COUNTERFACTUALS — the ablations:
gated vs auto-approve (gate value), team vs single-agent (team value), `--max-revisions 0` vs 2 (revision
value). Plus regression discipline: every misroute, thrash, and gate-catch becomes a permanent test (add the
brief + assert the fixed behavior). "We eval the deliverable, the trajectory, and the decisions — answer
correctness alone would miss a lucky run through a broken graph."

**Q18. Rubber-stamping check: prove your critic isn't just approving everything.**

**Answer:** The bite-rate test: feed the critic a DELIBERATELY bad draft (invented citation, off-brief section,
thin research — construct one) and confirm REVISE with SPECIFIC notes pointing at the defects. Your table's
critic-rounds column is the standing evidence: a column of zeros across briefs means the critic never bites —
either your writer is perfect (it isn't) or the critic prompt is sycophantic ("you are a helpful reviewer"
without adversarial instruction or a JSON verdict schema forcing APPROVE/REVISE). Fix pattern: critic prompt
with explicit defect checklist (citations resolve? claims supported? brief criteria met?), forced verdict JSON,
and few-shot REVISE example. A critic that can't fail a bad draft can't pass a good one — this is also the
interview answer to "how do you test an LLM judge" (Phase 3 preview).

---

## Part 6: Context Engineering & Memory Systems — "The buzzword, grounded in YOUR code"

*(Deep dive — do this part after writing the README's short comparison of memory strategies.)*

**Q19. What is context engineering, and how does it differ from prompt engineering? Show me where YOU did it.**

**Answer:** Prompt engineering tweaks the *wording* of a prompt. **Context engineering** decides *what
information goes into the model's window at each step* — and in a multi-agent team, every node gets a
DIFFERENT window, so the decision is load-bearing. Points in YOUR code where you did context engineering
(whether you called it that or not): (a) `supervisor.py`'s compact projection — goal + plan status +
research count + draft version + latest verdict, NOT full research text; (b) `workers.py` slices — writer
sees plan + research, critic sees draft + notes, researcher sees goal + plan; (c) goal re-anchoring (the task
restated per node so long runs don't drift — the Project A "model forgets the goal by step 8" lesson applied).
The 2025/26 hiring insight to state outright: for agents, success is less about clever phrasing and more about
engineering the right context — the model with the right 2k tokens beats the model with 20k noisy ones. Your
`--show-state` runs plus the bloat observation (full-research-into-supervisor) are the receipts.

**Q20. Name the memory types and point at each one in YOUR system.**

**Answer:** Three horizons, each with a concrete address in your repo: (a) **Short-term / in-context** — the
current node call's prompt + its immediate inputs (supervisor's projection this step, writer's plan+research
this draft). Dies when the call returns; bounded by the model's window. (b) **Working memory / scratchpad** —
`AgentState` DURING a run (`state.py`: plan, research[], draft versions, critiques[], revision_rounds). Lives
across nodes within one thread, mutated via reducers. (c) **Long-term memory** — `SqliteSaver` checkpoints +
`trajectory.jsonl` AFTER the run ends: resumable tomorrow, auditable next week. (If you later wire a vector
store or graph across threads, that joins this layer — name whether you did.) Pick by horizon: same call →
short-term; multi-step reasoning within a run → working; cross-session persistence/recall → long-term. The
interview move is pointing, not reciting: "short-term is the supervisor prompt I just showed you, working
memory is this state dict, long-term is this checkpoint file — here's a timestamp proving yesterday's research
loaded today."

**Q21. What are the common memory architectures — and which does YOUR team actually use?**

**Answer:** Four, as an honest inventory (used vs not): (a) **Buffering** — keep last N turns. That's what a
naive single agent does (Project A's ever-growing history), and what you OUTGREW: unbounded append is why
Project A bloats quadratically. (b) **Summarization-based compaction** — periodically compress history into a
summary (MemGPT-style). You DON'T do this yet — name where you'd add it: compress `research[]` into a brief
digest before the writer on long briefs, trading detail for window space; state the risk (summary drops the
one fact the critic needed). (c) **Semantic recall** — embed past content, retrieve relevant pieces on demand
(RAG over memory). Distinguish carefully: your researcher does retrieval over the CORPUS, not over memory —
corpus-RAG ≠ memory-RAG. True memory recall would be embedding past THREADS and retrieving them for a new
brief; you don't have it, and saying so is the senior answer. (d) **Self-editing memory** — the model writes
or updates its own persistent entries ("user prefers terse briefs"). Your checkpoints are written BY CODE
(reducers), not self-edited by the model — durable, but not self-editing. Summary line: "checkpoints give us
durable working memory; semantic recall and self-editing are explicitly future work, here's where each would
plug in."

**Q22. How does YOUR checkpointing map to "long-term memory," precisely — and where does the analogy break?**

**Answer:** The mapping: checkpointed state IS persistent memory in the functional sense — the team stops
tonight (kill, gate pause, crash) and resumes tomorrow with plan, research, and draft intact; your kill-switch
proof (pre-kill timestamps preserved, no repeated nodes) IS a memory-persistence demo, and the gate-pause
(process can die at the interrupt) only works because memory outlives the process. The bridge framing: working
memory (in-run `AgentState`) becomes long-term the moment `SqliteSaver` commits it. Where the analogy BREAKS
(say this unprompted): a checkpoint is a VERBATIM snapshot, not a memory system — no indexing, no retrieval by
relevance, no forgetting/decay policy, no consolidation across threads. Real long-term memory answers "what do
we know about X across all past briefs?"; your checkpoint answers "what was thread t1's exact state at node 7?"
Both valuable, different jobs. The one-line upgrade path: embed `research[]` per thread and add cross-thread
recall — that turns snapshots into searchable memory.

**Q23. What are the failure modes of memory systems — and which have YOU observed?**

**Answer:** Four, each with YOUR specimen and fix: (a) **Overflow** — too much in the window degrades reasoning
or truncates. Yours: full research text into the supervisor prompt (bloat run — cite the token count); fix was
the compact projection (counts/verdicts, not bodies). (b) **Stale memory** — persisted facts outlive their truth.
Yours (construct it if you haven't hit it): resume a checkpoint after the corpus changed — research cites
deleted docs; fix is revalidation (version-stamp research with corpus hash, drop or flag stale entries on
resume). (c) **Distraction** — irrelevant retrieved/persisted content gets attended to as current. Yours: old
critiques bleeding into a fresh revision round (thrash trace — writer addressing superseded notes); fix is
verdict-scoped notes (only the LATEST critique is instructions, older ones are audit). (d) **Cost** — long
context bills per token per call; your per-brief token table × revision rounds IS the cost-of-memory number.
The meta-rule: good context engineering is mostly SUBTRACTION — compress, filter, retrieve selectively. "We
fought all four: overflow with projection, stale with versioning, distraction with scoping, cost with the
comparison table" — then show one trace each.

---

## How to Use These Questions

1. **Narrate from trajectories** — every answer points at a node sequence: the misroute, the thrash, the gate catch, the resume.
2. **Quote the tables** — brief acceptance, gate ablation, team-vs-single cost. Numbers or it didn't happen.
3. **Demo the breaks** — kill-and-resume live, `--max-revisions 0`, planted-bad-draft critic test: 30-second narrations that land harder than definitions.
4. **Connect forward** — checkpoint store → memory systems; trajectory logs → Phase 3 eval inputs; researcher tools → Phase 3 guardrail surface.
