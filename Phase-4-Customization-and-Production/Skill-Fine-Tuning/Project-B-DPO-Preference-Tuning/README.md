# Project B — Preference Tuning with DPO

**Phase:** 4 — Customization & Production · **Skill:** Fine-Tuning · **Difficulty:** Intermediate–Advanced

Align an SFT model's behavior/style using **Direct Preference Optimization (DPO)** on a
chosen-vs-rejected preference dataset — on top of your Project A checkpoint. Extends *beyond*
roadmap.sh into alignment/post-training territory. **Same GPU tier as Project A (Colab T4 + Unsloth).**

SFT (Project A) taught capability: "do the task in this format." DPO teaches PREFERENCE: "of two valid
answers, THIS one" — safer, more helpful, better-styled. It also repairs the specific damage SFT can do:
narrow-domain training eroding the base model's refusal behavior (your Project A adversarial re-check —
if refusal dropped, this project is the fix, and that before/after is your headline result).

## Links to roadmap.sh/ai-engineer

- Fine-tuning (extended into alignment / preference optimization — beyond the roadmap node)
- Dataset Engineering — preference-pair construction (chosen vs rejected quality is everything)

## Concepts covered

RLHF pipeline intuition (SFT → reward model → PPO) vs DPO's collapse (no reward model, no RL),
preference data anatomy (prompt + chosen + rejected), DPO loss intuition (widen the chosen−rejected gap,
β-regularized against the reference), β tradeoff (align-hard vs stay-close), win-rate evaluation
(LLM-as-judge pairwise + human spot-check), reward hacking / over-optimization, safety-repair measurement.

## Prerequisites

- Fine-Tuning Project A DONE (SFT adapter checkpoint = DPO's starting policy AND reference model)
- HF `trl` `DPOTrainer` + Unsloth DPO support; same T4 GPU
- Phase 3 Evals A judge intuition (win-rate judging reuses it) + Guardrails A adversarial set (repair metric)

## Learning objectives

- Construct a preference dataset where the chosen−rejected gap isolates EXACTLY the behavior you want
- Run DPO on top of SFT and explain what the loss does in one paragraph (no hand-waving about β)
- Measure alignment via pairwise win-rate vs pre-DPO — plus refusal-rate repair if SFT regressed safety
- Diagnose DPO failure modes (noisy pairs, β mis-set, length bias) from training signals + samples

## How it works (the pipeline)

```
SFT checkpoint (Project A adapter) ──┬── policy model (TRAINED by DPO)
                                     └── reference model (FROZEN copy — the anchor)
                                              │
preference pairs: (prompt, chosen, rejected)  │
  │  build_pairs.py: curate + synthesize + audit (gap must isolate ONE behavior)
  ▼                                             ▼
DPOTrainer: per pair, push policy toward chosen, away from rejected,
  penalized by KL(policy || reference) × β  (drift too far → loss punishes)
  │
  ▼
dpo_adapters/ → eval: win-rate vs SFT on held-out pairs (judge-blind pairwise)
  + refusal-rate on adversarial set (repair check) + SFT-task metric (no capability regression)
  │  win? → merge → GGUF → ollama (same export path as Project A)
```

The β intuition to internalize: β is the leash length. High β = short leash (safe, weak alignment);
low β = long leash (strong alignment, risk of degeneration/reward hacking). Your β sweep makes this concrete.

## Setup

```bash
# Same Colab T4 as Project A; start FROM your SFT adapter
uv pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" transformers datasets trl

python -m dpo_tuning build-pairs --n 500 --audit 30
python -m dpo_tuning train --base-sft ../qlora-sft/adapters --beta 0.1
python -m dpo_tuning winrate --a ../qlora-sft/adapters --b ./dpo_adapters --judge qwen2.5:14b
```

| Knob | Default start | Meaning / what to try |
| ---- | ------------- | --------------------- |
| `β (beta)` | `0.1` | leash length — sweep 0.01 / 0.1 / 0.5 (experiment 2) |
| pair count | `300–1000` | fewer, cleaner pairs beat many noisy ones (prove it in experiment 3) |
| epochs | `1` | DPO overfits fast on small pair sets; held-out win-rate decides |
| judge | pinned model | your STRONGEST local tier (12–14B — root `MODELS.md`), version logged; judges have biases (Evals A lesson) |

## Project layout (files you will create)

```
dpo-preference-tuning/
├── requirements.txt
├── dpo_tuning/
│   ├── __init__.py
│   ├── build_pairs.py     curate/synthesize/audit (chosen−rejected gap isolation)
│   ├── train.py           DPOTrainer on SFT checkpoint (policy + frozen reference)
│   ├── winrate.py         blind pairwise judge: DPO vs SFT on held-out prompts
│   └── merge.py           merge → GGUF → Ollama (reuse Project A export)
├── data/
│   ├── pairs.jsonl        {prompt, chosen, rejected, behavior_tag, source}
│   └── audit_log.md       accept/reject per audited pair + reject reasons
├── evals/heldout_winrate.jsonl   prompts NEVER in pairs (contamination-checked)
└── README.md              this file + your measured tables
```

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Behavior target first (before any pairs)

- [ ] Name 1–3 target behaviors (e.g. "refuse disallowed requests crisply," "cite sources in briefs,"
  "terse over verbose"). Each gets a `behavior_tag` and 15 held-out win-rate prompts, locked now.
- [ ] If Project A showed refusal regression: that behavior is tag #1 and its repair is the headline metric.
- [ ] Verify: SFT model demonstrably exhibits the UNDESIRED variant on the held-out prompts (log specimens —
  DPO needs a gap to close; no gap, no project).

### Phase 1 — Preference-pair engineering (the project is won here, like SFT data)

- [ ] `build_pairs.py`: 300–1000 pairs where chosen−rejected differ in EXACTLY the tagged behavior
  (same facts, different safety/tone/format — a pair differing in everything teaches nothing).
- [ ] Sources: hand-write seeds → LLM-synthesize variants → AUDIT sample (reject noisy/ambiguous pairs;
  log rate + reasons — noisy labels are DPO's #1 failure mode, experiment 3 proves it).
- [ ] Contamination check: held-out win-rate prompts absent from pairs (same script discipline as Project A).
- [ ] Verify: 10 random pairs read aloud — a stranger agrees which is "chosen" without explanation. If not, rewrite.

### Phase 2 — Smoke DPO (tiny run, full loop)

- [ ] 50 pairs, β=0.1, 1 epoch: prove loop (trains → adapters → outputs shift toward chosen style on 5 probes).
- [ ] Verify: DPO loss decreases; spot-check 5 probes show movement (any movement — magnitude comes later).

### Phase 3 — Real DPO + β sweep (the core)

- [ ] Full pairs, β ∈ {0.01, 0.1, 0.5}, 1 epoch each; win-rate each vs SFT on locked held-out (blind pairwise,
  order-randomized — position bias is real, Evals A lesson).
- [ ] Read signals: loss ↓ + win-rate ↑ = aligning; loss ↓ + win-rate flat = pairs noisy or β too high;
  gibberish/degeneration samples = β too low (the leash lesson, observed not theorized).
- [ ] Verify: best-β checkpoint chosen by WIN-RATE, never train loss.

### Phase 4 — Repair + regression + export (the deliverables)

- [ ] Refusal-rate on Guardrails-A adversarial set: SFT vs DPO (repair quantified if SFT had regressed).
- [ ] Capability check: Project A held-out SFT metric re-scored on DPO model — must NOT regress
  (alignment tax documented if small; ship-blocker if large).
- [ ] Merge → GGUF → Ollama; fill tables below; write 1-page alignment report (behaviors, β choice, win-rates,
  repair delta, residual gaps).

---

## Core experiments (fill in YOUR numbers)

### 1. Win-rate + repair ← the core objective

| Metric | SFT (pre-DPO) | DPO (β=___) | delta |
| ------ | ------------- | ----------- | ----- |
| win-rate vs SFT on held-out (%, n=__) | 50 (baseline) |  |  |
| refusal rate on adversarial set % |  |  |  |
| SFT-task metric (capability check) % |  |  |  |
| quoted pair specimen (DPO wins — chosen behavior visible) | | | |

**What to look for:** win-rate clearly >50 (target 65–80 on tagged behaviors); refusal repaired without
capability collapse. Win-rate ≈50 with falling loss = pairs teach nothing (back to Phase 1, not more epochs).

### 2. β sweep (the leash, measured)

| β | DPO loss | win-rate % | sample quality note (quote 1 output) |
| - | -------- | ---------- | ------------------------------------ |
| 0.01 |        |            |                                      |
| 0.1 |         |            |                                      |
| 0.5 |         |            |                                      |

Expect: low β strongest alignment + first degeneration signs; high β safest + weakest. Your quotes make β concrete.

### 3. Pair-quality ablation (prove data > compute)

Train once on audited pairs, once on an equal-sized UNAUDITED (noisy) slice. Record win-rate both ways.
Expect audited ≫ noisy — the experiment that justifies every audit hour and mirrors Evals A's synthetic-audit lesson.

### 4. Break it deliberately

- Flip 20% of pairs (chosen↔rejected swapped) and train: watch win-rate invert/collapse (label-noise sensitivity,
  quantified — this is why audit exists).
- 5 epochs on 200 pairs: watch degeneration/reward-hacking specimens appear (repetitive safety preambles,
  length explosion — quote one; over-optimization made tangible).
- Judge-order bias check: score the same 20 matchups with A/B flipped; record flip rate (position bias in YOUR judge).

## Observations worth writing down as you go

1. **Gap isolation wins** — the pair rewrite where narrowing chosen−rejected to one behavior fixed training.
2. **β as leash** — your three-row sweep with quoted specimens; the setting you'd ship and why.
3. **Repair story** — SFT refusal number → DPO refusal number (or "no regression existed to repair," honestly).
4. **Noise sensitivity** — flipped-pair collapse number; the audit-rate justification.
5. **Alignment tax** — capability delta (ideally ~0; if negative, state it — taxes are real and reportable).

## Definition of done

- Locked held-out win-rate shows DPO beating SFT (table filled, judge + β logged, order-randomized).
- Refusal-rate measured (repaired if SFT regressed, else confirmed intact); SFT-task capability not regressed.
- Best-β justified by sweep table with quoted specimens; noisy-pair ablation run.
- Merged GGUF exported; alignment report written (behaviors, data, β, metrics, gaps).

## Reference material

- HF `trl` DPO docs + trainer: https://github.com/huggingface/trl
- DPO paper (Rafailov et al.): https://arxiv.org/abs/2305.18290
- Unsloth DPO notebooks: https://github.com/unslothai/unsloth

## Next

LLMOps next: the aligned model is what you INSTRUMENT (observability), SERVE, and GATE (CI/CD).
Your win-rate + refusal numbers become the deploy gate's thresholds — evals flow forward into operations.
