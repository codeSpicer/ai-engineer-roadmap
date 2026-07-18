# Project A — LLM API Playground CLI

**Phase:** 1 — Foundations · **Skill:** Foundations · **Difficulty:** Beginner

## Overview
A command-line tool to talk to an LLM API and learn the raw mechanics before any frameworks.
You will send prompts, count tokens, control generation, and force structured output.

## Links to roadmap.sh/ai-engineer
- Introduction / LLM basics (inference vs training)
- OpenAI API: tokens, context window, pricing, max tokens
- Prompt Engineering: zero-shot, few-shot, chain-of-thought
- Structured / JSON output

## Concepts covered
Tokenization, context windows, temperature/top-p, system vs user messages,
token-based pricing, structured (JSON) output, prompt patterns.

## Prerequisites
- Python (functions, virtualenv, `pip`)
- An LLM API key **or** Ollama running locally

## Learning objectives
- Make a working chat completion call from scratch
- Count tokens and estimate cost per request
- Compare zero-shot vs few-shot vs chain-of-thought on the same task
- Force valid JSON output and parse it safely

## Suggested build steps
1. Set up a virtualenv and install the LLM SDK (OpenAI/Anthropic) or `ollama`.
2. Build a CLI that takes a prompt and prints the response.
3. Add a `--tokens` mode that prints input/output token counts and estimated cost.
4. Add `--temperature` / `--max-tokens` flags and observe behavior.
5. Add a `--json` mode that requests structured output and validates it.
6. Add saved prompt templates for zero-shot, few-shot, and chain-of-thought; compare results.

## Reference material
- OpenAI / Anthropic API docs
- Ollama: https://github.com/ollama/ollama

## Definition of done
- CLI runs against a real model, prints token counts + cost, and can emit validated JSON.
- You can explain why the same prompt gives different outputs and how to constrain it.

## Further reading — LLM theory (conceptual, interviews)

This project is hands-on with API mechanics. Interviewers will also probe conceptual
LLM fundamentals, so work through these as **reading + a written summary**, not code:

- **Attention & transformers** — self-attention, Q/K/V, multi-head attention, positional encodings.
- **Tokenization & vectorization** — how text becomes tokens/embeddings (you saw tokens in this project; go deeper on the math).
- **Pre-training vs post-training** — pre-training objectives, then SFT / instruction-tuning / RLHF / preference optimization.
- **End-to-end LLM lifecycle** — data → pre-train → post-train → eval → deploy → monitor.
- **Reference:** Karpathy's "Zero to Hero" / intro LLM videos (per JOB.md, already in progress).

Deliverable: a 1–2 page notes doc you can speak to fluently. Don't sink build-hours here —
the goal is being able to *articulate* the concepts, not implement them.
