# Project A — RAG Evaluation Harness (with Dataset Engineering)

**Phase:** 3 — Quality & Safety · **Skill:** Evals · **Difficulty:** Intermediate

## Overview
A dataset-first evaluation harness that scores a RAG system on RAG-specific metrics and
compares retrieval configurations. Front-loaded with a **Dataset Engineering** stage:
curating and synthetically generating a golden test set.

## Links to roadmap.sh/ai-engineer
- Evaluation (RAG metrics, LLM-as-a-judge)
- Dataset Engineering — folded into this skill

## Concepts covered
Golden datasets, synthetic test-case generation, faithfulness, answer relevancy,
context precision/recall, LLM-as-a-judge, comparing configs.

## Prerequisites
- RAG Project A (the system under test)
- `pandas`, Ragas (or DeepEval), an LLM for the judge

## Learning objectives
- Build a labeled evaluation dataset (curated + synthetic)
- Score a RAG pipeline on faithfulness / relevancy / context precision & recall
- Compare two retrieval configs and pick a winner with evidence

## Suggested build steps
1. **Dataset engineering:** curate ~50–100 Q/A pairs; generate extra cases synthetically from your corpus.
2. Wire the dataset into Ragas (or DeepEval) with RAG metrics.
3. Score your RAG Project A pipeline; export a scored table.
4. Change a retrieval setting (e.g. hybrid on/off) and re-score.
5. Produce a comparison report / simple dashboard.

## Reference material
- Ragas: https://github.com/explodinggradients/ragas
- VickyGuo0907/ai_evaluation_project: https://github.com/VickyGuo0907/ai_evaluation_project

## Definition of done
- You can quantify which RAG config is better and by how much, backed by a golden set.
- The dataset includes both curated and synthetic cases.

## Related — Build your own LLM Judge + tradeoff framework

Cheap add-on using the eval infra above (good interview talking point, low build cost):

- **LLM-as-Judge from scratch** — write a small judge script: define rubric (faithfulness,
  relevancy, style), prompt the judge model, parse + score. Compare against Ragas/DeepEval
  to see where off-the-shelf judges disagree with yours and why.
- **Tradeoff framework: fine-tune vs prompt vs RAG** — a decision doc, not code:
  - *Prompt engineering* — cheapest, fastest; use when the knowledge/behavior already exists in the base model.
  - *RAG* — use when knowledge is external, fresh, or proprietary and changes often.
  - *Fine-tuning* — use when behavior/format/style must be baked in, latency matters, or the task resists prompting.
  - Tradeoffs: cost, latency, drift, maintenance, data needs, eval surface.

Deliverable: a judge script in this project's repo + a one-page tradeoff cheat-sheet.
