# Phase 5 — Synthesis & Frontier: How This Is Done at Production Scale

Companion to the Phase 5 capstone + frontier tracks. Earlier phases taught you to build each layer
(RAG, agents, evals, guards, tuned models, serving) for one user on a laptop; this doc explains what changes
when your CAPSTONE serves real traffic as a product — plus how each frontier technique fares in production.
Read it AFTER the capstone is live — every section assumes you have a URL, metrics, and scars.

---

## 1. The capstone as a product: what "live" actually requires

Your §1 definition of done (URL + green CI + canary + metrics + demo) is the LAUNCH, not the product.
Production operation adds five standing concerns, each with an owner and a cadence:

- **SLOs, stated and reviewed:** availability (99.x — YOUR probes + PDBs + multi-AZ as the evidence),
  QUALITY SLOs (faithfulness floor on live samples — the novel SLO this roadmap teaches: correctness with
  an error budget, burn-down tracked like latency), latency SLOs per request type (YOUR per-type p50/p99
  rows become contractual), cost SLOs ($/successful-task ceiling — the CFO-facing SLO). Reviewed quarterly;
  breached SLOs get error-budget policy (freeze features, spend the budget on reliability — SRE discipline
  applied to AI quality).
- **On-call for a thinking system:** rotation with detect → attribute → mitigate → learn as THE runbook,
  seeded by YOUR first-moving panel (which dashboard signal moved first in your sabotage replay) and response-time
  targets. AI-specific runbook
  entries no generic backend has: "scores sagging with flat latency" (quality incident, not traffic — check
  corpus/model/judge drift), "cost spiking with flat traffic" (mix shift or verbosity drift — check type-split
  panel), "guard-fire-rate spike" (attack or regression — sample blocked traces before touching thresholds).
- **Change management:** every AI-behavior change (prompt version, model swap, corpus re-index, threshold move,
  rail edit) is a FLAGGED, canaried, reversible release through YOUR LLMOps-B path (no exceptions for "just a
  prompt tweak" — prompt tweaks are the #1 production-breaker precisely because they feel safe; your Evals-B
  gate exists because someone learned that the hard way).
- **Data flywheel, operated:** §11 as a staffed loop (feedback volume targets, audit throughput, monthly DPO
  cadence, win-rate-gated promotion — the §11 flywheel as deferred advantage; competitors
  copy features, not flywheels).
- **Sunset criteria:** kill conditions written at launch (quality unrecoverable? cost exceeds value? owner gone?) —
  production systems need euthanasia plans, or they become unmaintained attack surface serving stale answers with
  nobody on-call. State yours.

## 2. Frontier techniques in production: what graduates, what doesn't

Each Phase-5 track, assessed as an OPERATOR (not a builder):

- **§2 agents-at-scale:** graduates ENTIRELY — the write-ups BECOME the
  architecture decision records (ADRs) of your org (budgets, breakers, queues, sharding rules) —
  living docs, re-ratified yearly.
- **§3 reasoning/distillation:** distillation GRADUATES (distilled small models serve cheaply behind cascades —
  YOUR cascade parity table as the promotion evidence); online RL (GRPO/PPO) mostly DOESN'T graduate to small
  teams (needs reward infrastructure + scale you don't have — buy reasoning, distill it, DPO the edges; run RL
  only with a dedicated post-training team).
- **§4 long-context:** prompt caching GRADUATES immediately (pure savings — enable everywhere stable); full-stuff
  architectures DON'T (cost scales with EVERY request's full prefix — your routing rule STAYS the production
  policy: stuff under N tokens, retrieve above; re-derive N yearly as prices move).
- **§5 retrieval upgrades:** ACL pre-filtering GRADUATES unconditionally (compliance non-negotiable — auditors
  accept "impossible by construction," never "we check after"); ColBERT/embedding bake-offs graduate as
  SCHEDULED re-evaluation (yearly, or on corpus 10× growth — not one-time wins); provenance controls graduate
  into the supply-chain checklist (§9).
- **§6 inference optimization:** the benchmark table graduates into CAPACITY PLANNING (node types, concurrency
  limits, quant rungs pinned per model — reviewed per release); the ladder re-runs PER RELEASE on live samples
  (new hardware/prices change the answer, so the table is never finished).
- **§7 multimodal:** vision-parse GRADUATES as an ingest-stage service (versioned parser models — parser upgrades
  re-index, same migration discipline as embedding upgrades); audio pipelines graduate with retention policies
  (raw audio is PII-dense — YOUR redaction discipline extended: transcripts kept, audio TTL'd); CLIP search
  graduates where users ask for it, measured by its own golden set (never assumed useful).
- **§8 routing/cascades:** cascades GRADUATE as the default cost architecture (small-first + confidence-gated
  escalation — YOUR escalation-rate monitored; drift in escalation rate pages, because it means the small model
  or the world changed); semantic cache graduates with INVALIDATION policy (stale-hit rate monitored — cache
  poisoning by corpus change is the incident class; TTL + change-event invalidation, both).
- **§9 red-teaming:** graduates as CADENCE (quarterly central exercises + continuous bug-bounty-style surface +
  post-incident targeted rounds — YOUR indirect suite re-run per release; findings feed EVERY product's golden
  set (one shared pool every product's evals draw from).
- **§10 agent evals:** trajectory scoring graduates into FLEET MONITORING (nightly sampled scoring with drift
  alerts — YOUR bite-rate/recovery-rate panels as standing dashboards); the gated agent metric joins the launch
  checklist (no trajectory coverage, no new-agent GA).
- **§11 flywheel:** graduates as THE compounding strategy (above §1) — the only track that is itself an
  operating model rather than a technique.

## 3. Multi-product reality: platform vs product, second edition

At capstone scale, the build-vs-buy split sharpens into PLATFORM ECONOMICS:

- **Build once, serve N products:** gateway, embedding fleet, vector platform, judge fleet, guard policy-layer,
  model registry, trace infra — each new product's marginal AI cost is prompts + corpus + thresholds, because
  the platforms exist (your capstone REUSED them; the second product reuses them cheaper — platform ROI
  demonstrated by the SECOND launch, priced in your write-up).
- **The customization spectrum, priced:** prompting (days, ~$0) → RAG (weeks, retrieval infra) → adapters
  (weeks + GPU, per-tenant routing) → full post-training (months + team, flywheel included) — YOUR tradeoff
  cheat-sheet with org-calibrated costs attached; product proposals pick a tier with the price visible UP FRONT
  (no "we'll fine-tune later" without the budget line).
- **Governance that scales sublinearly:** launch reviews (YOUR checklist), quarterly risk-register sign-offs
  (YOUR residual lists, aggregated), incident post-mortems feeding shared golden sets (YOUR learn-loop,
  federated) — total governance headcount grows SLOWER than product count, because platforms + checklists absorb
  it. If governance headcount scales linearly with products, the platforms failed — that ratio is itself a KPI.

## 4. The failure modes of success

- **Portfolio drift:** five capstones-in-spirit later, shared platforms forked per product ("just this once"
  custom gateway bypasses) → unmaintainable sprawl. Fix: platform ADRs + exception process (bypasses expire,
  reviewed — YOUR config-review discipline applied to architecture).
- **Metric gaming at scale:** teams optimizing the SLO number instead of the user (faithfulness via shorter,
  safer, less-useful answers — Goodhart's law wearing your metrics). Fix: paired metrics (quality + USEFULNESS/
  task-success — never one alone), human spot-audits that read for value (YOUR trajectory-audit habit, sampled
  org-wide), metric-definition reviews (gaming patterns retire metrics — registry churn is healthy).
- **Flywheel capture:** feedback loops amplifying the majority while starving minorities (corrections come from
  loud users; mined pairs encode their preferences as global truth). Fix: STRATIFIED mining (feedback weighted
  by segment, minority-segment floors on pair counts — fairness as a data-pipeline constraint, YOUR audit bar
  extended) + disparate-impact checks per alignment release (win-rate SPLIT by segment, not just global).
- **Institutional amnesia:** the engineers who ran YOUR break-runs leave; the reasons behind thresholds/rails/
  budgets leave with them. Fix: decision records (YOUR dead-ends tables + policy pages + write-ups ARE the
  institutional memory — onboarding reads them; "why is β 0.1" answerable in 30 seconds by search, forever).
  Stated plainly: docs like these ARE the production system, three years out.

---

**Interview line for this phase:** "I shipped one system end-to-end, then described its production life —
quality and cost SLOs with error budgets, AI-specific on-call runbooks, flagged everything-releases, an
operated flywheel, and a graduate/don't-graduate verdict per frontier technique with the rows behind each.
And I wrote down WHY β is 0.1, so the org still knows after I've left."
