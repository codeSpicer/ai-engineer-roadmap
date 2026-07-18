# Project B — Preference Tuning with DPO

**Phase:** 4 — Customization & Production · **Skill:** Fine-Tuning · **Difficulty:** Intermediate

## Overview
Align an SFT model's behavior/style using **Direct Preference Optimization (DPO)** on a
chosen-vs-rejected preference dataset. Extends *beyond* roadmap.sh.

## Links to roadmap.sh/ai-engineer
- Fine-tuning (extended into alignment/preference optimization)
- Dataset Engineering — building preference pairs

## Concepts covered
Alignment/RLHF intuition, preference data (chosen vs rejected), DPO vs SFT,
win-rate evaluation.

## Prerequisites
- Fine-Tuning Project A (provides the SFT checkpoint)
- HF `trl` (DPOTrainer), same GPU tier

## Learning objectives
- Construct a preference dataset (chosen vs rejected pairs)
- Run DPO on top of an SFT model
- Measure behavior change via win-rate vs the base

## Suggested build steps
1. **Dataset engineering:** build/curate chosen-vs-rejected preference pairs.
2. Load the SFT checkpoint from Project A as the policy model.
3. Configure and run `DPOTrainer`.
4. Save the aligned model.
5. Evaluate helpfulness/safety win-rate vs the pre-DPO model.

## Reference material
- huggingface/trl (DPO): https://github.com/huggingface/trl
- Unsloth DPO notebooks: https://github.com/unslothai/unsloth

## Definition of done
- The DPO model shows a measurable win-rate improvement on the target behavior.
- You can explain how DPO differs from SFT.
