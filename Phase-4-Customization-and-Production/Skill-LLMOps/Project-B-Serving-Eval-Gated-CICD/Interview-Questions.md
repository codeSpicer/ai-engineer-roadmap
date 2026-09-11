# Interview Questions — Serving + Eval-Gated CI/CD (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual cluster and pipeline runs** — gate logs, probe drills, canary
table, time-to-detect, image/cost rows. Quote the proof table; that separates "wrote manifests" from
"ships safely."

---

## Part 1: Serving — "Production-shaped inference"

**Q1. Why FastAPI + `/generate` + `/health` + `/ready` — what does each endpoint guarantee, and why split health from readiness?**

**Answer:** `/generate` (the product: validate → guards → inference → trace — YOUR guarded+traced path, not a
bare model call; every production concern from Phases 3–4 composed in one handler). `/health` (LIVENESS: is the
process alive — K8s restarts on failure; cheap, never touches the model). `/ready` (READINESS: is it safe to
SEND TRAFFIC — model loaded? warm? deps reachable? — K8s withholds traffic until true). The split is the
interview point: a pod can be ALIVE but UNREADY (30s model load — your slow-start drill: 0 requests served
until `/ready` flipped, request counts quoted), and conflating them routes traffic into warming pods (cold-start
500s — the failure your drill makes tangible). Probe periods/thresholds tuned (YOUR values — period vs
detection-speed tradeoff stated). "Liveness restarts the dead, readiness shields the warming" — then the drill
numbers.

**Q2. Ollama vs vLLM behind the API: what did you serve, why, and when would you switch?**

**Answer:** (YOUR choice + reasoning.) Ollama: single-binary simplicity, GGUF-native (YOUR fine-tune drops in),
fine for learning-scale and low-concurrency — the right default when throughput isn't the lesson. vLLM: Paged
Attention (KV-cache memory efficiency → bigger batches fit), CONTINUOUS batching (no padding-wait — requests
join the running batch; throughput 2–10× on concurrent load), at the cost of ops complexity (GPU scheduling,
engine tuning). Switch rule (state YOURS): sustained concurrent requests where p99 queues (YOUR load observation
— queueing appeared at N concurrent; below that Ollama's simplicity wins, above it vLLM's batching pays).
Throughput intuition to voice: LLM serving is memory-bandwidth-bound (KV cache per sequence), so batching =
amortizing the same weight-reads across requests — that's WHY vLLM's batching matters (not "it's faster" but
"it shares the bottleneck"). Your served choice + the switching threshold = capacity planning stated plainly.

**Q3. Multi-stage Dockerfile: what's in each stage, what got left behind, and prove the discipline.**

**Answer:** BUILD stage (compilers, dev headers, pip cache — everything needed to COMPILE deps) → RUNTIME stage
(slim base + installed packages + model artifact ONLY — no compilers, no caches, no git history). Left behind
(measured): build tools (~hundreds of MB), pip cache, test files — YOUR single-vs-multi size row (e.g. 3.1GB →
1.4GB quoted). PLUS the non-size disciplines: pinned versions (every line versioned — unpinned = unreproducible
deploys; the `:latest` break-run's ambiguity quoted), artifact by HASH (digest in Dockerfile + startup log —
"which model is live?" answerable in one command), non-root USER (blast-radius containment — exploited process
≠ root), `.dockerignore` (no secrets/corpora baked into layers — AND layer-history checked for accidental keys).
Size is the visible win; pinning + hash + user are the operational wins — state all four with YOUR numbers.

---

## Part 2: Kubernetes — "Orchestration that earns its YAML"

**Q4. Deployment + Service + probes + limits: what does each K8s object do for YOUR app?**

**Answer:** DEPLOYMENT (desired state: N=2 replicas of image@digest — self-healing (dead pod rescheduled —
YOUR kill-drill recovery time) + declarative rollouts/rollbacks (`rollout history` = release ledger)).
SERVICE (stable endpoint across pod churn — clients never track pod IPs; rollout/canary traffic math attaches
here). READINESS probe (traffic gate — YOUR slow-start counts) + LIVENESS probe (deadlock recovery — YOUR kill
vs hang distinction: killed pod reschedules; HUNG process (simulate: sleep-infinity handler) needs liveness to
catch what readiness can't — run it if you haven't). RESOURCES (requests = scheduler placement promises; limits
= OOMKill/CPU-throttle boundaries — YOUR breach drill: throttled vs evicted behavior + recovery, quoted).
Minikube note: single-node portability (SAME manifests apply to EKS/GKE — the learning transfers; node-count
and storage classes differ — your portability notes). "K8s gives us self-healing, gated traffic, bounded blast
radius, and boring rollbacks" — four nouns, four drills.

**Q5. Narrate your probe drills. What did you break, what did K8s do, and what would have happened bare-metal?**

**Answer:** ( YOUR three rows.) KILL-A-POD: `kubectl delete pod` → rescheduled in Xs, client impact N failed
requests (ideally 0 — 2 replicas + Service drain; quote honestly) — bare-metal: outage until human restarts.
SLOW-START (30s load sleep): 0 requests to warming pod (request counts per pod quoted) — bare-metal/LB-without-
checks: cold-start 500s served to users. LIMIT-BREACH (load test past memory limit): OOMKilled → rescheduled
(log line quoted) or CPU-throttled (latency, not death — the distinction: memory kills, CPU slows). Each drill's
bare-metal counterfactual is the interview move: probes/replicas/limits aren't ceremony, they're the specific
outages you just watched NOT happen. Time-to-recover per drill quoted — those are your mini-SLOs, and the canary
bake time (Q9) is calibrated against them (rollback must complete faster than users notice — connect the numbers).

**Q6. Resource limits: how did you SIZE them (not guess), and what happens at the boundary?**

**Answer:** Sizing from MEASUREMENT: model RSS at load (YOUR GB — artifact size + KV cache at target concurrency
+ headroom %) → memory limit; p99-latency-vs-CPU curve knee → CPU limit (YOUR millicores). Requests = steady-state
measured (scheduler packs honestly); limits = peak + margin (burst absorbed, runaway contained). Boundary
behaviors DEMONSTRATED (not documented-from-memory): memory → OOMKill + reschedule (log quoted; client saw
[retryable 5xx / zero impact with 2 replicas]); CPU → throttle (p99 degrades smoothly — YOUR latency-vs-limit
note; throttling is graceful, killing is not — which is why memory margins run fatter). The anti-patterns named:
no-limits (one bad pod eats the node — noisy-neighbor death), limits==requests for bursty LLM workloads
(throttles the normal case — wasteful). "Our limits are measured, our margins are stated, our boundary behavior
is drilled" — resource policy as engineering, not YAML folklore.

---

## Part 3: The Gates — "Two moments, one metric chain"

**Q7. Eval gate (pre-deploy) vs canary alarms (post-deploy): which catches what? Prove you need both.**

**Answer:** GATE catches KNOWN-measured regressions pre-deploy (weakened prompt → faithfulness floor trips in CI
— YOUR row-2 log; cheap: no cluster touched, no users exposed; blind spot: anything the golden set doesn't cover
+ live-traffic distribution shift). CANARY catches UNKNOWN-live failures post-deploy (poisoned v2 at 10% trips
baseline alarms on REAL traffic — YOUR row-3 log with time-to-detect; expensive: cluster + bake time + 10%
exposure; blind spot: slow drift inside alarm bands). The MUTUAL-COVER proof: gate-REMOVED drill (row: red-team
artifact sailed through CI — then CANARY caught it — defense in depth demonstrated by removing a layer ON
PURPOSE) and the inverse reasoning (canary-absent: gate-green-but-distribution-shifted model serves 100% blind —
name a shift class your golden set misses, e.g. new user phrasing season). "Gate blocks the stupid, canary
catches the surprising" — different moments, different failure classes, SHARED metric definitions (same
thresholds.yml/baselines.yml — one chain, two enforcement moments, Q13's diagram).

**Q8. Narrate the proof table: clean v1, red-team v2 at the gate, poisoned v2 in canary.**

**Answer:** (Walk YOUR three rows with logs open.) ROW 1 (clean v1): CI green (lint→tests→gate margins quoted) →
image built → minikube rollout → canary 10%→bake→metrics within baselines → promote 100% (promotion log +
post-promote trace health). ROW 2 (weakened-prompt v2): CI RED at eval gate (faithfulness X vs floor Y — metric
named), NO image built (compute not wasted AND confusion avoided), `rollout history` shows cluster untouched
(the negative proof — NOTHING happened in prod, verifiably). ROW 3 (poisoned v2 direct-to-canary, bypass-test):
10% traffic → alarm [which] tripped at +T seconds (YOUR time-to-detect) → AUTOMATIC rollback (no human;
rollback completion time quoted) → v1 restored + verified healthy (post-rollback trace/eval check — rollbacks
can restore stale-bad; yours was verified). The table's moral, stated: "row 2 saves clusters, row 3 saves users,
row 1 proves the happy path isn't broken by all this safety." Three rows, full release confidence.

**Q9. Canary parameters: why 10%, why that bake time, what promotes, what rolls back?**

**Answer:** (YOUR policy values, each defended.) TRAFFIC %: 10% (enough for signal — YOUR n requests in bake
window gives the alarm metrics statistical legs; small enough for blast radius — 10% × T minutes × failure rate
= bounded user harm, computed). BAKE TIME: 10 min (≥ time-to-detect measured in drills + metric lag (Langfuse
aggregation delay — YOUR minutes) + margin; shorter bakes ship undetected regressions, longer bakes slow every
release — the tradeoff stated with YOUR detection-lag number). PROMOTE: all alarms green + sampled-eval pass +
manual approval (YOUR approval rule — auto-promote vs human-gated, and which you chose for prod vs learning).
ROLLBACK TRIGGERS: any baseline alarm breach + eval-sample floor trip (automatic, no quorum — speed beats
consensus mid-incident; the human reviews AFTER). Previous ReplicaSet retained + tagged (rollback target EXISTS
— `rollout history` shown; retention count stated). "Our canary numbers are calibrated to our measured detection
lags" — parameters from data, not folklore (10%/10m defaults are STARTING points your drills confirmed or
adjusted — state which).

---

## Part 4: Policy & Economics — "Releases as social systems"

**Q10. Rollback completed. Then what? (The post-rollback procedure most teams forget.)**

**Answer:** (YOUR policy page, rehearsed.) Immediate: VERIFY v1 health (traces + sampled evals green —
rollbacks CAN restore stale-bad; verification is mandatory, not optimistic) → QUARANTINE the bad artifact
(tag + image quarantined, digest recorded, redeploy BLOCKED by digest-deny rule — prevents "oops, re-pushed"). 
Then: PRESERVE evidence (canary metrics snapshot + trace IDs + alarm log linked to the incident) → ATTRIBUTE
(gate gap or novel class? quarantine routes to: threshold fix (Evals-B PR) vs new-cases (golden PR) vs new-alarm
(canary tuning)) → COMMUNICATE (who was exposed: 10% × T min — exposure math stated; who gets told: on-call →
team → users-if-harm). Finally: POST-MORTEM with one action item per layer that missed (gate case added?
alarm threshold moved? reviewer assigned?). "Rollback is the MIDDLE of the incident, not the end" — the teams
that stop at restore ship the same bug next month; your quarantine→attribute→action chain is what makes rollback
a learning system instead of a reset button.

**Q11. What does this cost — image, CI minutes, cluster — and what would production cost?**

**Answer:** (YOUR accounting rows.) IMAGE: single-vs-multi size (GB + pull-time implication — big images slow
rollouts; YOUR seconds), registry storage trivial. CI: minutes per green run (lint:X + tests:Y + eval-gate:Z —
the gate's share itemized, Evals-B cost row returning; red runs cheaper (fail-fast) — state both). CLUSTER:
minikube footprint (YOUR CPU/RAM — free locally, but the managed equivalent priced: N nodes × type $/mo for
YOUR replica/resource spec on EKS/GKE — named instance math, order-of-magnitude honest). PROJECTION at 2 traffic
levels (replicas scale ~linearly to point X, then vLLM/GPU nodes change the curve — the scaling kink named).
The budget sentence: "each release costs $A in CI + $B/mo serving at current scale; 10× traffic ≈ $C via
[replicas/GPU-note]." Teams that can't price releases can't plan them — your paragraph is the planning input.

**Q12. Minikube here, EKS/GKE there: what transfers, what changes, and what's the migration checklist?**

**Answer:** TRANSFERS (identical): manifests (Deployment/Service/probes/limits), release pipeline SHAPE
(lint→tests→gate→build→deploy→canary), metric definitions + thresholds + baselines, digest discipline,
rollback mechanics (`rollout undo` works the same). CHANGES: nodes (single → multi-AZ node groups + autoscaling
— YOUR autoscale rule sketch: GPU-node pool for inference, CPU pool for API), traffic (NodePort/tunnel →
Ingress + real load balancer + TLS), state (local Langfuse Postgres → managed DB + backups + retention policy),
secrets (repo Secrets → cloud secret manager + rotation), registry (local → ECR/GCR with lifecycle rules),
observability (same Langfuse, now HA + SLO dashboards paging real on-call). CHECKLIST (your portability notes):
[ ] secrets migrated [ ] ingress+TLS [ ] node pools + autoscale [ ] PDBs (disruption budgets — 2 replicas mean
nothing if both drain at once) [ ] backup/restore drilled [ ] cost alerts on. "Minikube taught the
architecture; the checklist prices the migration" — learning complete, path forward explicit.

---

## How to Use These Questions

1. **Show the trinity** — gate-red log, rollout history (untouched), canary rollback log: three proofs, one story.
2. **Quote detection times** — time-to-detect, rollback duration, recovery per drill: incident numbers, not adjectives.
3. **Run a drill live** — kill-a-pod or slow-start: 60 seconds of K8s doing its job, narrated.
4. **Price everything** — CI minutes, image GB, cluster $/mo: releases are budget items, show the budget.
