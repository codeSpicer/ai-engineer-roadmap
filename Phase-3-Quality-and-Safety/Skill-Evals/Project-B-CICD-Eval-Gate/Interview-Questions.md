# Interview Questions — CI/CD Eval Gate (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual code and measured runs** — red-team logs, flake audits, threshold
rationale, cost rows, CI screenshots. Quote the coverage table; that separates "added a YAML file" from
"quality is enforced."

---

## Part 1: Fundamentals — "Evals as tests?"

**Q1. What does "treat evals as unit tests" mean mechanically — and where does the analogy break?**

**Answer:** Mechanically: each eval case is a test function asserting a metric threshold —
`assert faithfulness(case) >= 0.75` in `tests/eval_gate.py` — run by pytest inside GitHub Actions, where a
failed assert exits nonzero, turns the run red, and blocks merge. Same shape as unit tests: named cases,
thresholds as expected values, CI as enforcer, history showing which commit broke what. Where it BREAKS
(say unprompted): LLM outputs are NONDETERMINISTIC (same commit can score 0.78 then 0.74 — unit tests never
do that) and JUDGED (the "assertion" is itself a model with biases — no unit test's `==` has opinions).
Those two breaks drive the entire project design: noise-aware thresholds (Evals A noise floor), flake audits,
judge versioning, and quarantine lists. The analogy gets you the pipeline; the breaks get you the engineering.

**Q2. Walk me through one push, file by file. What runs, in what order, and what stops the merge?**

**Answer:** Push → `.github/workflows/eval-gate.yml`: (1) LINT + `test_unit.py` (fast, cheap, fail-early —
no GPU/LLM spend on broken syntax); (2) eval job: setup Python, install deps, inject the LLM secret from
repo Secrets, `pytest tests/eval_gate.py -v` (each DeepEval case: run YOUR app → judge vs rubric → assert
threshold from `thresholds.yml`); (3) green → merge unblocked (and LLMOps-B's release pipeline may proceed);
RED → run fails, and with branch protection on the eval job (or documented no-merge-on-red), the PR can't
merge. `conftest.py` guarantees the loud-fail property: missing secret = explicit ERROR, never silent skip
(your secret-removed break-run proves it). `baseline.json` backs delta-thresholds: the run diffs current
scores against pinned passing scores. Name the failing metric + case + commit from YOUR red-team PR — that's
the whole system in one log.

**Q3. Floors vs deltas: what threshold types did you set, and why both?**

**Answer:** FLOOR: absolute bar (`faithfulness >= 0.75`) — catches slow rot (five individually-shippable
regressions summing to garbage still trip the floor eventually). DELTA: no-regression vs pinned baseline
(`recall@5 >= baseline − 0.05`) — catches sharp drops that stay ABOVE the floor (0.90→0.78 is a regression
worth blocking even though 0.78 "passes"). Your `thresholds.yml` holds both per metric WITH rationale comments
tracing each number to a measured noise floor or quality bar (Evals A numbers — thresholds inside the noise
band fire on luck, and your flake audit proves you checked). Update discipline differs: floors change on
product decisions (reviewed), deltas re-pin via explicit `--update-baseline` runs on intentional improvements
(also reviewed — never auto). One line for interviews: "floors defend quality, deltas defend momentum."

---

## Part 2: Custom Criteria — "Beyond generic faithfulness"

**Q4. What are custom G-Eval-style criteria, and what 2–3 did YOU define? Why those?**

**Answer:** Custom criteria extend judging beyond generic RAG metrics into YOUR product's contract: a rubric
("what good means HERE") + scale + threshold, evaluated by the judge model per case. Yours (quote them with
thresholds): e.g. "cites ≥1 chunk" (grounding contract — catches citation-less fluency the generic metrics
underweight), "no medical/financial advice beyond sources" (safety contract — your Guardrails vocabulary in
eval form), "tone is professional" (product contract). Each needs the same validation as generic metrics
(human agreement spot-check — a custom criterion nobody validated is a vibe with YAML). Why custom at all:
generic faithfulness passes an answer that's true, cited, and wildly off-brand — the product owner cares, the
generic metric doesn't. Your red-team mapping shows which sabotage each custom criterion catches (poisoned fact
→ "no-X" criterion trips while faithfulness wobbles — coverage the generic set lacked).

**Q5. How do you write a rubric that judges consistently? What went wrong in your first draft?**

**Answer:** Anatomy: dimension definition + 1–5 scale with ANCHOR sentences per level (what a 2 vs 4 looks like
— anchors carry 90% of the consistency) + explicit edge rules ("citing the wrong chunk = max 2"). What went
wrong in v1 (quote YOURS): typical failure — unanchored scale ("rate tone 1–5") produced judge-vs-human
disagreement on the middle grades; fix was anchors + a worked example in the rubric. Validation loop from Evals
A applies per criterion: human-score 10 items, compute agreement, rewrite anchors till ≥8/10. A criterion that
can't reach agreement after two rewrites gets CUT (an unreliable gate is worse than no gate — it teaches the
team to ignore red). Your cut-or-kept list with reasons is a strong exhibit.

---

## Part 3: Red-Teaming — "Prove the gate bites"

**Q6. Walk me through your two sabotages. What did you break, what tripped, and with what margin?**

**Answer:** (Narrate YOUR table.) Sabotage 1 — weakened grounding prompt (drop "answer ONLY from context"):
faithfulness floor trips on paraphrase/multi cases (scores fell X→Y vs 0.75 floor — quote the margin; a 0.01
margin is a future flake, note if yours was thin and what you did). Sabotage 2 — poisoned corpus fact: the
"no-X"/faithfulness criterion trips on the poisoned-question cases (and NOTE which cases DIDN'T trip — poison
outside the tested questions is uncovered, honesty about coverage gaps). The mapping (sabotage → metric → case)
IS the gate's coverage proof — no mapping, no coverage claim. Both pushes went red in CI (screenshots/logs
linked), reverts went green. Close with: "a gate that never fired in anger is untested; ours fired twice on
purpose before it ever needed to fire for real."

**Q7. Your gate stayed green through a sabotage. Now what? (It happened — be honest about which one.)**

**Answer:** If every sabotage tripped first try, say which NEARLY didn't (thinnest margin) — same lesson.
Otherwise: diagnose the miss class. (a) WRONG INSTRUMENT: sabotage outside all rubrics (e.g. latency sabotage
vs quality-only gates — correctly out of scope; response is a NEW criterion or explicit scope note, not threshold
tweaking). (b) THRESHOLD TOO LOOSE: metric moved but stayed above floor (fix: tighten to noise-floor-aware level,
or add a delta threshold — your chunk-size-swap row likely lives here). (c) CASE GAP: no test question exercises
the sabotaged path (fix: add cases — the adversarial-set lesson from Guardrails, applied to evals). NEVER fix a
miss by blindly lowering thresholds globally — that manufactures flakes elsewhere. Your actual miss (or near-miss)
+ the layered fix is the best story in this file.

**Q8. Why must a missing secret FAIL loudly instead of skipping? What does the failure look like?**

**Answer:** Because a silently-skipped eval gate is a DISABLED gate that reports green — strictly worse than no
gate (false confidence). Real-world cause: secret expired/renamed, fork PRs without secret access, job
misconfiguration — all common, all invisible if the suite `pytest.skip`s. Your `conftest.py` policy: assert
secret presence at session start, ERROR with "LLM secret missing — eval gate cannot verify; failing closed"
(your break-run log quoted). CI nuance worth stating: fork PRs legitimately lack secrets — handle with an
explicit `pull_request_target` + approval flow or label-gated full runs, NOT silent skips; document YOUR choice.
Fail-closed everywhere: erroring safety/quality infra must block, never wave through (same principle as
Guardrails-A fail-closed — name the rhyme).

---

## Part 4: Flakiness & Cost — "The two gate-killers"

**Q9. Flakiness audit: what wobbled, why, and what's quarantined?**

**Answer:** (Quote YOUR 3-local + 2-CI runs.) Typical wobblers: thin-margin cases (score 0.76 vs 0.75 floor —
sampling variance flips them), judge-variance cases (same output, different judge run, ±0.06), model-drift cases
(CI judge version ≠ local). Dispositions, each documented: (a) LOOSEN with noise-floor justification (floor moved
0.75→0.70 because noise is ±0.06 — honesty, not laxity); (b) MORE SAMPLES per case (average of 3 — costs judge
calls, say how many); (c) QUARANTINE to advisory/non-blocking (runs + reports, doesn't block — with a re-promotion
rule, not exile). The quarantine LIST ships in-repo, reviewed like code. The principle: a flaky BLOCKING gate
gets disabled by annoyed engineers within a month — your flake protocol is what keeps the gate alive past week 3.
State your current quarantine count (zero is fine IF the audit supports it).

**Q10. What does the gate cost per run, and what tiering did that buy?**

**Answer:** (Quote YOUR math.) Judge calls per full run × price (or local GPU-minutes): e.g. 15 cases × 2 judge
metrics × $0.002 = $0.06/run local-model-equivalent — then monthly at YOUR push rate. Tiering decision it drove:
fast subset (deterministic recall@k + 5 core cases, every push — cheap, exact) vs FULL suite (nightly + PRs
touching app/corpus/prompts — path-filtered). If cheap enough to run full always, say so WITH the number
("full suite is $0.06, we run it unconditionally — tiering would save pennies and cost coverage"). Cost-per-push
is also the answer to "why not 500 cases": each case has marginal CI cost; your case count is budgeted, not
accidental. Sampling judges (not every output) and deterministic-first metrics are the cost controls — name both.

**Q11. Judge-swap row: you changed the judge model and re-ran. What happened, and what does it mean?**

**Answer:** (Quote YOUR result.) Expected: small systematic shift (scores move ±0.03–0.08 uniformly) with ranks
preserved (same cases trip, margins shift). Meaning: thresholds are judge-ANCHORED — a judge upgrade/drift moves
every gate simultaneously, so judge version is PINNED in the workflow and logged per run (your Phase 3
requirement), with re-validation (Evals-A 15-item check) on judge change. If the swap REORDERED results (different
cases trip), your thresholds are judge-OVERFITTED — recalibrate across both judges (min of the two, or
judge-specific thresholds — state your fix). This row is also the drift early-warning: scheduled judge-version
audits (monthly re-run of the validation subset) catch silent provider-side changes. "Our gates are valid for
judge X vY; changing judges re-opens validation" — versioned trust, stated plainly.

---

## Part 5: Policy & Handoff — "Gates are social systems"

**Q12. Read me your gate policy: what blocks, who updates baselines, flake protocol, cost — in 60 seconds.**

**Answer:** (This is a presentation question — rehearse from YOUR policy page.) Shape: "Federation: floors on
faithfulness + context recall block; precision + relevancy report advisory. Baselines re-pin ONLY via
`--update-baseline` runs linked to intentional-change PRs, reviewed by [owner]. Flakes: 2 strikes → quarantine,
weekly re-promotion review. Cost $X/run, full suite on app-touching PRs + nightly, fast subset otherwise.
Secret rotation: [your procedure]." Every clause traces to a measured artifact (thresholds.yml rationale,
quarantine list, cost row). The meta-point: gates ROT without ownership — thresholds drift, quarantines grow,
secrets expire. Your policy names an OWNER and a CADENCE (weekly green-review? monthly threshold audit?) —
without those the gate is a YAML file with an expiration date.

**Q13. How does this gate relate to Evals A's harness and LLMOps B's deploy gate? (Draw the chain.)**

**Answer:** One trust chain, three stages: EVALS A builds the instrument (golden set + validated metrics +
noise floors — the science); THIS gate enforces it pre-MERGE (same cases, blocking — the law); LLMOps B
enforces it pre-DEPLOY + canary (same thresholds, later moment + live alarms — the last line). Same
`golden.jsonl`, same `thresholds.yml` (imported, never forked — forks drift and gates rot silently). The interview
line: "measure once (A), block merges (B-evals), block deploys + watch prod (B-llmops) — one metric definition,
three enforcement moments." Breaking the chain anywhere named: unvalidated metrics → flaky gates → ignored red
→ eval-blind deploys. Your red-team PR + canary rollback (LLMOps B row 3) are the two ends demonstrated.

**Q14. When should a gate be ADVISORY (non-blocking) instead of blocking? Give me YOUR advisory list and why each.**

**Answer:** Blocking = high-signal, low-flake, fast, cheap (your floors on validated metrics). Advisory =
informative but unfit to block: high-variance experimental metrics (new criterion in probation — promote after
N green weeks), slow/expensive suites (full 100-case judge run — nightly advisory, subset blocks), known-flaky
cases (quarantine — visible, not gating, with re-promotion rule), informational signals (cost-per-push trend,
judge-disagreement monitor — review inputs, not verdicts). YOUR advisory list quoted with per-item rationale +
promotion criteria. The discipline: advisory is a WAITING ROOM with entry/exit rules, not a graveyard — every
advisory item has either a promotion plan or a deletion date. Teams that block on everything get disabled gates;
teams that advisory everything get ignored gates. Your split is the judgment call — defend it.

---

## How to Use These Questions

1. **Show the red** — red-team PR logs open while answering; green claims need red receipts.
2. **Quote policy, not just code** — thresholds with rationale, flake protocol, cost row, owner + cadence.
3. **Demo the loud fail** — secret-removed run and the quarantine list: 30-second narrations.
4. **Draw the chain** — A-harness → this gate → deploy gate + canary, one breath, shared files named.
