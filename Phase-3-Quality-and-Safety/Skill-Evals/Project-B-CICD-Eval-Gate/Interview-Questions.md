# Interview Questions — Evals Project B: CI/CD Eval Gate

Complete the project, then quiz yourself. Answers are detailed.

## Phase 3 — Quality & Safety · Evals · Project B

**Q1. What does it mean to "treat evals as unit tests"?**
You wrap each evaluation case as a test assertion with a pass/fail threshold, just like
a unit test asserts `expected == actual`. Instead of "does the code return 4?", it's
"does the LLM output score ≥ 0.8 faithfulness?" The eval suite runs in a test runner
(pytest + deepeval) and fails the build when a threshold isn't met. This makes quality
a **hard gate**, not a quarterly afterthought.

**Q2. What is G-Eval / custom judge criteria?**
G-Eval is a framework for LLM-as-a-judge where you define a **rubric** (what "good"
means for your use case) and weighted **criteria**, then the judge model scores outputs
against it and produces a metric. Custom criteria let you go beyond generic faithfulness
— e.g. "tone is professional," "mentions refund policy," "no medical advice." You set
thresholds per criterion so regressions fail the test.

**Q3. How does a regression gate work in CI/CD?**
On every push/PR, GitHub Actions runs the eval suite. If any metric drops below its
threshold (a regression vs the baseline), the job exits non-zero → the run turns red and
blocks the merge/deploy. This catches quality degradation *before* it reaches
production, the same way a failing unit test blocks a bad code change. It shifts quality
from manual review to an automated, enforceable checkpoint.

**Q4. How do you store the LLM API key safely in CI?**
As an encrypted **CI secret** (GitHub repo → Settings → Secrets). The workflow reads it
as an environment variable at runtime; it's never committed to the repo or logged.
You verify a regression actually fails the job (not silently skips due to a missing key).

**Q5. How does this project reuse Phase 3 Evals A and Phase 4 LLMOps B?**
- Reuses **Evals A's** golden dataset and metric definitions as the test cases.
- Reuses the **eval gate concept** that **LLMOps B** deploys to Kubernetes — here it's
  the CI pipeline; there it's the deploy gate. Same principle (block on eval failure),
  different stage (pre-merge vs pre-deploy).

**Q6. Why is an eval gate more reliable than manual review for catching regressions?**
Manual review is sporadic, subjective, and easy to skip under deadline pressure. An
automated gate is **consistent, fast, and enforceable** — it runs on every change with
the same thresholds, and a red build is unambiguous. It also gives a historical trail:
you can see exactly when a metric regressed and which commit caused it.
