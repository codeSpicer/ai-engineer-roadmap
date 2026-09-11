# Project A — QLoRA Supervised Fine-Tune (with Dataset Engineering)

**Phase:** 4 — Customization & Production · **Skill:** Fine-Tuning · **Difficulty:** Intermediate–Advanced

Fine-tune a small (3B–7B) model to a domain/instruction dataset on a single GPU using
**QLoRA** (4-bit quantization + LoRA adapters), then merge and export to GGUF for local inference.
Begins with a **Dataset Engineering** stage — the same discipline as Evals A, now producing training
data instead of test data. **Needs a GPU: free Colab T4 works; Unsloth for memory-efficient training.**

Everything before this changed the model's INPUTS (prompts, retrieval, guards). Fine-tuning changes the
MODEL: behavior baked into weights, no retrieval step at inference, format compliance that survives
prompt variation. The price is GPU time, dataset labor, and a new failure class (overfitting, catastrophic
forgetting, eval-gaming) that only Phase 3 measurement can see — which is why the project ends with a
before/after scored on YOUR eval harness, not vibes.

## Links to roadmap.sh/ai-engineer

- Fine-tuning (roadmap covers hosted fine-tuning; this goes deeper: local QLoRA on your own GPU)
- Dataset Engineering — folded into this skill (training-data twin of Evals A's test-data work)

## Concepts covered

Instruction-dataset design (prompt/response pairs, coverage, dedup, contamination), chat templating,
quantization (4-bit NF4: what 4× memory savings cost in precision), LoRA (rank/alpha/target-modules,
why <1% trainable params works), SFT loss (plain next-token prediction on responses only), training
hygiene (lr, epochs, early stopping, loss-curve reading), overfitting vs underfitting on small data,
adapter merging, GGUF export (quantized inference formats), before/after eval discipline.

## Prerequisites

- PyTorch basics; HF `transformers` / `datasets` / `peft` / `trl`; Unsloth (`FastLanguageModel`)
- A GPU — Colab T4 free tier suffices for 3B–7B + QLoRA (CPU training is not viable; state this constraint)
- A Hugging Face account (model + dataset pull/push); Phase 3 Evals A harness for the final comparison

## Learning objectives

- Prepare, clean, and format an instruction dataset (and explain every cleaning choice)
- Run a QLoRA SFT job to convergence on limited VRAM without OOM or silent divergence
- Read a loss curve and catch overfitting before it ships
- Prove the fine-tune helped with a held-out before/after scored on eval tooling, and export a runnable artifact

## How it works (the pipeline)

```
raw task data (your domain: support answers, JSON extractors, style examples…)
  │  dataset.py: collect → clean → dedupe → format (Alpaca/instruction template)
  │              → split train / held-out (contamination check: held-out never in train)
  ▼
train.jsonl / heldout.jsonl  [{instruction, input?, output}]
  │  train.py: Unsloth FastLanguageModel.from_pretrained(4-bit) + LoRA attach (r=16, α=16, targets)
  │            + SFTTrainer (response-only loss via template masking)
  ▼
adapters/  (small: tens of MB — the ONLY trained artifact; base untouched)
  │  loss curve → converge? overfit? → early-stop / adjust
  ▼
eval: base vs adapter on held-out (YOUR Evals-A-style rubric: format compliance, task accuracy)
  │  win? → merge.py: base + adapters → full fp16 → quantize → model.gguf → ollama run
  ▼
local fine-tuned model answering in YOUR format, no retrieval step
```

Adapter math that matters: full 7B fine-tune ≈ 28GB gradients+optimizer (needs datacenter);
QLoRA 7B ≈ fits 16GB T4 (4-bit base ~4GB + adapters + paged optimizer). That gap is the project.

## Setup

```bash
# Colab T4 (free): Runtime → Change runtime → T4 GPU
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" transformers datasets peft trl

# Local inference of the RESULT needs only Ollama (no GPU):
ollama create my-sft -f Modelfile.gguf
ollama run my-sft "extract JSON: John is 34"
```

| Knob | Default start | Meaning / what to try |
| ---- | ------------- | --------------------- |
| LoRA `r` / `alpha` | `16 / 16` | adapter capacity; sweep 8 vs 32, record eval delta |
| target modules | `q,k,v,o (+ gate/up/down)` | which layers adapt; attention-only vs all-linear ablation |
| learning rate | `2e-4` | most common divergence cause — too high explodes, too low flatlines |
| epochs | `1–3` | small data overfits fast; held-out curve decides, not habit |
| 4-bit quant | `NF4` | base precision; QLoRA-vs-LoRA quality note in observations |
| held-out split | `10–20%` | the ONLY honest scoreboard; never train on it |

## Project layout (files you will create)

```
qlora-sft/
├── requirements.txt
├── dataset.py            collect/clean/dedupe/format + train/held-out split + contamination check
├── train.py              Unsloth 4-bit load + LoRA attach + SFTTrainer + checkpointing
├── loss_curves/          train/loss pngs per run (commit them — they're evidence)
├── eval_sft.py           base-vs-adapter on held-out with format/task rubric
├── merge.py              merge adapters → fp16 → GGUF export (+ Modelfile)
├── data/
│   ├── train.jsonl       formatted training pairs
│   └── heldout.jsonl     NEVER-trained-on evaluation pairs
└── README.md             this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Task + metric first (before touching data)

- [ ] Define the target behavior in one sentence + its PASS metric on held-out prompts
  (e.g. "valid JSON matching schema X on 50 extraction prompts" — format compliance % + field accuracy %).
- [ ] Collect 20 held-out prompts NOW, lock them (`heldout.jsonl`), never train on them.
- [ ] Verify: BASE model scores poorly on the metric (headroom proven — fine-tuning a task the base aces teaches nothing).

### Phase 1 — Dataset engineering (the project is won or lost here)

- [ ] `dataset.py`: gather 500–5k pairs (curate + synthesize with an LLM + hand-audit a sample, Evals A method);
  clean (strip boilerplate, normalize whitespace — Phase 1 cleaning lesson returns), dedupe (exact + near-dup),
  format into instruction template with the SAME chat template the base expects.
- [ ] Contamination check: no held-out prompt (or near-duplicate) in train — script it (`difflib` threshold),
  log the check. A leaked held-out invalidates every later claim.
- [ ] Verify: print 10 random train pairs; each has correct output, consistent format, no PII/secrets;
  audit reject rate logged (nonzero, with reasons).

### Phase 2 — Smoke train (tiny run, full loop, before the real job)

- [ ] 50-pair subset, 1 epoch, `r=8`: prove the loop works end-to-end (trains → saves adapters → loads →
  answers differently). Watch VRAM (`nvidia-smi` — record peak; OOM here means config, not hardware).
- [ ] Verify: loss decreases monotonically-ish; adapter loads and changes outputs (any change — quality comes later).

### Phase 3 — Real SFT + loss-curve discipline (the core)

- [ ] Full data, `r=16`, lr `2e-4`, 2–3 epochs with per-epoch held-out scoring (NOT just train loss).
- [ ] Read curves like an engineer: train loss ↓ + held-out ↑ = learning; train ↓ + held-out ↓ = overfitting
  (stop, cut epochs / grow data / lower lr); loss NaN/spike = lr too high or bad batch (drop lr 3×, re-run).
- [ ] Commit `loss_curves/` PNGs per run with config in the filename. Failed runs stay in the log with causes —
  the dead-ends table below is required, not optional.
- [ ] Verify: best checkpoint chosen by HELD-OUT score, never train loss.

### Phase 4 — Merge, export, re-attack (the deliverables)

- [ ] `merge.py`: merge adapters → fp16 → GGUF quantize → `ollama create` → run locally, no GPU needed.
- [ ] Before/after on locked held-out: base vs fine-tuned, same rubric — fill the table below.
- [ ] Safety re-check: run YOUR Phase 3 adversarial set against the fine-tuned model — alignment/refusal
  behavior must not have REGRESSED (fine-tuning on narrow data can erode safety tuning; a refusal-rate drop
  is a ship-blocker — FT-B's DPO exists partly to repair exactly this).
- [ ] Verify: GGUF runs on CPU via Ollama; someone else can reproduce from your `data/` + `train.py` alone.

---

## Core experiments (fill in YOUR numbers)

### 1. Before/after on locked held-out ← the core objective

| Metric (held-out, n=__) | base model | fine-tuned (best ckpt) | delta |
| ----------------------- | ---------- | ---------------------- | ----- |
| task accuracy % |            |                        |       |
| format compliance % |        |                        |       |
| refusal rate on adversarial set % | |                       |       |
| qualitative note (1 failure fixed, quoted) | |               |       |

**What to look for:** format compliance should jump hard (SFT's superpower); task accuracy should rise
without held-out gaming (contamination check is what makes this believable); refusal rate must NOT drop —
a drop ships a safety regression and flips the project to "needs DPO repair" (say so explicitly).

### 2. Dead-ends log (required — failed runs are curriculum)

| Run (config) | symptom (loss curve / OOM / garbage) | diagnosis | fix attempted + result |
| ------------ | ------------------------------------ | --------- | ---------------------- |
| e.g. lr 1e-3 | loss spike epoch 1 | lr too high | 2e-4 → smooth converge |
|              |                                      |           |                        |

Minimum 2 dead-ends documented. A clean first-try train teaches less than one rescued divergence.

### 3. Break it deliberately

- Train 10 epochs on 200 pairs: watch held-out collapse while train loss → 0 (overfitting, induced on purpose —
  quote both curves; this is the "more training ≠ better" demo).
- Leak 5 held-out prompts into train, re-score: watch the metric inflate (contamination effect quantified —
  then DELETE the leak and re-run honestly).
- `r=4` vs `r=64` on the same data: record eval delta vs adapter size (capacity/quality tradeoff in numbers).
- Prompt the fine-tuned model with a task FAR outside training: confirm graceful degradation or honest failure
  (fine-tunes narrow competence — catastrophic forgetting probe: test one BASE strength the data never covered).

### 4. Extend it (springboard to Project B)

- Collect 20 cases where the SFT model is CORRECT-but-ugly vs ideal-style (tone/format preferences) — these
  become Project B's first preference pairs.
- Try inference WITHOUT merging (PEFT adapter loading) vs merged GGUF: latency/quality parity check.

## Observations worth writing down as you go

1. **Dataset > hyperparameters** — the cleaning/dedupe decision that moved held-out most (quote the delta).
2. **Loss-curve literacy** — your overfit/divergence specimens with PNGs; what each shape meant.
3. **Contamination paranoia** — the leak experiment's inflation number; why the check script stays in repo.
4. **Refusal-rate watch** — fine-tune's safety side effect, measured not assumed.
5. **VRAM accounting** — peak GB per config; what actually OOMs a T4 (batch × seq-len × r, in your numbers).

## Definition of done

- Locked held-out set (contamination-checked) on which fine-tuned measurably beats base (table filled).
- Merged GGUF artifact running locally via Ollama; reproduction from `data/` + `train.py` possible.
- Dead-ends log with ≥2 rescued failures + loss-curve PNGs committed.
- Adversarial re-check shows no refusal regression (or regression flagged + routed to DPO).

## Reference material

- Unsloth: https://github.com/unslothai/unsloth · QLoRA notebooks therein
- leeroopedia QLoRA workflow: https://github.com/leeroopedia/workflow-unslothai-unsloth-qlora-sft-finetuning
- HF `trl` SFTTrainer docs: https://huggingface.co/docs/trl

## Next

Project B aligns the SFT model's preferences (DPO) — including repairing any refusal regression found above.
Keep the checkpoint + held-out set: DPO trains ON TOP of this adapter and evals on the SAME held-out plus win-rate.
