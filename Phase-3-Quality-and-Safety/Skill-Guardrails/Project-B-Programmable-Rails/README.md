# Project B — Programmable Dialog / Safety Rails

**Phase:** 3 — Quality & Safety · **Skill:** Guardrails · **Difficulty:** Intermediate

## Overview
A guarded conversational bot using **programmable rails**: input, dialog, retrieval, and output rails
that prevent jailbreaks/off-topic drift and keep the bot on an approved path.

## Links to roadmap.sh/ai-engineer
- AI Safety & Ethics (programmable safety, conversational control)

## Concepts covered
Input/dialog/retrieval/output/execution rails, dialog flow control, Colang flows,
retrieval rails for RAG, on-topic enforcement.

## Prerequisites
- Guardrails Project A
- NeMo Guardrails, YAML (`config.yml`), Colang (`.co`) basics; a RAG pipeline to guard (optional)

## Learning objectives
- Configure the five rail categories in NeMo Guardrails
- Keep a bot on-topic and resistant to jailbreaks
- Add retrieval rails to filter/guard RAG context

## Suggested build steps
1. Create a `config.yml` declaring the model and a `.co` file with dialog flows.
2. Add input rails (jailbreak/off-topic checks) and output rails (response vetting).
3. Wrap the app with `LLMRails` and test the guarded conversation.
4. Add retrieval rails to guard a RAG pipeline's chunks.
5. Test adversarial prompts and confirm the bot stays on the approved path.

## Reference material
- NVIDIA-NeMo/Guardrails: https://github.com/NVIDIA-NeMo/Guardrails
- NeMo Guardrails docs: https://docs.nvidia.com/nemo/guardrails

## Definition of done
- The bot refuses off-topic/jailbreak attempts and follows the defined dialog flow.
- Retrieval rails filter unsafe/irrelevant context.
