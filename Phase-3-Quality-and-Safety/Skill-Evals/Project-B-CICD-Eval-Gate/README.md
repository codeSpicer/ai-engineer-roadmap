# Project B — CI/CD Eval Gate

**Phase:** 3 — Quality & Safety · **Skill:** Evals · **Difficulty:** Intermediate

## Overview
Treat evaluations as unit tests: define pass/fail thresholds with custom LLM-as-judge criteria
and **block a build in GitHub Actions** when quality regresses.

## Links to roadmap.sh/ai-engineer
- Evaluation (regression testing, CI-native evals)
- Production Architecture (release safety)

## Concepts covered
Evals as pytest tests, G-Eval / custom judge criteria, thresholds, regression gating, CI/CD.

## Prerequisites
- Evals Project A (or any app/agent to test)
- `deepeval`, `pytest`, Git + GitHub, GitHub Actions YAML basics

## Learning objectives
- Wrap eval cases as pytest tests with thresholds
- Define custom G-Eval criteria for your use case
- Fail a CI pipeline automatically on regression

## Suggested build steps
1. Write `deepeval` test cases (assertions) over your app's outputs.
2. Add G-Eval / custom-criteria metrics with thresholds.
3. Run `deepeval test run` locally and confirm pass/fail behavior.
4. Add a GitHub Actions workflow that runs the suite on every push.
5. Store the LLM key as a CI secret; verify a regression fails the job.

## Reference material
- confident-ai/deepeval: https://github.com/confident-ai/deepeval

## Definition of done
- A quality regression turns the GitHub Actions run red automatically.
- Thresholds and criteria are documented in the repo.
