# Interview Questions — Observability + Cost Dashboard (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual dashboards and measurements** — baseline rows, A/B verdict,
redaction queries, first-moving panel, cost projections. Quote the baseline table; that separates
"deployed Langfuse" from "operates with data."

---

## Part 1: Fundamentals — "What do you watch, and why?"

**Q1. Why isn't "the app works on my laptop with --trace prints" observability? What breaks first without it?**

**Answer:** CLI prints are EPHEMERAL (gone when the terminal closes), UNATTRIBUTED (no user/version/request
linkage), UNRETAINED (no trends — "did p99 creep this month?" unanswerable), and UNJOINED (cost lives in the
billing console, quality in eval CSVs, latency nowhere — the three never meet). What breaks first in production
(order from your sabotage replay): SILENT QUALITY ROT (prompt tweak drops faithfulness — nobody re-runs evals
daily; sampled-trace scores would have caught it) → COST SURPRISES (one query class 10× tokens — billing
reveals it weeks later; per-request $ would have paged) → UNDEBUGGABLE INCIDENTS ("users complain answers got
worse Tuesday" — without traces: which requests? which chunks? which prompt version? all unanswerable). Your
before/after: the same sabotage detected in X minutes via dashboard vs never via CLI (the replay proved the
panel moves; the CLI proved nothing without a human watching). Observability converts anecdotes into time series
— that's the entire justification, and your first-moving panel names which series matters most.

**Q2. Walk me through one request's trace, span by span, with what's INSIDE each span.**

**Answer:** (Open Langfuse on YOUR request.) Trace (trace_id = request id, user + prompt_version tags) →
router/loop span (agent path: model, tokens, ms per iteration) → RETRIEVAL span (dense ms, BM25 ms, fusion ms,
AND the chunk IDs + scores as metadata — the diagnostic payload: a trace without chunk IDs can't attribute RAG
failures, your Phase 1 verification checked this explicitly) → RERANK span (model, candidates in/out, ms) →
GENERATION span (model, prompt_version, prompt_tokens, completion_tokens, ms, computed $) → GUARD span
(verdicts per guard, ms) → attached SCORES (eval metrics / user feedback on the SAME trace — quality+cost
joined). Timings sum sensibly to wall-clock (your CLI-vs-dashboard consistency check: Phase-2 `--trace` ms ≈
span ms — agreement = instrumentation trust). Narrate the dominant span (generation, then rerank — matches every
prior forensics reading) and one attribution walk: "bad answer → generation span's chunk-ID metadata shows the
retrieval miss → retrieval bug, not model bug" (the Phase-2 attribution boundary, now permanent infrastructure).

**Q3. Traces vs spans vs logs vs metrics: define each by what question it answers.**

**Answer:** LOGS answer "what happened" (flat timestamped lines — grep-able, causation-free). SPANS answer "what
did THIS unit of work cost" (one LLM call / retrieval / tool: timing + tokens + metadata — the cost atom).
TRACES answer "why was THIS request slow/expensive/wrong" (the causal TREE of spans for one request — parent/
child order shows the critical path; essential for multi-step agents where one user request = N model calls).
METRICS/DASHBOARDS answer "how is the SYSTEM doing" (aggregates over traces: p50/p99, $/request, fire-rates —
the trend layer alerts read). YOUR stack holds all four (app logs + Langfuse spans/traces + dashboards), and the
mapping matters operationally: alerts fire on METRICS, debugging descends to TRACES, cost disputes resolve to
SPANS, forensics grep LOGS. "Which layer do you check first for [incident]?" (p99 spike → metrics→trace→span;
wrong answer → chunk IDs→retrieval span) — rehearse both descents.

---

## Part 2: Cost & Baselines — "Money as a metric"

**Q4. How is per-request cost actually computed? Prove the math is right.**

**Answer:** Per generation span: prompt_tokens × prompt_rate + completion_tokens × completion_rate (model-specific
table — YOUR pricing rows, prompt vs completion split because completion costs 2–4×). Retrieval/rerank spans:
local-model GPU-time or $0-marginal on owned hardware (stated explicitly — "free" means amortized, not zero;
at scale the embedder fleet has a bill too). Request rollup = Σ span costs (agent multi-step = N generations +
tools — the 3–5× team multiplier from Phase 2, now metered). PROOF: 30 replayed requests hand-computed from raw
token counts vs dashboard rollup, within YOUR ±10% (the Phase 2 verification — pricing-table bugs caught HERE,
not in a budget meeting). Footnotes that matter: cached-prefix discounts (if your provider has them — state
handling), judge/synthetic calls EXCLUDED from product $/request (eval spend tracked separately or baselines
lie), currency of model version (price changes re-pin the table — versioned like thresholds).

**Q5. Narrate your baseline table. Why per-TYPE rows instead of one average?**

**Answer:** (Walk YOUR rows.) Single-hop $X / multi-hop ~3X / direct ~0.1X / agent multi-step ~5X (YOUR ratios —
the blended average would read $Y and lie to every capacity plan: it overcharges simple traffic and underfunds
complex). Per-type baselines exist because the COST DISTRIBUTION IS MULTIMODAL (your histogram, if exported:
peaks per type, not one bell — show it). Each row: n (sample size — 30+ or the p99 is fiction), p50/p99 (p99 =
SLO material, p50 = typical), $/request (budget material), tokens/request (the lever), dominant span (where
optimization goes — generation everywhere, rerank second). Consumers named: canary alarms compare per-type
(LLMOps-B imports the file — a blended baseline would false-alarm every multi-hop canary); A/B verdicts read
per-type deltas (v2's +$0.001 on single-hop ≠ +$0.01 on multi-hop). "Average $/request" is the most expensive
lie in LLMOps — your table is the correction.

**Q6. Prompt A/B: v1 vs v2 — verdict, math, and what you'd tell the stakeholder.**

**Answer:** ( YOUR table + verdict.) The four numbers per version (faithfulness w/ trace-attached scores, $/request,
p50) and the DELTAS with noise awareness (score delta vs judge-agreement bounds — Evals-A discipline imported;
cost delta vs replay variance). Verdict branches: SHIP ("+0.06 faithfulness for +$0.0004 (+8%) — quality gain
clears noise, cost within budget — ship with canary watch on multi-hop $"), NO-SHIP ("+0.02 within judge noise
for +40% cost — no"), or SPLIT ("ship v2 for multi-hop only — gains concentrate there; single-hop stays v1" —
the per-type dividend paying off). Stakeholder sentence rehearsed: "v2 costs us $Z/month more at current mix
for +N quality points where it matters, measured on [n] replayed goldens with scores attached to traces."
Prompt versioning (`prompt_registry.py` — get(name, version), every span tagged) is what makes this a REPEATABLE
muscle, not a one-off experiment: rollbacks are version flips, comparisons are tag filters. Without versioning,
prompt work is untracked experiments nobody can reproduce or revert — your registry is the fix, quote its API.

---

## Part 3: Privacy & Reliability — "Observability must not harm"

**Q7. PII in traces: what did you log, what did you redact, and prove the absence.**

**Answer:** Policy: prompts/responses/chunks are DIAGNOSTICALLY NECESSARY (without chunk text you can't judge
retrieval; without prompts you can't debug grounding) but PII-bearing — so `redaction.py` strips entities
(emails/phones/IDs — YOUR recognizer list) BEFORE spans leave the app (client-side, pre-transport — server-side
scrubbing still transmitted the secret). Proof (not screenshots): Postgres queries — `SELECT count(*) WHERE
payload LIKE '%@%'` → 0 (YOUR queries quoted), across all three probe forms (plain, obfuscated, PII-inside-
retrieved-chunk — the chunk path teams forget, YOUR probe covered it). Tradeoff stated: redaction blinds SOME
debugging (can't see the exact email format that broke extraction — mitigated with typed tokens `[EMAIL]`
preserving structure). Compliance line: retention TTL on raw payloads (YOUR setting — traces with payloads age
out, aggregates persist), provider-DPA note for any SaaS in the loop (self-hosted Langfuse = data stays local —
your Q&A's privacy answer). "Prove absence with queries" is the sentence that passes security review.

**Q8. The Langfuse stack died mid-traffic. What happened to the app? Prove observability is advisory.**

**Answer:** (YOUR kill-stack run.) App DEGRADEs (log-and-continue: spans dropped with a counter, requests served
normally — p99 +~0ms, zero 500s attributable) — because tracing calls are wrapped non-blocking with timeouts and
NEVER on the request's critical path for correctness (fire-and-forget with bounded queue; queue-full = drop +
count, not backpressure-into-serving). The dropped-span counter + alert ("telemetry blind since T") is the
honesty mechanism — silent blindness is the failure mode (you'd fly without instruments AND without knowing).
Ordering principle, stated generally: observability is ADVISORY (loss degrades insight, never availability);
guards are ENFORCING (their failure fails closed — the deliberate asymmetry with Guardrails-A, name it).
Interviewers ask because teams HAVE paged on dead dashboards while serving fine — your run proves the ordering,
and the blind-window alert proves you know blindness itself needs monitoring.

---

## Part 4: Alerts & Handoff — "From dashboards to action"

**Q9. Read me your ALERTS.md: rules, thresholds, severity, first response — and which one PROVABLY fires.**

**Answer:** (Rehearse YOUR file.) Rules from YOUR baselines (each threshold cites its baseline row — no magic
numbers): "$/request > 2× type-baseline for 15min" (cost incident — first step: check request-type mix shift vs
per-request inflation via dashboard split); "p99 > SLO for 10min" (latency — first step: dominant-span panel);
"guard-fire-rate spike ×3" (attack-or-regression — first step: sample blocked traces); "sampled faithfulness <
floor" (quality — first step: pull failing trace IDs, check chunk-ID metadata for retrieval vs generation split).
Severity tiers (page vs ticket — cost/Latency page, slow quality drift tickets; rationale per tier). PROVEN:
sabotage replay tripped [rule] in [minutes] (YOUR demo — screenshot + trace IDs; an untested alert is a comment).
Owners + on-call routing named (alerts without owners are logs). The runbook-first-step per rule is what makes
this OPERATIONS, not documentation — "alert fires → human knows the first click" is the bar, and yours clears it.

**Q10. First-moving panel: in the sabotage replay, which signal moved first and what does that teach on-call?**

**Answer:** (YOUR ordering.) Typical: guard-fire-rate or sampled-score moves FIRST (minutes — inline/sampled
quality signals), cost-per-request SECOND (as the degraded path burns more tokens/retries), p99 THIRD (latency
follows the extra work), billing LAST (weeks — useless for incidents). The on-call playbook follows the physics:
page on fast signals (fire-rate, sampled scores), diagnose via traces (chunk IDs → retrieval-vs-generation in
one descent), confirm via cost/latency (blast radius), never wait for billing. YOUR panel ranking quoted with
minute-offsets is a runbook seed no textbook gives ("our sabotage showed scores at +3min, cost at +9min, so our
quality alerts page and cost alerts ticket"). Also the negative lesson: any panel that DIDN'T move (relevancy?
throughput?) is documented as incident-BLIND — knowing what your dashboards can't see is as important as what
they can.

**Q11. Handoff to LLMOps-B: what exactly does the deploy pipeline import, and how did you test the handoff?**

**Answer:** Imports (not copies — single source of truth): `baselines.yml` (canary alarm thresholds per type —
LLMOps-B `canary.py` reads it; drift the file and canaries misjudge — ownership stays HERE), `ALERTS.md`
rules (promoted to canary rollback triggers + prod monitors), prompt-version tags (canary compares v-current vs
v-candidate in-dashboard — the A/B muscle reused for releases). Handoff TEST (not assumption): LLMOps-B setup
step imports both files and runs a canary-compare dry-run against YOUR replayed data (green on your baselines —
proves schema compat; your verification log). Contract discipline: schema changes to either file are
cross-project PRs (consumer + producer review — the anti-rot rule shared with thresholds.yml). "Our canary
alarms ARE our baseline rows" — one breath, files named, compat proven. That's the operational chain made real.

---

## Part 5: Economics — "Cost as a design input"

**Q12. Monthly projection at three volumes: show the math and name the cheapest lever per level.**

**Answer:** (YOUR table.) Math: monthly = Σ_types (share × $/request × volume) — mix-dependence explicit (a
traffic shift toward multi-hop DOUBLES the bill at fixed volume — the per-type dividend again). Levers per
level: 1k/mo (caching frequent queries — near-free, exact-match embed cache kills the dominant cost at low
volume); 100k/mo (smaller embedder/reranker + prompt-version discipline — YOUR A/B cost deltas applied fleet-wide;
guard-order tuning); 10M/mo (batching + model right-sizing (small router, big synthesizer — the agentic cost
trick) + reserved/provisioned inference + aggressive caching + request-type routing (direct-skip saves full
retrieval cost on X% — YOUR RAG-B number returns)). Each lever with YOUR estimated savings (order-of-magnitude
honest, not false precision). The manager sentence: "at our mix, 10× traffic costs ~X× (sublinear via [levers])
— here's the paragraph to budget from." Cost projections with named levers are what turn dashboards into
decisions — your Q&A closes the loop the project opened.

---

## How to Use These Questions

1. **Open the dashboard** — baselines, A/B view, fire-rate panel: answer with the UI visible.
2. **Quote the math** — hand-computed cost check, per-type ratios, monthly rows: numbers or it didn't happen.
3. **Prove the negatives** — redaction queries (absence), kill-stack run (advisory), blind panels (limits).
4. **Draw the chain** — traces → baselines → alerts → canary: one breath, files named, handoff tested.
