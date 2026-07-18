# Interview Questions — Fine-Tuning Project A: QLoRA Supervised Fine-Tune

Complete the project, then quiz yourself. Answers are detailed.

## Phase 4 — Customization & Production · Fine-Tuning · Project A

**Q1. What is LoRA and why is it parameter-efficient?**
LoRA (Low-Rank Adaptation) freezes the pre-trained weights and injects small
**trainable low-rank matrices** into each target layer (e.g. attention). Instead of
updating a full W (d×d), you learn A (d×r) and B (r×d) with r ≪ d. Trainable params drop
dramatically (often <1% of the model), so training needs far less memory and compute,
and you get a small **adapter** you can swap without touching the base model. Multiple
adapters can share one base.

**Q2. What is QLoRA and how does it let you fine-tune on limited VRAM?**
QLoRA = LoRA + **4-bit quantization** of the base model (NF4 / bitsandbytes). The frozen
base is loaded in 4-bit instead of 16-bit, cutting memory ~4×. Combined with LoRA's
tiny trainable adapters, you can fine-tune a 7B (even 13B/70B with care) model on a
single consumer GPU (e.g. Colab T4, 16GB). Dequantization happens on-the-fly during the
forward pass, so quality stays close to full-precision fine-tuning.

**Q3. What is SFT (Supervised Fine-Tuning)?**
SFT trains the model on a dataset of (instruction/context, desired response) pairs via
standard next-token prediction. It teaches the model a format, behavior, or domain
(e.g. "always answer as valid JSON," "respond in a support-agent voice," "know our
internal API schema"). It's the first post-training step — before any preference/alignment
tuning (DPO, Project B).

**Q4. What does the training loop look like (Unsloth + SFTTrainer)?**
1. Load a 4-bit base model with Unsloth `FastLanguageModel` (optimized kernels, less memory).
2. Attach LoRA adapters (rank, alpha, target modules).
3. Format the instruction dataset (prompt/response templates).
4. Configure `SFTTrainer` (learning rate, epochs, batch) and train; monitor loss curve.
5. Save the LoRA adapters (and optionally merge into a full model).

**Q5. Why merge adapters and export to GGUF?**
- **Merge**: combine base + LoRA weights into one standalone model so you don't need the
  adapter at inference (simpler serving, sometimes better kernel support).
- **GGUF**: a single-file format for efficient local inference (llama.cpp / Ollama).
  Exporting to GGUF lets your fine-tuned model run locally via Ollama — a deployable artifact.

**Q6. How do you prove the fine-tune actually helped (and how does this connect to Evals)?**
Compare base vs fine-tuned on held-out prompts using a consistent metric — ideally the
RAG Eval Harness (Phase 3) or a custom rubric: does the fine-tuned model follow the
format / domain better? "Measurably outperforms the base" is the definition of done.
This is where dataset engineering (curated/synthetic pairs) and evaluation meet — you
can't claim improvement without measuring it.
