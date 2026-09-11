# Project B — Serving + Eval-Gated CI/CD

**Phase:** 4 — Customization & Production · **Skill:** LLMOps · **Difficulty:** Intermediate–Advanced

Serve a model behind a REST API, containerize it, deploy to Kubernetes (minikube) via
GitHub Actions, and **block deploys when evals fail** — with canary rollout + automatic rollback.
**The synthesis of the operational half of the roadmap: Evals-B gate (pre-merge) + baselines
(LLMOps-A) + probes + canary (this project, pre/during-deploy).**

Every prior phase produced artifacts this project assembles: the model (base, SFT, or DPO — YOUR
fine-tune served for real), the eval gate (Evals B thresholds block the pipeline), the baselines
(LLMOps A numbers become canary alarms), the guards (wrapped around the served endpoint). A deploy
that passes tests but fails evals never reaches the cluster; a canary that trips alarms rolls back
automatically. That sentence is the whole project.

## Links to roadmap.sh/ai-engineer

- Deployment / Production Architecture (serving, containers, K8s, release safety)
- Reuses the eval gate from the Evals skill (same principle, deploy stage) + baselines from LLMOps A

## Concepts covered

Model serving (FastAPI + inference backend: Ollama-simple vs vLLM-throughput, batching/paged-attention
intuition), containerization (multi-stage Dockerfiles, layer caching, artifact pinning), Kubernetes
(deployments, services, readiness/liveness probes, resource limits, minikube as local cluster), CI/CD
pipeline composition (lint → tests → eval gate → build → deploy), deploy-time eval gating, canary
releases (traffic splitting, bake time, promotion/rollback criteria), rollback mechanics, alarm wiring
(baseline → canary metric → auto-rollback).

## Prerequisites

- Evals Project B (eval gate + thresholds — imported, not rebuilt) and LLMOps A (baselines + alerts)
- A model artifact to serve (your DPO/SFT GGUF or base — serving YOUR model closes the loop)
- Docker, minikube + `kubectl`, GitHub Actions; `pip install fastapi uvicorn` (+ vLLM optional)

## Learning objectives

- Serve a model behind a production-shaped API (`/generate`, `/health`, readiness semantics)
- Containerize reproducibly (pinned deps + artifact, small image, non-root, resource limits)
- Build a pipeline where eval failure blocks deploy — proven by a red-team deploy, not asserted
- Execute a canary with automatic rollback on eval/alarm failure, end to end on minikube

## How it works (the release path)

```
git push / PR
  │
  ▼
CI (.github/workflows/release.yml):
  1. lint + unit tests (fast fail)
  2. EVAL GATE (Evals-B suite vs thresholds.yml — FAIL → stop, no image built)
  3. build image (multi-stage Dockerfile, model artifact pinned by digest/hash)
  4. push → deploy to minikube (kubectl apply manifests/)
  │
  ▼
K8s: Deployment (N replicas, readiness/liveness probes, resources) + Service
  │
  ▼
CANARY: new version → 10% traffic, bake 10 min, compare vs baselines.yml alarms
  │  metrics OK + eval-sample pass → promote to 100%
  │  alarm/eval fail → AUTOMATIC rollback to previous ReplicaSet (previous image STILL TAGGED)
  ▼
stable serving + Langfuse traces flowing (LLMOps-A instrumentation inside the served app)
```

Two gates, different moments: EVAL GATE blocks bad builds pre-deploy (cheap, deterministic-ish);
CANARY+ROLLBACK catches what evals miss post-deploy (real-traffic behavior). Neither alone suffices.

## Setup

```bash
# Local cluster + serving
minikube start --cpus=4 --memory=8192
docker build -t my-llm:v1 -f Dockerfile .
kubectl apply -f k8s/                         # deployment + service + probes
kubectl get pods -w                            # readiness gates traffic until model loaded

# Release flow
git push                                       # CI: lint → tests → eval gate → build → deploy
kubectl rollout status deployment/llm-api
python scripts/canary.py --new v2 --traffic 10 --bake 10m   # watch promote or auto-rollback
```

| File | Meaning |
| ---- | ------- |
| `app/main.py` | FastAPI: `/generate` (guarded, traced) + `/health` (liveness) + `/ready` (readiness: model loaded?) |
| `Dockerfile` | multi-stage (build deps ≠ runtime), pinned versions, model artifact by hash, non-root user |
| `k8s/deployment.yaml` | replicas, probes (readiness waits for model load!), resources/limits |
| `k8s/service.yaml` | stable endpoint across rollouts |
| `.github/workflows/release.yml` | lint → tests → **eval gate** → build → deploy (gate failure = no build) |
| `scripts/canary.py` | traffic split, bake, baseline-compare, promote/rollback driver |
| `thresholds.yml` + `baselines.yml` | imported from Evals-B / LLMOps-A (single source of truth, not copies) |

## Project layout (files you will create)

```
serving-eval-gated-cicd/
├── app/
│   ├── main.py              FastAPI: /generate + /health + /ready (model-load-aware)
│   └── guard_wrap.py        guards (Phase 3) + tracing (LLMOps-A) around inference
├── Dockerfile               multi-stage, pinned, hashed artifact, non-root
├── k8s/
│   ├── deployment.yaml      replicas, probes, resources
│   └── service.yaml         ClusterIP/NodePort + minikube tunnel notes
├── .github/workflows/
│   └── release.yml          full pipeline with eval gate
├── scripts/
│   ├── canary.py            canary driver (split/bake/compare/promote/rollback)
│   └── redteam_deploy.py    bad-model builder (weakened prompt/adapter) for gate proof
├── thresholds.yml           ← symlink/import from Evals-B (don't fork it)
├── baselines.yml            ← symlink/import from LLMOps-A (don't fork it)
└── README.md                this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Artifact + thresholds pinned (before any YAML)

- [ ] Choose the served artifact (your DPO GGUF recommended — the roadmap's full arc in one deployment)
  and pin it by HASH (digest in Dockerfile + logged at startup — "which model is live?" must be answerable).
- [ ] Import (don't copy) `thresholds.yml` + `baselines.yml` — one source of truth; forks drift and gates rot.
- [ ] Verify: artifact runs locally via `uvicorn` with guards + tracing active (serve green before cluster).

### Phase 1 — Serving + container (production-shaped, locally)

- [ ] `app/main.py`: `/generate` (validate → guards → inference → trace), `/health` (alive?),
  `/ready` (model LOADED? — readiness must fail during warmup; test by hitting it in the first seconds).
- [ ] `Dockerfile`: multi-stage, pinned deps, non-root, artifact hash verified at build; image size recorded
  (multi-stage should roughly halve it — note yours).
- [ ] Verify: `docker run` serves correctly; `/ready` false-then-true across restart (probe semantics proven
  before K8s ever sees them).

### Phase 2 — K8s on minikube (orchestration basics)

- [ ] `k8s/`: Deployment (2 replicas, CPU/memory limits, readiness+liveness probes with tuned periods),
  Service; `minikube start`, apply, `kubectl get pods -w` shows readiness-gated rollout.
- [ ] Kill-a-pod drill: `kubectl delete pod` → K8s reschedules, Service uninterrupted (liveness + replicas
  working — log the recovery time).
- [ ] Slow-start drill: deploy with an artificial 30s model-load sleep → confirm ZERO traffic hits the pod
  until `/ready` flips (readiness saving you from cold-start 500s — the probe lesson made tangible).
- [ ] Verify: steady-state serves with traces flowing to Langfuse (LLMOps-A loop closed).

### Phase 3 — Eval-gated pipeline (bad builds never ship)

- [ ] `release.yml`: lint → unit tests → EVAL GATE (Evals-B suite; fail = pipeline stops, NO image build —
  building-then-discarding is wasted compute AND a confusion risk).
- [ ] Red-team deploy: push `redteam_deploy.py`'s weakened model → pipeline MUST go red at the gate with the
  failing metric named; cluster still serves the OLD version (`kubectl rollout history` proves no rollout happened).
- [ ] Revert → green → rollout proceeds. Verify the full green path end-to-end once.

### Phase 4 — Canary + auto-rollback (the deliverable)

- [ ] `canary.py`: deploy v2 alongside v1 at 10% traffic, bake (10 min), compare live metrics vs
  `baselines.yml` alarms + sampled evals; promote (100%) or ROLLBACK automatically.
- [ ] Prove BOTH directions: good v2 promotes (log the promotion); poisoned v2 (red-team artifact at 10%)
  trips an alarm/eval and rolls back WITHOUT human action (log the rollback + time-to-detect).
- [ ] Previous image retained + tagged (rollback target always exists — verify `rollout history` shows it).
- [ ] Write 1-page release policy: gate thresholds, canary %, bake time, rollback triggers, who approves
  production promotes, post-rollback procedure (quarantine artifact? page who?).

---

## Core experiments (fill in YOUR numbers)

### 1. Gate + canary proof table ← the core objective

| Scenario pushed | CI gate verdict (metric that tripped) | reached cluster? | canary verdict | final state |
| --------------- | ------------------------------------- | ---------------- | -------------- | ----------- |
| clean v1 | green | yes | promote | v1 @100% |
| weakened-prompt v2 (red-team) | RED (faithfulness __) | NO (no build) | n/a | v1 undisturbed |
| poisoned v2 direct-to-canary | (bypass test only) | 10% | ROLLBACK (alarm: __) | v1 restored in __s |

**What to look for:** row 2 proves the pre-deploy gate; row 3 proves the post-deploy net. A team with only
row 2 ships eval-blind canaries; only row 3 wastes clusters on builds evals would have caught. Time-to-detect
on row 3 is your incident-response number — quote it.

### 2. Probe semantics proof

| Drill | observed behavior | what it proves |
| ----- | ----------------- | -------------- |
| kill one pod | rescheduled in __s, 0 failed client requests (or N — honestly) | liveness + replicas |
| 30s slow-start deploy | 0 requests to warming pod until ready (log counts) | readiness gates traffic |
| resource-limit breach (load test) | throttled/OOMKilled? pod behavior + recovery | limits are real, not decorative |

### 3. Break it deliberately

- Push with the eval-gate job REMOVED from the workflow (simulate gate-skipping): red-team artifact deploys —
  then canary must still catch it (defense in depth proven by removing a layer on purpose).
- Roll back the rollback: after auto-rollback, confirm v1 serves AND its traces/evals look healthy (rollbacks
  can restore a stale-bad version — verify, don't assume).
- Image without pinned digest (`:latest`): demonstrate the ambiguity ("which model is live?" unanswerable) —
  then re-pin. Tag discipline learned the hard way, cheaply.

### 4. Cost + size accounting

Image size (single-stage vs multi-stage), CI minutes per run (eval gate share itemized — the Evals-B cost row
returns), minikube resource footprint, projected cluster cost at 2 traffic levels. The "what would production
cost" paragraph (EKS/GKE equivalent named, same manifests asserted portable).

## Observations worth writing down as you go

1. **Gate-vs-canary division** — which failure class each layer caught in YOUR red-teams (they catch different things).
2. **Readiness save** — the slow-start request counts proving probes aren't ceremony.
3. **Time-to-detect/rollback** — your canary's incident number; what dominates it (bake time? alarm lag?).
4. **Digest discipline** — the `:latest` ambiguity demo and the hash-pinning rule it produced.
5. **Manifest portability notes** — what changes minikube→managed K8s (and what doesn't — the learning that transfers).

## Definition of done

- Served artifact (YOUR fine-tune) live on minikube behind probes, guarded + traced, model hash answerable.
- Red-team push blocked at the CI eval gate (log linked); cluster untouched (rollout history proves it).
- Canary demonstrated BOTH ways: good version promotes, poisoned version auto-rolls-back (times logged).
- Release policy written: thresholds source, canary params, rollback triggers, approval + post-rollback procedure.

## Reference material

- sarthxk20/llmops-platform: https://github.com/sarthxk20/llmops-platform
- Terraform LLMOps canary platform: https://github.com/Theepankumargandhi/Terraform-Based-LLMOps-Platform-for-Evaluation-Gated-Canary-Deployment
- K8s docs (deployments, probes, rollbacks): https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

## Next

Capstone (Phase 5): this release path is what ships it — same gates, same canary, one integrated system.
Your release policy + baselines + thresholds transfer directly; only the artifact changes.
