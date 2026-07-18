# Project A — QLoRA Supervised Fine-Tune (with Dataset Engineering)

**Phase:** 4 — Customization & Production · **Skill:** Fine-Tuning · **Difficulty:** Intermediate

## Overview
Fine-tune a small (3B–7B) model to a domain/instruction dataset on a single GPU using
**QLoRA** (4-bit quantization + LoRA adapters), then merge and export.
Begins with a **Dataset Engineering** stage.

## Links to roadmap.sh/ai-engineer
- Fine-tuning (roadmap covers hosted fine-tuning; this goes deeper: local QLoRA)
- Dataset Engineering — folded into this skill

## Concepts covered
Dataset prep/formatting, PEFT/LoRA, 4-bit quantization, SFT training loop,
adapter merging, GGUF export for local inference.

## Prerequisites
- PyTorch basics; HF `transformers`/`datasets`/`peft`/`trl`; Unsloth
- A GPU (free Colab T4 works); a Hugging Face account

## Learning objectives
- Prepare and format an instruction dataset
- Run a QLoRA SFT job efficiently on limited VRAM
- Evaluate before/after and export a deployable model

## Suggested build steps
1. **Dataset engineering:** collect, clean, and format instruction data (prompt/response).
2. Load a 4-bit base model with Unsloth `FastLanguageModel`.
3. Attach LoRA adapters; configure `SFTTrainer`.
4. Train; monitor loss; save adapters and a merged model.
5. Compare base vs fine-tuned on held-out prompts; export to GGUF (Ollama).

## Reference material
- unslothai/unsloth: https://github.com/unslothai/unsloth
- leeroopedia/workflow-unslothai-unsloth-qlora-sft-finetuning: https://github.com/leeroopedia/workflow-unslothai-unsloth-qlora-sft-finetuning

## Definition of done
- The fine-tuned model measurably outperforms the base on your task.
- You have a merged/exported model that runs locally.
