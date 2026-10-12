# Interview Questions — Multi-Agent Supervisor System (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual code and the numbers you measured** — brief tables, trajectories,
resume proofs, gate catches, cost comparisons. Quote your brief table; that separates "drew boxes and
arrows" from "ran a team."

**Evidence status:** every answer is tagged. **[BUILT]** = the code exists — fill in YOUR measured
numbers. **[PLANNED → Phase N]** = design answer written from the spec — verify it when you build
that phase, and correct the answer if reality disagrees. An answer you had to correct is a better
interview story than one that was right first try.

Built right now: `state.py` (AgentState + reducers + CriticVerdict), `workers.py` (planner /
researcher / writer / critic on `qwen3.5:4b`), `pa_tools.py` (Project A tools verbatim),
`evals/briefs.md` (B1/B2/B3). Still TODO: `supervisor.py`, `graph.py`, `cli.py`, `gate.py`,
`trace.py`, `__main__.py`.

---

## Part 1: Fundamentals — "Why a team instead of one agent?"

**Q1. What problem does a multi-agent system solve that a single ReAct agent doesn't? Give me a failure you SAW in Project A that a team fixes.** **[BUILT]**

**Answer:** A single ReAct agent (Project A) holds EVERY role in one context window and one prompt:
planning the approach, executing searches, drafting, and self-checking — with full history
regurgitated every step. Three concrete pains from YOUR Project A traces that motivate the split:
(a) WASTED STEPS — M1 ran an extra unprompted `web_search` before writing (5 steps for a
2-search-then-write task); one prompt can't hold "be thorough" and "be minimal" sharply at once.
(b) NO-VERIFY LOOP — the `error.txt` probe wrote the file at step 2 then re-read until
`--max-steps 10` killed it; nothing in the loop knew "writing" and "checking" are different jobs.
(c) NO REDUNDANCY — small-number E2 answered `96` from weights with zero calls; no second role
existed to challenge the shortcut. The team (`workers.py`: planner / researcher / writer / critic)
gives each role a narrow prompt, narrow state slice, and narrow success criterion. Quality goes up
(depth per role + adversarial review), cost goes up too (more LLM calls — your Q14 table states
both). "Split when the single-agent trace shows wasted steps or uncheckable shortcuts" is the
honest trigger — not "multi-agent is better" in the abstract.

**Q2. Walk me through one brief end to end, naming every file that touches it.** **[BUILT Phase-1 slice / PLANNED → Phase 2 for routing+]**

**Answer:** Take B1 ("How Claude Code works, under 300 words"). What runs TODAY, from a REPL on
canned state: (1) `planner({"goal": ...})` in `workers.py` → `ollama.chat(model="qwen3.5:4b")` →
returns `{"plan": [steps]}`; (2) `researcher({"goal", "plan"})` → mini-ReAct loop (max
`MAX_RESEARCH_STEPS = 5`) over `pa_tools.TOOLS` via `dispatch()` → returns `{"research":
[findings]}`; (3) `writer({"plan", "research"})` → returns `{"draft", "draft_version": n+1}`;
(4) `critic({"draft"})` → `format="json"` → returns `{"critiques": [{verdict, notes}],
"revision_rounds": n+1}`. Shapes enforced by `state.py`'s `AgentState`.
What Phase 2+ adds around the SAME four functions: `supervisor.py` routes between them via
conditional edges in `graph.py` (emitting `{"next", "reason"}`), `cli.py` threads
`{"configurable": {"thread_id": ...}}` through every invoke, `gate.py` interrupts after
critic-APPROVE, finalize writes `report.md`, `trace.py` appends the trajectory JSONL. The workers
don't change — orchestration wraps them. (Note the real limitation in step 2: `findings` collects
only the researcher's FINAL summary thought — tool observations stay in its local messages list.
Evidence survives only if the model restates it. That's Q15c.)

**Q3. Supervisor vs swarm — what's the actual structural difference, and why did you start with supervisor?** **[PLANNED → Phase 2]**

**Answer:** SUPERVISOR (planned `supervisor.py` + conditional edges in `graph.py`): ONE central
router sees the state and decides `next` after every step; workers never call each other — all
traffic hub-and-spoke through the supervisor. SWARM: peer-to-peer handoffs — the researcher decides
"hand to writer now" without asking a boss; no single node has global view. Tradeoff: supervisor is
EASY TO REASON ABOUT (every routing decision is one logged `reason` string in one place — your
misroute debugging in Q4 works because of this), easy to GATE (one choke point before finalize),
but a BOTTLENECK and single point of failure (supervisor prompt bug derails everything; every step
pays a router LLM call). Swarm is resilient and parallel-friendly but debugging is distributed —
"why did the writer run twice?" has no single log line. For learning AND production control,
centralized routing with a logged reason is the right start; decentralize only with evidence the
supervisor is the bottleneck (your Q14 cost table would show router-call share).

---

## Part 2: Orchestration — "Routing, roles, and revision bounds"

**Q4. How does the supervisor decide what's next? What exactly does it read and emit?** **[PLANNED → Phase 2]**

**Answer:** Planned `supervisor.py` is an LLM call over COMPACT state (goal + plan status +
research count + draft version + latest critique verdict + revision_rounds — NOT full research
text; that's context economics, and your Project A bloat observation is the receipt for why), with
a system prompt listing the legal transitions (planner→researcher→writer→critic→{writer|gate|END}).
Output is forced JSON `{"next": ..., "reason": "..."}` via `format="json"` — the SAME trick already
proven in your built `critic()`, including its fallback discipline (unparseable → safe default,
never a crash). The conditional edge in `graph.py` dispatches on `next`. Model: `qwen3.5:4b` first
(already pulled); the tripwire is documented — misroutes surviving two prompt iterations mean
upgrading the supervisor call to `qwen3:8b`, recorded as a finding like Project A's model-swap
experiment. Known confusion pair to watch for: critic-APPROVE-with-nits vs REVISE — does the
supervisor send nits back to the writer (wasting a revision round) or to the gate? Record which way
yours errs and the prompt line you changed.

**Q5. Why four roles — planner, researcher, writer, critic? What breaks if you merge or split further?** **[BUILT — roles exist; cost half PLANNED]**

**Answer:** Each role isolates a CONFLICTING objective: planner optimizes COMPLETENESS of approach,
researcher optimizes RECALL of evidence, writer optimizes FLUENCY of draft, critic optimizes
CORRECTNESS adversarially. Read it off YOUR briefs: B2's three-category split is the planner's job
(a writer asked to "research peptides" without a plan under-covers a category — that's a REVISE
condition in B2's step 4); B2's "no dosage instructions" rule is unenforceable without a critic
reading adversarially. Merging writer+critic collapses the adversarial tension (self-review is
rubber-stamping — your Q18 bite test degrades); merging planner+writer recreates Project A's
role-confusion. Splitting further (fact-checker + stylist + sourcer…) multiplies LLM calls per
brief with diminishing returns — your Q14 cost table shows the per-role token share, so you can
point at which split would be pure overhead. The four-role split is minimal-viable-separation:
plan / gather / produce / verify. If your data shows one role contributing nothing (e.g. planner on
trivial briefs), say so — "planner is skippable for single-source briefs" is a finding, not a failure.

**Q6. The writer↔critic loop could spin forever. What EXACTLY bounds it, and what happens at the bound?** **[BUILT mechanics / PLANNED → Phase 2 wiring]**

**Answer:** `revision_rounds` in state, checked against `--max-revisions 2`. Read YOUR `critic()`
closely: `rounds = state.get("revision_rounds", 0) + 1` runs on EVERY critic call — APPROVE included.
So the bound counts critic PASSES, not just REVISE loops; with max-revisions 2, two critic verdicts
total, then forced END with a failure note (your planned `--max-revisions 0` break-run proves the
mechanism: forced END, no infinite loop). This is Project A's `--max-steps` guard lifted to the team
level: unbounded agency converts to bounded spend + debuggable trace. Production reading: the bound
is a COST control (each round = writer call + critic call + full-state context) and the thrash case
(writer ignores critique, critic repeats REVISE) is the most instructive trace you will own: read it
to learn whether the bug is writer-obedience or critique-vagueness ("be better" critiques never
converge — critiques must be ACTIONABLE, cite the offending passage).

---

## Part 3: State & Checkpointing — "The collaboration contract"

**Q7. What is shared state mechanically, and why are reducers the real design decision?** **[BUILT]**

**Answer:** `state.py` defines `AgentState` (a `total=False` TypedDict — all keys optional, so every
node reads with `.get()`): `goal, plan, research, draft, draft_version, critiques, next,
revision_rounds, human_decision` — the ONLY channel workers share; workers never message each other
directly. REDUCERS define the write semantics per field and ARE the collaboration contract:
`research`/`critiques` use `Annotated[list, operator.add]` (parallel-safe accumulation, nothing
lost), `draft` OVERWRITES with a manual `draft_version` bump (single current truth + history via
versions — no silent clobbering), `revision_rounds` overwrites with `+1` (monotonic bound).
`CriticVerdict = Literal["APPROVE", "REVISE"]` pins the critic's vocabulary at the type level.
Wrong reducer = real bug class: APPEND on `draft` leaves workers reading stale versions; OVERWRITE
on `research` loses findings across resume. Note the honest gap: `plan` is a BARE list with no
reducer — fine while the planner is the sole writer, but a second plan-writer would race. In
interviews: "reducers are the concurrency + persistence contract; the TypedDict is just the shape."
LangGraph enforces them at every node commit — that's what makes resume SAFE (replayed state merges
identically, not approximately).

**Q8. Checkpointing: what is persisted, when, and prove resume works — don't just claim it.** **[PLANNED → Phase 3]**

**Answer:** Planned: `graph.py` wires `SqliteSaver`; LangGraph persists the FULL state snapshot
after EVERY node completion, keyed by the `--thread` ID that `cli.py` (TODO) threads through every
invoke. Proof protocol (the kill-switch test): `run --thread t1` on a slow-researcher brief (B2 —
three categories means several `web_search` calls, a wide kill window) → Ctrl+C mid-research, note
the wall time → `resume --thread t1` (SAME id — a new id silently starts a fresh thread; that's the
#1 false alarm) → completes. The PROOF is in the trajectory: post-resume log shows state intact
(plan present, `research[]` preserved with pre-kill timestamps), NO repeated completed nodes (no
second planner entry, no re-search of completed queries), continuation from the exact next node.
Quote the timestamps. What checkpointing buys: crash recovery (long runs survive), human-gate
pausing (the process can DIE at the interrupt and resume tomorrow — the gate is just a named
pause), replay/debugging. Without it every mid-run failure restarts from zero — at team-scale cost
(5+ LLM calls per brief) that's not an inconvenience, it's a budget fire.

**Q9. Your corrupt-state break-run: you emptied `research` mid-run. Which node failed first, and did the supervisor recover or derail?** **[PLANNED → Phase 2/3]**

**Answer:** (Run it, quote YOUR run.) Predicted shape from YOUR code: the writer fails first — it
drafts from `plan + []` into a thin, citation-free draft (its prompt says "use only the research
provided," and there is none). The interesting part is what the critic can even see: YOUR `critic()`
receives ONLY `f"Draft to review:\n{draft}"` — no `research`, no plan. So it can REVISE on "uncited
claims" (one of its four listed triggers) but CANNOT distinguish "thin research" from "writer ignored
rich research." Supervisor behavior is the actual test: a good router sees the REVISE notes +
`research=[]` and routes BACK to researcher (recovery — state-conditioned routing works); a brittle
one pushes the empty draft toward the gate (derail — routing follows stage order, not state
content). Either result is a finding: recovery proves state-conditioned routing; derail proves your
supervisor prompt needs a "validate preconditions before advancing" rule (add it, re-run, record the
fix). This experiment is the state-management equivalent of Project A's error-as-observation test —
the system meeting violated expectations and showing its character.

---

## Part 4: Human-in-the-Loop — "The gate before the irreversible step"

**Q10. What is human-in-the-loop here, precisely — and why THIS position in the graph?** **[PLANNED → Phase 4]**

**Answer:** Planned `gate.py` calls LangGraph `interrupt()` AFTER critic-APPROVE and BEFORE
finalize: the run pauses (checkpointed — safe to walk away), CLI presents draft + latest critique,
human chooses approve → finalize as-is / edit:\<text> → finalize edited version /
reject:\<reason> → back to writer (consuming a revision round). Three mechanics that bite (from the
linked LangGraph guide — read before coding): `interrupt()` raises without the Phase-3
checkpointer; the node function RE-RUNS from the top on resume, so everything before `interrupt()`
must be side-effect-free; the human's decision arrives as the `interrupt()` RETURN VALUE — you must
write it into `state["human_decision"]` yourself. Position rationale: the gate sits where MISTAKE
COST is highest — finalize publishes `report.md`, the deliverable the world sees; everything
upstream is cheap revision. Gating every node would strangle throughput (human latency per step);
gating nothing ships critic-missed defects (your ablation Q11 has the receipt). Rule: gate
IRREVERSIBLE or EXTERNAL actions (publish, send, spend, deploy) — internal drafts stay
machine-speed. Your three-path verification (approve a good draft, edit a mediocre one, reject a
bad one and watch the writer address the reason) proves all branches, not just the happy path.

**Q11. Gate ablation: same brief, gated vs `--auto-approve`. What did the human catch?** **[PLANNED → Phase 5]**

**Answer:** (Quote YOUR defect, verbatim.) Expected shape — read it off YOUR briefs: B2 is the
trap brief. The critic checks "dosage advice present" per B2's step 4, but a soft dosage hint
("many users start low…") may pass a 4b critic and get REJECTed by a human. That verbatim quote is
the one that justifies the gate's existence: "auto-approve shipped [X]; the gate caught it because
[Y]." Also record the COST: gate adds human-latency (minutes–hours) to every brief — so the verdict
includes WHEN you'd remove it (low-stakes internal drafts, after critic bite-rate earns trust over N
briefs) and when never (external publish, money, safety-relevant content like B2). "Gated by
default, auto-approve as a measured ablation, never as the default" is the production posture.

**Q12. Approve / edit / reject — what does each do to state, exactly?** **[PLANNED → Phase 4]**

**Answer:** APPROVE: sets `human_decision="approve"`, routes to finalize untouched. EDIT: human text
becomes the new `draft` with a `draft_version` bump — the human is just another writer node with
full authority, and the edit is logged in the trajectory like any state diff. REJECT with reason:
appends the reason to `critiques[]` (indistinguishable from a critic REVISE downstream —
deliberate design, so the writer handles human feedback through the same path) and increments
`revision_rounds`, routes to writer. Elegance worth stating: the gate needs no special downstream
plumbing because rejection REUSES the revision machinery — three human choices, one existing loop.
Note the fit with YOUR built code: `critiques` is already APPEND-reduced and `revision_rounds`
already increments per cycle, so the reject path slots into existing reducers with zero new
mechanics. Your rejected-then-fixed trace (writer visibly addressing the human reason) is the demo.

---

## Part 5: Memory, Cost & Production — "Context engineering, bills, and breakage"

**Q13. How does this project's state/checkpointing map to "memory systems" and "context engineering"? (2026 buzzword question — nail it.)** **[BUILT slices / PLANNED checkpointing]**

**Answer:** Three mappings, precise: (a) CHECKPOINTED STATE = long-term/working memory persisted —
[PLANNED → Phase 3] the team resumes tomorrow with yesterday's research intact; your kill-switch
proof WILL BE a memory-persistence demo. (b) WORKER SLICES = context engineering ALREADY BUILT —
point at the code: planner sees goal only, researcher sees goal+plan, writer sees plan+research,
critic sees draft ONLY. Each `state.get(...)` line in `workers.py` is a context-engineering
decision (right information, no drowning), as opposed to prompt engineering (wording). The
supervisor's compact projection (counts/verdicts, not bodies) is [PLANNED → Phase 2] on the same
principle. (c) FULL HISTORY NOWHERE — no node holds the entire trajectory; the trajectory log is
write-only audit, not context. Failure modes transfer directly: OVERFLOW (full research into the
supervisor prompt — Project A's ever-growing history is the specimen), STALE memory (checkpoint
resumed after corpus changed), DISTRACTION (old critiques attended to as current — your APPEND
`critiques[]` keeps every round visible, so scoping "only the LATEST critique is instructions" is a
real design decision to state). "We did context engineering when we chose each worker's `state.get`
slice; the checkpoint file will be our long-term memory" — then point at the code lines. (Deep
dive: Part 6 below — Q19–Q23.)

**Q14. Single Project-A agent vs this team on the SAME brief: tokens, wall-clock, quality. Who wins what?** **[PLANNED → Phase 5, experiment 4]**

**Answer:** (Run it, quote YOUR comparison.) Protocol: one brief (B1 — simplest, fairest to the
single agent) on the team AND as a single Project-A agent with all tools. Prediction from YOUR
Project A numbers: team wins QUALITY (acceptance criteria met: ≥5 sources, critic-enforced
citations, plan adherence — against M1's precedent of unminimal but correct output) and loses COST
(3–5× tokens: supervisor router calls + 4 workers + revision rounds; longer wall-clock from
sequential `qwen3.5:4b` calls at ~10–15 tok/s). The honest version includes the crossover: on
SIMPLE briefs the single agent ties quality at a fraction of the cost (team overhead unjustified —
merge roles or stay single); on COMPLEX briefs (B2's three categories + safety constraints) the team
pulls ahead (role focus + redundancy pay off). If your team lost BOTH, roles are too fine-sliced
(merge writer+planner, re-run — record the fix). Decision rule for interviews: "start single, split
when traces show wasted steps or uncheckable shortcuts, and keep this comparison table as the
ongoing justification."

**Q15. What are the multi-agent-specific failure modes — the ones that DON'T exist for single agents?** **[BUILT code facts + PLANNED specimens]**

**Answer:** Four, each anchored in YOUR code: (a) SUPERVISOR BOTTLENECK/misroute — one bad router
prompt derails all workers [PLANNED → Phase 2 specimen: wrong `next` with confident reason, your
misroute log]. (b) STATE CORRUPTION — one node writes garbage, ALL downstream consume it [PLANNED
break-run Q9; the shape is predictable from your code because the critic sees draft only and can't
see the empty `research` behind it]. (c) REVISION THRASH — writer↔critic ping-pong without
convergence; YOUR `critic()` feeds it twice: it increments `revision_rounds` even on APPROVE (bound
counts passes, not just disputes), and its four REVISE triggers are all draft-local — a writer that
can't satisfy "uncited claims" with thin research loops forever. Mitigation: actionable-critique
discipline + the max-revisions circuit breaker. (d) EVIDENCE COMPRESSION — researcher-shaped, and
already visible in BUILT code: `findings` keeps only the final summary thought while tool
observations (URLs, snippets, counts) die in the local messages list. The writer cites from a
summary-of-evidence, not evidence — B1's "≥5 distinct sources" criterion is exactly what this
failure mode threatens. Mitigations: findings schema (URL + quote per finding), or pass
observations through. Name one specimen each; (c) and (d) are quotable from code TODAY.

**Q16. What breaks at 10k briefs/day that works in your 3-brief eval?** **[PLANNED — design answer]**

**Answer:** Same graph, new constraints: COST (your per-brief token count × 10k × model price = the
budget line — router calls on every step are now a line item to optimize, e.g. small-model router +
big-model workers, the asymmetric-tier habit from MODELS.md); HUMAN GATE throughput (humans can't
approve 10k briefs — gate sampling: approve all high-stakes like B2, spot-check low-stakes,
auto-approve only below a trust threshold EARNED from bite-rate data); CHECKPOINT STORE (SQLite file
→ Postgres-backed saver with TTL and thread GC); SUPERVISOR LATENCY (sequential router call per step
sets the floor — parallelize independent workers, e.g. two researchers concurrently, via multi-edge
fan-out; your APPEND `research` reducer is already parallel-safe, which is exactly why that reducer
choice matters at scale); EVAL CONTINUITY (brief acceptance criteria become the Phase 3 eval harness
running per-deploy, not per-demo). The graph shape survives; every node gets metered, bounded, and
the gate becomes a policy (what fraction needs humans) instead of a CLI prompt. This is the
agents-at-scale gap topic from the roadmap — name it.

**Q17. How do you eval a multi-agent team? (Grading one answer is easy; grading a collaboration is hard.)** **[BUILT layer (a) / PLANNED (b)(c)]**

**Answer:** Three layers: (a) OUTCOME per brief — [BUILT] acceptance criteria from YOUR
`evals/briefs.md` (B1: ≤300 words, ≥5 sources, APPROVE, ≤2 rounds; B2: 3 categories + disclaimer +
no-dosage; B3: table + recommendation) — the table in your README. (b) PROCESS audits —
[PLANNED → Phase 5] sample trajectories reviewed node-by-node: was each routing decision justified
by its reason string? did the critic bite on the planted bad draft (Q18)? did resume preserve
continuity (Q8)? (c) COUNTERFACTUALS — the ablations: gated vs auto-approve (gate value, Q11),
team vs single-agent (team value, Q14), `--max-revisions 0` vs 2 (revision value, Q6). Plus
regression discipline: every misroute, thrash, and gate-catch becomes a permanent test (add the
brief + assert the fixed behavior). "We eval the deliverable, the trajectory, and the decisions —
answer correctness alone would miss a lucky run through a broken graph."

**Q18. Rubber-stamping check: prove your critic isn't just approving everything.** **[BUILT — run it now]**

**Answer:** The bite-rate test, runnable TODAY against your built `critic()` — no graph needed:
`critic({"draft": <poisoned>})` from a REPL. Construct the poisoned draft from B1's REVISE triggers
(YOUR `CRITIC_SYSTEM` lists four: invented citations, off-brief sections, missing sources, uncited
claims — use at least two). Record verbatim: verdict + notes. `APPROVE` = stop, sharpen the prompt,
re-run — do not proceed to Phase 2. `REVISE` with specifics = pass, and save it as your first
trajectory specimen. Your README's worker-REPL table is the standing evidence going forward: a
critic-rounds column of zeros across briefs means the critic never bites — either your writer is
perfect (it isn't) or the prompt is sycophantic. Note the built safety net: unparseable output and
invalid verdict strings both fall back to REVISE (never a crash, never a silent APPROVE) — the
critic fails CLOSED. A critic that can't fail a bad draft can't pass a good one — this is also the
interview answer to "how do you test an LLM judge" (Phase 3 preview).

| Poisoned draft defect (B1-based) | Verdict | Notes (verbatim — fill in) |
| -------------------------------- | ------- | -------------------------- |
| invented citation ("per Smith et al. 2024…") | | |
| off-brief section (pricing tiers — B1 never asked) | | |

---

## Part 6: Context Engineering & Memory Systems — "The buzzword, grounded in YOUR code"

*(Deep dive — do this part after writing the README's short comparison of memory strategies.)*

**Q19. What is context engineering, and how does it differ from prompt engineering? Show me where YOU did it.** **[BUILT]**

**Answer:** Prompt engineering tweaks the *wording* of a prompt. **Context engineering** decides
*what information goes into the model's window at each step* — and in a multi-agent team, every
node gets a DIFFERENT window, so the decision is load-bearing. Points in YOUR code where you did
context engineering (quote the `state.get` lines): planner reads goal ONLY (`state.get("goal")`);
researcher reads goal+plan; writer reads plan+research; critic reads draft ONLY. The SYSTEM prompts
are short because the SLICES do the work — `PLANNER_SYSTEM` is two sentences; it works (or fails)
because of what it ISN'T shown. The 2025/26 hiring insight to state outright: for agents, success is
less about clever phrasing and more about engineering the right context — the model with the right
2k tokens beats the model with 20k noisy ones. The supervisor's compact projection [PLANNED →
Phase 2] extends the same principle to routing. Receipts you already own: each worker's input slice
in `workers.py`, plus Project A's bloat observation (full history regurgitated every step) as the
before-picture.

**Q20. Name the memory types and point at each one in YOUR system.** **[BUILT (a)(b) / PLANNED (c)]**

**Answer:** Three horizons, each with a concrete address: (a) **Short-term / in-context** [BUILT] —
the current node call's prompt + immediate inputs (e.g. the researcher's `messages` list mid-loop,
the writer's plan+research this draft). Dies when the call returns; bounded by the model's window.
(b) **Working memory / scratchpad** [BUILT] — `AgentState` DURING a run (`state.py`: plan,
`research[]`, draft versions, `critiques[]`, `revision_rounds`), mutated via reducers. Lives across
nodes within one thread. (c) **Long-term memory** [PLANNED → Phase 3] — `SqliteSaver` checkpoints
+ `trajectory.jsonl` AFTER the run ends: resumable tomorrow, auditable next week. (If you later
wire a vector store or graph across threads, that joins this layer — name whether you did.) Pick by
horizon: same call → short-term; multi-step reasoning within a run → working; cross-session
persistence/recall → long-term. The interview move is pointing, not reciting: "short-term is this
`messages` list, working memory is this state dict, long-term will be this checkpoint file — and
here's the kill-test timestamp proving yesterday's research loaded today."

**Q21. What are the common memory architectures — and which does YOUR team actually use?** **[BUILT + honest gaps]**

**Answer:** Four, as an honest inventory (used vs not): (a) **Buffering** — keep last N turns.
[BUILT, scoped] your researcher's local `messages` list IS a buffer — but bounded by
`MAX_RESEARCH_STEPS = 5` and discarded after the call; Project A's ever-growing history is what you
OUTGREW, and the bound is the lesson applied. (b) **Summarization-based compaction** — compress
history into a digest. [BUILT, accidental] your researcher already does a crude version: a whole
tool trajectory compressed into one summary thought in `findings` (Q15d) — lossy, unasked-for, and
exactly why B1's source-count criterion is at risk. Name where you'd do it DELIBERATELY: compress
`research[]` into a sourced digest before the writer on long briefs. (c) **Semantic recall** — embed
past content, retrieve on demand. [NOT BUILT] your researcher retrieves over the CORPUS, not over
memory — corpus-RAG ≠ memory-RAG. True memory recall would be embedding past THREADS and retrieving
them for a new brief; you don't have it, and saying so is the senior answer. (d) **Self-editing
memory** — the model writes its own persistent entries. [NOT BUILT] your checkpoints are written BY
CODE (reducers), not self-edited by the model — durable, but not self-editing. Summary line:
"reducers give us durable working memory plus accidental compaction; semantic recall and
self-editing are explicitly future work, here's where each would plug in."

**Q22. How does YOUR checkpointing map to "long-term memory," precisely — and where does the analogy break?** **[PLANNED → Phase 3]**

**Answer:** The mapping: checkpointed state IS persistent memory in the functional sense — the team
stops tonight (kill, gate pause, crash) and resumes tomorrow with plan, research, and draft intact;
your kill-switch proof (pre-kill timestamps preserved, no repeated nodes) WILL BE a
memory-persistence demo, and the gate-pause (process can die at the interrupt) only works because
memory outlives the process. The bridge framing: working memory (in-run `AgentState`) becomes
long-term the moment `SqliteSaver` commits it. Where the analogy BREAKS (say this unprompted): a
checkpoint is a VERBATIM snapshot, not a memory system — no indexing, no retrieval by relevance, no
forgetting/decay policy, no consolidation across threads. Real long-term memory answers "what do we
know about X across all past briefs?"; your checkpoint answers "what was thread t1's exact state at
node 7?" Both valuable, different jobs. The one-line upgrade path: embed `research[]` per thread
and add cross-thread recall — that turns snapshots into searchable memory.

**Q23. What are the failure modes of memory systems — and which have YOU observed?** **[BUILT (a) / PLANNED rest]**

**Answer:** Four, each with specimen status: (a) **Overflow** [BUILTodet observer, PLANNED specimen]
— too much in the window degrades reasoning. Your specimen exists one level down: Project A's full
history regurgitated every step; your fix is already in code (worker slices + researcher's 5-step
bound). The supervisor-projection overflow test (full research into the router prompt — cite the
token count) lands in Phase 2. (b) **Stale memory** [PLANNED] — persisted facts outlive their truth:
resume a checkpoint after the corpus changed, research cites deleted docs; fix is revalidation
(version-stamp research with corpus hash, drop or flag stale entries on resume). (c) **Distraction**
[BUILT SHAPE] — irrelevant persisted content attended to as current. Your APPEND `critiques[]`
keeps EVERY round visible to all future nodes — writer addressing superseded notes in a thrash trace
is the predicted specimen; fix is verdict-scoped notes (only the LATEST critique is instructions,
older ones are audit). (d) **Cost** [PLANNED numbers] — long context bills per token per call; your
per-brief token table × revision rounds IS the cost-of-memory number (Q14). The meta-rule: good
context engineering is mostly SUBTRACTION — compress, filter, retrieve selectively. Target closing
line: "we fought overflow with slices, distraction with scoping, stale with versioning, cost with
the comparison table" — with one trace each.

---

## How to Use These Questions

1. **Fill in phase order** — Q18 + worker-REPL table NOW (all runnable against built code); Q2-trajectory,
   Q4-misroutes, Q6-thrash when Phase 2 runs; Q8-timestamps, Q9-verdict when Phase 3 runs; Q10–Q12
   transcripts when Phase 4 runs; Q11-defect, Q14-costs, Q17-layers when Phase 5 runs.
2. **Narrate from trajectories** — every PLANNED answer points at a future node sequence: the misroute,
   the thrash, the gate catch, the resume. When it happens, paste the verbatim strings HERE.
3. **Quote the tables** — brief acceptance (built), gate ablation, team-vs-single cost. Numbers or it didn't happen.
4. **Demo the breaks** — kill-and-resume live, `--max-revisions 0`, planted-bad-draft critic test: 30-second narrations that land harder than definitions.
5. **Connect forward** — checkpoint store → memory systems; trajectory logs → Phase 3 eval inputs; researcher tools → Phase 3 guardrail surface.
