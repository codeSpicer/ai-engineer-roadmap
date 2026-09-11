# Interview Questions — Capstone & Agents at Scale (with Answers)

These questions simulate a real technical interview for an AI engineering role — the system-design
round, not the trivia round. Each answer must be grounded in **YOUR capstone build (§1) and YOUR
§2 design write-ups**, with numbers from your phase projects cited as evidence. Quote your reuse
table, your cost rows, and your tradeoff docs; that separates "designed a system" from "listed
buzzwords."

Do this Q&A LAST — after the capstone is live and the §2 write-ups are written. Every answer below
names the artifact it points at.

---

## Part 1: Capstone — "One system, every phase"

**Q1. Why is the capstone more valuable than four disconnected phase projects?**

**Answer:** One polished system that **integrates RAG + agents + evals + guards (+ a tuned component)**
demonstrates end-to-end engineering: scoping, composition (the layers interact — composition creates
failure modes no phase had alone, and YOUR §1 Phase-2 log holds the one your unit-guarded parts missed),
measurement with teeth (gates that block, canaries that roll back — both PROVEN by red runs, not asserted),
and operations (live URL, baselines, cost math). Four disconnected projects demonstrate coursework: each
correct in isolation, never composed, never pressured by real traffic. Recruiters screening your resume see
ONE coherent product they understand in a glance (problem → architecture → metrics → demo) versus four
half-projects they must assemble mentally. Depth + integration beats breadth — and the integration is where
senior judgment lives (which phase's guarantees survive composition, which need re-verification — YOUR
write-up names both).

**Q2. What pieces did YOUR capstone reuse from earlier phases? Walk the reuse table.**

**Answer:** (Walk YOUR §1 table, layer by layer — no hand-waving, file pointers per row.) Knowledge: Phase 2
RAG-A/B retriever (hybrid + rerank; graph if YOUR task is multi-hop; §7 vision-parse if YOUR corpus is
scanned — name which). Reasoning/action: Agents-A ReAct loop or Agents-B supervisor (which you chose and WHY —
single-loop sufficiency vs role-confusion evidence from YOUR traces). Quality: Evals-A golden-set METHOD
extended to the CAPSTONE TASK (not the RAG subtask — new golden set, new `must_hit` semantics for task success)
+ Evals-B workflow retargeted at capstone metrics (which thresholds carried over, which are new). Safety:
Guards-A validators + Guards-B rails on every I/O boundary (which rails, which adversarial sets re-run against
the ASSEMBLED system). Model: YOUR SFT/DPO checkpoint with win-rate + refusal receipts — or the written
"tuning didn't earn it" verdict with headroom numbers (both defensible; point at the verdict either way).
Operations: LLMOps-A traces/baselines + LLMOps-B serving/canary (same files imported — baselines.yml,
thresholds.yml — never forked). The table proves range; the per-row WHY proves judgment.

**Q3. How did you pick the capstone problem and its metrics? Why do those metrics suffice?**

**Answer:** Problem filter (YOUR §1 Phase-0 doc): REAL user (named — not "users"), NEEDS retrieval (headroom
proof: base model fails without context — quoted), NEEDS multi-step work (single-shot sufficiency would make
the agent theater — YOUR pilot traces show the steps), HAS safety stakes (guards/audits meaningful — YOUR
adversarial set exists because the stakes do). Metrics, each with a target AND an owner: faithfulness/task-success
(quality — Evals-A method), $/request + p99 (operations — LLMOps-A baselines), win-rate if tuned (FT-B method),
block-rate on adversarial sets (safety — Guards tables). Sufficiency argument: quality WITHOUT cost is a demo
(shippable? unknown); cost WITHOUT quality is a budget line (useful? unknown); safety WITHOUT either is theater
(blocking what, at what price?). YOUR metrics page holds all four families on one screen — "suffice" means no
stakeholder question (does it work? what does it cost? is it safe? will it stay working?) lacks a number. Targets
set from YOUR baselines, not aspirations (faithfulness ≥ measured-phase-best − noise, cost ≤ measured + margin).

**Q4. What would you put in the capstone's README / portfolio page — and what does YOURS actually show?**

**Answer:** The seven elements, each verified present in YOUR write-up: (1) problem + why it matters (one
paragraph, user named); (2) architecture diagram (retrieval → agent → guards → generation → eval gate → serve —
YOUR diagram, with the §2 scale annotations if designed); (3) phase-reuse table (Q2 — shows range at a glance);
(4) metrics (eval scores + cost/latency + win-rate + block-rate — YOUR numbers, with noise/margin honesty);
(5) demo (LIVE link preferred — "keep it live, a URL beats screenshots" per §1 DOD — plus the 5-minute narrated
flow: happy path, one blocked attack, one trace read, one metric explained); (6) honest limitations + "what I'd
improve" (YOUR two named items — limitations with owners signal seniority louder than features); (7) repo hygiene
(repro instructions, pinned versions, artifact hashes — a stranger can run it). Portfolio order per §1: capstone
FIRST, one frontier artifact second (range), phase projects as depth links. Rehearse the 5-minute demo until the
transitions are boring — demo fluency IS the interview.

**Q5. How does the capstone tie back to the agentic system-design write-ups (§2)?**

**Answer:** The capstone IS a small agentic system under load — it FORCED the §2 tradeoffs concretely instead of
theoretically: YOUR orchestration choice (supervisor vs swarm) justified by YOUR Phase-2 cost table, not doctrine;
MCP-vs-thin-client decided PER TOOL with YOUR hop-latency row; HITL placed at YOUR highest-mistake-cost boundary
(the gate before publish/send/spend — YOUR gate-catch quoted); cost/latency math from YOUR $/request rows
projected to the write-up's 10k req/day. Direction of influence runs BOTH ways: §2 thinking shaped capstone
choices (idempotency keys on write tools from day one because the write-up demanded them), and capstone
measurements CORRECTED §2 assumptions (quote one: "write-up assumed X ms/step; capstone traces showed Y because
[reason] — doc updated"). Building the capstone last, after the system-design study, makes both stronger — and
saying which assumption broke, with numbers, is the single best system-design interview story in this file.

---

## Part 2: Agents at Scale — "The 10k req/day design round"

**Q6. How do you make an agent system robust at scale? Walk YOUR 10k req/day write-up.**

**Answer:** Treat the agent like a DISTRIBUTED SYSTEM, not a script — seven mechanisms, each with YOUR
write-up's concrete choice: (a) CONCURRENCY WITH LIMITS (bounded parallel tool calls / sub-agents — YOUR
bound number + the overload failure it prevents, quoted from a Phase-2 thrash trace if you have one);
(b) IDEMPOTENCY (keys on every write/API tool — retrying `charge` / `send` / `write_file` never double-applies;
YOUR key scheme: request-id + tool-name + args-hash — state it); (c) RETRIES WITH BACKOFF (transient: rate
limits, timeouts — YOUR policy: N attempts, exponential base, jitter, which errors retry vs fail-fast);
(d) TIMEOUTS (per tool, per step, per run — YOUR values calibrated against LLMOps-A p99 rows; no step runs
forever — fail fast with the partial trace preserved); (e) PERSISTENT STATE (checkpoints/DB — YOUR Agents-B
kill-switch proof cited: resume with zero repeated nodes, timestamps quoted); (f) FAILURE ISOLATION (one
sub-agent/tool failing degrades THAT branch — supervisor reroutes or abstains that part; YOUR corrupt-state
run: recovered vs derailed, and the precondition rule it produced); (g) OBSERVABILITY (every step traced —
YOUR LLMOps-A span taxonomy + the first-moving panel from the sabotage replay as the incident playbook).
"Robust" = each mechanism named, valued, and evidenced — buzzword bingo is listing them; engineering is the
numbers attached.

**Q7. MCP vs thin API wrapper — when does the protocol earn its hop? Decide for YOUR tools.**

**Answer:** Rule: a THIN client/SDK suffices for one agent + one service, same language, tight coupling (YOUR
example: `calculator` in-process — zero reason to pay a hop). MCP EARNS its overhead (+YOUR measured ms/call —
quote it) when tools are SHARED across agents/clients/processes/languages, need INDEPENDENT lifecycles
(version/deploy the tool without redeploying agents), or cross TRUST boundaries (untrusted tool code isolated
by process — YOUR sandbox review's containment argument). YOUR §2 write-up-2 decides PER TOOL in your stack
(tool × verdict × reason rows — e.g. file-tools: MCP (shared by RAG indexer + agent + capstone); calculator:
thin; web-search: MCP (versioned, rate-limited service); domain API: thin until second consumer appears).
Plus the DYNAMIC-DISCOVERY point (agent learns tools at runtime vs hardcoded imports — matters when the tool
set changes without agent redeploys; YOUR config-only behavior-change demo from Guards-B is the cousin).
Plus the security footnote (malicious tool DESCRIPTIONS inject into the agent — MCP servers are prompt-injection
surface; YOUR indirect-injection suite covers it — Phase-5 §9). "USB-C vs hard-wiring, priced per tool in
millisecond receipts" — decide, don't sermonize.

**Q8. Centralized (supervisor) vs decentralized (swarm) orchestration — which did YOU ship, and what would flip you?**

**Answer:** SHIPPED: supervisor (YOUR Agents-B system — hub-and-spoke, every routing decision one logged reason
string, one choke point for the human gate). WHY (three concrete virtues from YOUR runs): reason-about-ability
(misroutes debuggable from ONE log line — YOUR misroute collection), gateability (single interrupt point —
YOUR approve/edit/reject proof), auditability (trajectory narratable node-by-node — the DOD demo). COSTS PAID
(router LLM call per step — YOUR token share from the cost table; single point of failure — supervisor prompt
bug derails everything, YOUR thrash/misroute specimen). WHAT FLIPS TO SWARM (state the tripwires, not
aspirations): router-call share exceeding X% of per-brief cost with no quality contribution (YOUR number as the
tripwire) / supervisor latency flooring p99 below SLO (YOUR p99 row as the tripwire) / need for parallel
specialist execution the hub serializes (YOUR fan-out sketch: two researchers concurrently). "Most production
systems start centralized for control, decentralize where parallelism/robustness demands — HERE are our numbers
for where that line is." Starting position + tripwires + numbers = a defensible architecture, not a preference.

**Q9. Cost and latency at 10k req/day: show the math from YOUR rows.**

**Answer:** ( YOUR write-up's math, built ONLY from measured rows.) Base: per-request-type $/request × YOUR
traffic mix (LLMOps-A baseline table — single/multi/direct/agent rows, never a blended average) × 10k =
daily $ (quote it). Levers APPLIED in order with YOUR deltas: DIRECT-skip (RAG-B router: X% of traffic skips
retrieval entirely — biggest free win, already built); cascade (Phase-5 §8: small-model-first + confidence
escalation — YOUR parity table's escalation rate × price ratio); semantic cache (hit-rate × $/hit from YOUR
replay volume); small-router/big-synthesizer split (supervisor on cheap model — YOUR model-swap table's
compliance check says whether the cheap model routes safely); guard ordering + short-circuit (cheap regex first
— YOUR ms rows); batching/provisioned inference at volume (YOUR §6 benchmark's concurrency knee). Final number:
optimized daily $ + the A/B-quality guardrail (every lever re-validated on Evals-A scores — cost cuts that drop
faithfulness below floor are REJECTED, with the rejected lever named if you have one). "10k requests costs $X
optimized, quality held at Y, HERE's the ladder" — arithmetic, not adjectives.

**Q10. Where does human-in-the-loop sit at scale — and where emphatically NOT?**

**Answer:** AT the highest-cost-of-mistake boundary ONLY (YOUR gate: before publish/send/spend/deploy — the
irreversible/external actions; YOUR gate-catch quoted as the existence proof). NOT on every step (human latency
× 10k/day = absurd queue — YOUR cost math extended: reviewers-needed at 30s/review vs traffic = impossible,
stated). SCALE PATTERN (your write-up's policy): gate ALL high-stakes + SAMPLE low-stakes (spot-check rate from
YOUR critic bite-rate trust data — bite-rate earns sampling; sampling never precedes trust) + auto-approve
below a threshold EARNED from N green weeks (YOUR Evals-B advisory→blocking promotion rule, same muscle) +
eval-gates as the machine first-pass (humans review only flagged/low-confidence cases — YOUR confidence-gate
vocabulary from RAG-B, scaled up). Combine with the resume-proof (kill-switch: process can DIE at the interrupt
— at 10k/day the review queue IS a persistent, resumable system, not a CLI prompt). "Humans at irreversibility,
machines at volume, sampling in between, everything resumable" — the staffing math attached.

---

## Part 3: Synthesis — "Prove the whole arc"

**Q11. Trace one capstone request from user text to deployed response through EVERY phase's contribution.**

**Answer:** (The full-arc narration — rehearse with YOUR trace open.) User prompt → input validators
(Guards-A: PII/jailbreak screens) → router (RAG-B: DIRECT/SINGLE/MULTI — YOUR route + reason) → retrieval
(RAG-A hybrid + rerank; graph paths if multi-hop; §5 ACL pre-filter + §7 vision-parsed chunks if YOUR build
has them — chunk IDs + scores into spans) → agent steps (Agents-A loop or Agents-B team — supervisor reasons
quoted) → guards on context (Guards-B retrieval rails: drops logged) → generation (YOUR SFT/DPO model or base —
prompt version tagged) → output rails + validators (Guards-A/B) → citations resolved → trace with SCORES
attached (LLMOps-A) → served behind probes (LLMOps-B) → CI gate green on merge (Evals-B) + canary clean on
deploy (YOUR proof-table rows). Every arrow names its phase file. THEN the failure-branch narration: "when THIS
request fails, the trace shows [chunk IDs / reason strings / guard verdicts] and I know in one descent whether
it's retrieval, generation, guard, or model — HERE's a real failed trace I diagnosed" (quote it). One request,
twelve phases, one trace — the hireable demo.

**Q12. What breaks in YOUR capstone at 100× traffic, in order — and what did you already pre-build for it?**

**Answer:** Ordered by YOUR measurements (first bottleneck first): (1) GENERATION queueing (dominant span —
YOUR p99-vs-concurrency knee from §6 benchmarks; pre-built: cascade + cache design (§8), runtime choice with
rows); (2) RETRY-STORM under partial failure (agentic chains amplifying a sick dependency 3× — pre-built:
budgets/timeouts/idempotency from §2 write-up, canary alarms on retry-rate); (3) HUMAN-GATE queue (reviewers
don't scale — pre-built: sampling policy + eval-first-pass from Q10); (4) CHECKPOINT STORE (SQLite → Postgres +
TTL/GC — YOUR LLMOps-B portability note); (5) EVAL COST (judge calls × traffic — pre-built: tiered
fast-subset/nightly from Evals-B cost row); (6) STALE MEMORY/corpus drift (research/checkpoints aging —
pre-built: version-stamps + revalidation rule from memory-failure work). Each with the tripwire metric that
FIRES before users hurt (which dashboard, which threshold — YOUR ALERTS.md rows). "100× breaks HERE first
(measured knee), we pre-built THESE three mitigations (named), the next three are tripwired (dashboards named)."
Capacity planning as ordered, evidenced argument — the senior close to the whole roadmap.

---

## How to Use These Questions

1. **Answer with artifacts open** — capstone demo live, §2 write-ups beside you, cost/baseline rows visible.
2. **Every claim carries a number** — reuse rows, win-rates, $/request, tripwire thresholds, detection times.
3. **Narrate the failures** — composition hole found, assumption corrected, sabotage caught: war stories, not slogans.
4. **Close the arc** — any answer may end at Q11's trace: one request through every phase is the whole roadmap in 60 seconds.
