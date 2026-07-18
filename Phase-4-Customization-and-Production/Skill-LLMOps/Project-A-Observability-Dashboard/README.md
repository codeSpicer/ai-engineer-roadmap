# Project A — Observability + Cost Dashboard

**Phase:** 4 — Customization & Production · **Skill:** LLMOps · **Difficulty:** Intermediate

## Overview
Instrument an existing LLM app (your RAG or agent) with tracing, logging, and a
token/latency/cost dashboard using self-hosted Langfuse.

## Links to roadmap.sh/ai-engineer
- Production Architecture / Observability

## Concepts covered
Tracing/spans, token & cost tracking, latency, prompt versioning, baseline metrics.

## Prerequisites
- An existing app (RAG or agent) to instrument
- Docker + Docker Compose; Langfuse SDK

## Learning objectives
- Trace every LLM call including retrieval/agent steps
- Track cost and latency per request and establish a baseline
- Version and compare prompts

## Suggested build steps
1. Self-host Langfuse via Docker Compose.
2. Add the Langfuse SDK/callbacks to your app.
3. Log inputs, outputs, model, tokens, latency, and cost for every call.
4. Build a cost dashboard; record baseline cost/latency per request.
5. Version a prompt and compare metrics across versions.

## Reference material
- langfuse/langfuse: https://github.com/langfuse/langfuse

## Definition of done
- Every request is traced with cost + latency, and you know your baseline.
- Prompt versions are comparable in the dashboard.
