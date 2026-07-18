# Project B — Multi-Agent Supervisor System

**Phase:** 2 — Building AI Apps · **Skill:** Agents · **Difficulty:** Intermediate

## Overview
A supervisor agent that orchestrates specialized agents (e.g. planner, researcher, writer, critic)
to produce a deliverable, with shared state, handoffs, and human-in-the-loop gates.
Extends *beyond* roadmap.sh's single-agent coverage.

## Links to roadmap.sh/ai-engineer
- AI Agents node (extended)
- Extends beyond the roadmap into multi-agent orchestration

## Concepts covered
Orchestration, supervisor/swarm patterns, shared state, message passing,
graph-based stateful execution (LangGraph), checkpointing, human-in-the-loop.

## Prerequisites
- Agents Project A
- LangGraph basics (StateGraph, reducers), async Python basics

## Learning objectives
- Coordinate multiple specialized agents toward one goal
- Manage shared state across agents with checkpointing
- Insert a human approval gate before a critical step

## Suggested build steps
1. Define agent roles (planner, researcher, writer, critic) as nodes in a graph.
2. Build a supervisor that routes work and aggregates results.
3. Add shared state + checkpointing so runs can pause/resume.
4. Add a human-in-the-loop interrupt before finalizing output.
5. Run it end-to-end to produce a report; inspect the full trajectory.

## Reference material
- LangChain DeepAgents Playbook (Level 3.5, Supervisor/Swarm): https://github.com/sdivyanshu90/LangChain-DeepAgents-Playbook
- ashishpatel26/500-AI-Agents-Projects (LangGraph multi-agent): https://github.com/ashishpatel26/500-AI-Agents-Projects

## Definition of done
- The team produces a coherent multi-step deliverable with a working human-approval gate.
- Runs can pause and resume from a checkpoint.

## Related deep-dive — Context Engineering & Memory Systems

This project touches memory (shared state + checkpointing) but doesn't name it as a
first-class topic. Treat the following as a **standalone study piece** (cheap, no full
project) — it's a 2026 hiring buzzword and worth being explicit about:

- **Context engineering** — what to put in the prompt/window per step (not prompt *tweaking*,
  but *engineering* the right context: retrieval, compression, summarization, scratchpad).
- **Memory types** — short-term (in-context), working (scratchpad/state), long-term
  (vector store / KV / graph). When to use each; write-through vs read-through.
- **Memory architectures** — buffering, summarization-based compaction, semantic recall,
  self-editing memory (e.g. MemGPT-style).
- **Failure modes** — context overflow, stale memory, distraction, cost of over-long context.

Deliverable: a short written comparison of memory strategies and when you'd pick each,
plus a note on how this project's checkpointing maps to "long-term memory."
