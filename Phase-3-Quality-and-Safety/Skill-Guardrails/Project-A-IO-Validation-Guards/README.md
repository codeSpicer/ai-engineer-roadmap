# Project A — Input/Output Validation Guards

**Phase:** 3 — Quality & Safety · **Skill:** Guardrails · **Difficulty:** Intermediate

## Overview
Wrap an LLM endpoint with input and output **validators** — PII detection, toxic-language filtering,
competitor mentions, and format/regex enforcement — with reject/repair (fail) actions.

## Links to roadmap.sh/ai-engineer
- AI Safety & Ethics (prompt injection, bias, privacy) — hands-on enforcement

## Concepts covered
Input vs output validation, PII/toxicity detection, fail actions (reject/repair/reask),
structured-output enforcement.

## Prerequisites
- Foundations Project A
- `guardrails-ai` + Guardrails Hub validators; optionally FastAPI

## Learning objectives
- Intercept and validate both inputs and outputs of an LLM
- Apply multiple validators and choose appropriate fail actions
- Expose the guarded model as a REST service

## Suggested build steps
1. Install Guardrails AI and configure the Hub CLI.
2. Add input guards (e.g. PII, jailbreak/regex) and output guards (toxicity, competitor check).
3. Configure fail actions (exception vs repair vs reask).
4. Wrap an LLM call so unsafe inputs/outputs are blocked or repaired.
5. Expose it via FastAPI and test with adversarial inputs.

## Reference material
- guardrails-ai/guardrails: https://github.com/guardrails-ai/guardrails
- Guardrails Hub: https://guardrailsai.com/hub

## Definition of done
- Unsafe inputs/outputs are reliably blocked or repaired; safe ones pass through.
- Available as a REST endpoint.
