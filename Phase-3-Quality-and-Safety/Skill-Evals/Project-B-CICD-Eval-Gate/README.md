# Project B — CI/CD Eval Gate

**Phase:** 3 — Quality & Safety · **Skill:** Evals · **Difficulty:** Intermediate

Treat evaluations as unit tests: define pass/fail thresholds with custom LLM-as-judge criteria
and **block a build in GitHub Actions** when quality regresses. Same golden set + metrics as
Project A — but enforced automatically on every push instead of run by hand.
**Local-first: DeepEval + pytest locally; the gate runs in CI (Ollama for local dev, hosted
model or self-hosted runner if your CI lacks a GPU/CPU budget for local models).**

Manual evals rot: someone runs the harness once, posts numbers in a README, and six prompt tweaks
later nobody knows quality regressed. The gate fixes that by making quality a hard, versioned,
blocking check — the LLM equivalent of `pytest` failing on `assert expected == actual`, except the
assertion is "faithfulness ≥ 0.8" and the runner is GitHub Actions.

## Links to roadmap.sh/ai-engineer

- Evaluation (regression testing, CI-native evals)
- Production Architecture (release safety — same gate LLMOps B reuses at deploy time)

## Concepts covered

Evals-as-tests (assertions over nondeterministic outputs), custom judge criteria (G-Eval style rubrics
beyond generic faithfulness), threshold design (per-metric floors vs deltas vs baselines), regression
semantics (what counts as a break), CI pipeline structure (lint → tests → evals → block), secrets hygiene,
flakiness control for LLM tests (seeds, sampling, retries), gate-vs-advisory modes.

## Prerequisites

- Evals Project A done (golden set + metric definitions are the test cases — no new dataset work)
- `uv pip install deepeval pytest` (+ your app importable as a module)
- Git + GitHub repo with Actions enabled; YAML basics

## Learning objectives

- Wrap eval cases as pytest tests with thresholds that actually fail on real regressions
- Define custom G-Eval-style criteria for YOUR use case (tone, policy mentions, no-go content)
- Run the suite locally green, then red-team it (inject a regression, watch CI go red)
- Ship a workflow where a quality regression blocks merge — and document the thresholds

## How it works (the gate)

```
git push / PR
  │
  ▼
GitHub Actions: .github/workflows/eval-gate.yml
  │  1. lint + unit tests (fast, cheap — fail early)
  │  2. eval job: checkout → setup Python → install deps → pull model / read LLM secret
  │     → pytest tests/eval_gate.py (DeepEval cases over YOUR app)
  │        │  each case: run app → judge scores vs rubric → assert score ≥ threshold
  │        ▼
  │     pass → green, merge/deploy unblocked
  │     FAIL → red, merge blocked, offending metric + case in the log
  ▼
main stays green by construction; every red run names the metric, case, and commit
```

Threshold philosophy (pick per metric, document WHY in `thresholds.yml`): FLOOR (`faithfulness ≥ 0.75`
— absolute quality bar), DELTA (`recall@5 ≥ baseline − 0.05` — no-regression vs pinned baseline committed
in repo), or both. Floors catch rot; deltas catch regressions that stay above the floor.

## Setup

```bash
uv pip install deepeval pytest
export OPENAI_API_KEY=...        # local only — never commit; CI uses repo Secrets

# Local: green first, then prove it can go red
pytest tests/eval_gate.py -v
deepeval test run tests/eval_gate.py
# Red-team: weaken your RAG prompt (drop the grounding instruction), re-run → must FAIL
git push                           # watch the Actions run go red/green
```

| Flag / file | Where | Default | Meaning |
| ----------- | ----- | ------- | ------- |
| `tests/eval_gate.py` | local + CI | — | DeepEval test cases (assertions + thresholds) |
| `thresholds.yml` | repo | — | per-metric floors/deltas with rationale comments |
| `baseline.json` | repo | — | pinned passing scores; delta-thresholds compare here |
| `--update-baseline` | local only | off | re-pin baseline after an INTENTIONAL quality change |
| CI secret | GitHub Settings → Secrets | — | LLM key as env var; job fails LOUDLY if missing (never silently skips) |

## Project layout (files you will create)

```
cicd-eval-gate/
├── .github/workflows/eval-gate.yml   lint → unit tests → eval job → block on fail
├── tests/
│   ├── eval_gate.py                  DeepEval cases: app call + metric + assert threshold
│   ├── test_unit.py                  fast non-LLM tests (run first, fail early)
│   └── conftest.py                   model/secret setup, skip-with-loud-warning policy
├── thresholds.yml                    per-metric floors + deltas + WHY comments
├── baseline.json                     pinned scores for delta comparison
├── scripts/redteam.py                injects a known regression (prompt weaken / corpus poison)
└── README.md                         this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — App + evals pinned (before any CI YAML)

- [ ] System under test pinned (same commit discipline as Evals A Phase 0); golden set + metrics imported, not rebuilt.
- [ ] Verify: `pytest tests/eval_gate.py` passes locally TWICE (flakiness check — an eval that flakes locally
  will flake in CI, and a flaky gate gets disabled; measure your pass variance now).

### Phase 1 — Eval cases as tests (local, green)

- [ ] `tests/eval_gate.py`: 10–20 DeepEval cases covering your 4 question types; each asserts a metric threshold
  (start with faithfulness + context recall floors from your Evals A noise-aware numbers — thresholds BELOW
  the noise floor are decoration).
- [ ] Custom G-Eval criteria (2–3 for YOUR app): e.g. "cites at least one chunk," "no medical advice,"
  "tone is professional" — rubric + scale + threshold each, in `thresholds.yml` with rationale.
- [ ] Verify: full suite green locally; each case prints metric + threshold + margin (thin margins are future flakes).

### Phase 2 — Red-team the gate (local, red ON PURPOSE)

- [ ] `scripts/redteam.py`: two regressions — (1) weaken the RAG system prompt (drop grounding instruction),
  (2) poison one corpus doc (insert a wrong fact). Re-run suite: at least one case MUST fail per regression.
- [ ] A gate that stays green through sabotage tests nothing — tune thresholds/cases until both red-teams trip it.
- [ ] Verify: restore the app, suite goes green again. Record which metric caught which sabotage (that mapping
  is your gate's coverage proof).

### Phase 3 — CI workflow (green in the cloud)

- [ ] `eval-gate.yml`: jobs in order — lint → unit tests → eval gate (eval runs ONLY if cheap jobs pass).
  LLM key from Secrets; missing key = explicit FAIL (a skipped eval gate is a disabled gate — `conftest.py`
  must error, never `pytest.skip` silently).
- [ ] Pin model versions in the workflow (judge model drift silently moves thresholds — log judge version per run).
- [ ] Verify: push a clean commit → green run with per-case scores visible in the log.

### Phase 4 — Regression blocks merge (red in the cloud — the deliverable)

- [ ] Push the red-team branch (weakened prompt) as a PR → run MUST go red and block merge (branch protection
  on the eval job, or at minimum a documented "do not merge on red" + screenshot).
- [ ] Revert → green. Update `baseline.json` ONLY via explicit `--update-baseline` runs tied to intentional
  changes (baseline updates are reviewed changes, not side effects).
- [ ] Write the 1-page gate policy: what blocks (floors? deltas? which metrics), who can update baselines,
  flake protocol (re-run N times? quarantine case?), cost per run (LLM judge calls × price — CI evals have a
  budget too).

---

## Core experiments (fill in YOUR numbers)

### 1. Red-team coverage ← the core objective

| Sabotage | expected tripwire | tripped? (metric + case) | margin (score vs threshold) |
| -------- | ----------------- | ------------------------ | --------------------------- |
| weakened grounding prompt | faithfulness floor |                 |                             |
| poisoned corpus fact | faithfulness / custom "no-X" criterion |      |                             |
| chunk-size swap (300→1200) | context recall delta |              |                             |
| judge model swap | none (robustness check) |                    |                             |

**What to look for:** each sabotage trips ≥1 case with MARGIN (a trip by 0.01 is a future flake — widen the
case or lower the floor honestly). The judge-swap row should trip NOTHING — if it trips, your thresholds are
judge-overfitted (recalibrate across two judges, Evals A Phase 4 method).

### 2. Flakiness audit

Run the suite 3× locally + 2× in CI on the SAME commit. Record per-case pass/fail + score spread.
Any case failing ≥1 of 5 needs: more samples, looser threshold, or removal to advisory (non-blocking).
A gate with known flakes ships with a quarantine list — document yours.

### 3. Break it deliberately

- Remove the CI secret → push: confirm LOUD fail (not silent skip/green). This is the most common real-world
  gate failure — prove yours can't do it.
- Push a docs-only change: suite still runs (correct — cheap) — or implement path-filters and justify them
  (app/corpus/prompt paths trigger evals; README-only skips; record the rule).
- Open a PR that IMPROVES quality (better chunking): delta-thresholds stay green, floors stay green, and you
  practice the `--update-baseline` flow to pin the new higher baseline.

### 4. Cost accounting

Count judge LLM calls per full run × price (or local GPU minutes). State cost-per-push and monthly projection
at your team's push rate. If it's expensive, design the tiering: fast subset on every push, full suite nightly
+ on PRs touching app/corpus/prompts. Implement the tier split if cost justifies it.

## Observations worth writing down as you go

1. **Tripwire mapping** — which metric catches which sabotage class; gaps are uncovered failure modes.
2. **Flake list** — cases that wobbled, why (sampling? judge variance? thin margin?), and their disposition.
3. **Threshold rationale** — every number in `thresholds.yml` traces to a measured noise floor or quality bar.
4. **Secret-missing behavior** — proven loud-fail, with the log line quoted.
5. **Cost per run** — judge calls × price; the tiering decision it drove.

## Definition of done

- `pytest tests/eval_gate.py` green locally AND in GitHub Actions on a clean push.
- Both red-team sabotages turn the CI run red (screenshot/log linked), blocking merge.
- `thresholds.yml` documents every threshold with rationale; `baseline.json` pinned via explicit flow.
- Gate policy page written: what blocks, baseline-update rules, flake protocol, cost per run.
- Missing-secret push fails loudly (proven, not assumed).

## Reference material

- DeepEval: https://github.com/confident-ai/deepeval · G-Eval: https://arxiv.org/abs/2303.16634
- GitHub Actions docs: https://docs.github.com/en/actions · branch protection: same docs, "protected branches"

## Next

Phase 4 LLMOps B reuses this gate at DEPLOY time (pre-merge → pre-deploy). Guardrails next: evals MEASURE
quality, guards ENFORCE safety — the gate blocks regressions, rails block attacks.
