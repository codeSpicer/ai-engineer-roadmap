# Interview Questions — QLoRA Supervised Fine-Tune (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual runs and artifacts** — held-out tables, loss curves, dead-ends
log, VRAM numbers, GGUF demo. Quote the before/after table; that separates "ran a notebook" from
"shipped a tuned model."

---

## Part 1: Fundamentals — "What did you change, and why not prompt?"

**Q1. Why fine-tune at all? Your RAG pipeline + prompting worked — what forced weights to change?**

**Answer:** The tradeoff-framework answer (Evals-A add-on), instantiated: prompting failed on headroom grounds
(base scored X% on YOUR held-out format/task metric — the Phase 0 proof that the behavior ISN'T reliably in
the weights), and RAG solves KNOWLEDGE gaps, not BEHAVIOR gaps (retrieval can't make outputs consistently
schema-valid under prompt variation — your format-breaker specimens). Fine-tuning bakes the behavior IN:
consistent format without the retrieval step (latency win — YOUR per-request ms before/after), robust to prompt
rephrasing (no fragile instruction to regress), at the price of GPU hours + dataset labor + retraining-on-change.
The decision chain to recite: "knowledge-in-weights? (no → RAG veut dire behavior?) prompting elicits it?
(base failed at X% → tune) — each answer picked the tool, and the held-out table proves the pick."

**Q2. Walk me through the pipeline end to end, file by file, with what each file guarantees.**

**Answer:** `dataset.py` (collect→clean→dedupe→format→split + contamination check — guarantees: no held-out
leak (scripted), no PII, consistent chat template); `train.py` (Unsloth 4-bit load + LoRA attach + SFTTrainer,
response-only loss — guarantees: base untouched, adapters small, checkpoints per epoch); `loss_curves/` PNGs
(guarantee: every run's health visible — convergence, overfit, divergence all legible); `eval_sft.py`
(base-vs-adapter on LOCKED held-out + adversarial refusal re-check — guarantees: the claim + the safety watch);
`merge.py` (adapters→fp16→GGUF→Ollama — guarantees: runnable CPU artifact, reproducible from data+script).
Narrate one full pass with YOUR numbers (pairs count, epochs, best-ckpt selector = held-out score) — the files
are the answer's skeleton, the numbers its flesh.

**Q3. SFT loss: what is the model actually optimizing? Why "response-only"?**

**Answer:** Plain next-token cross-entropy — but MASKED to response tokens only (instruction tokens contribute
zero loss). Why: training on instructions teaches the model to PREDICT PROMPTS (generate new instructions
instead of answers — the failure you avoid by masking; template masking in `train.py` implements it). So SFT =
"given this instruction, the desired response's tokens should be likelier" — capability + format acquisition,
nothing about preferences (two valid responses both get likelihood mass — preference ranking is DPO's job,
Project B). Implication for data: response QUALITY is the entire signal (garbage responses trained confidently
= confident garbage generator — your audit reject reasons quoted). One line: "SFT teaches the shape of right;
DPO teaches the choice among rights."

---

## Part 2: LoRA & Quantization — "The efficiency stack"

**Q4. LoRA: explain the math intuition, then point at YOUR config and defend each choice.**

**Answer:** Freeze W (d×d); learn ΔW = BA with B (d×r), A (r×d), r≪d (yours: r=16) — trainable params ≈
2dr vs d² (for d=4096, r=16: ~0.8% of full — quote YOUR adapter MB vs base GB). Forward: h = Wx + (α/r)·BAx
(α=16 scales the adapter's voice — α/r ≈ 1 keeps updates sane). Why low-rank WORKS: fine-tune updates live in
a low-dimensional subspace (empirical finding — task adaptation needs direction tweaks, not full rewiring);
frozen base preserves pretraining, adapters swap per task (one base, MANY adapters — serving implication).
YOUR defenses: r=16 (sweep 8/32 showed [your delta] — capacity/quality point picked); targets (attention-only
vs all-linear ablation result quoted); α=r (standard stability — and what happened when you deviated, if you
did). The `r=4 vs 64` break-run row (eval delta vs adapter MB) is the exhibit that rank is a real knob with a
real price.

**Q5. QLoRA: what does 4-bit NF4 buy, what does it cost, and prove the tradeoff was worth it.**

**Answer:** BUYS: ~4× base-memory cut (7B fp16 ~14GB → NF4 ~4GB — YOUR `nvidia-smi` peak per config quoted),
which is what fits 7B-training on a 16GB T4 at all (full fine-tune needs ~28GB+ gradients/optimizer — datacenter
territory; without QLoRA this project doesn't exist on free hardware). COSTS: quantization noise in the frozen
base (forward-pass dequantize-then-compute is near-lossless empirically — "near" doing work: extreme-precision
tasks may feel it; your QLoRA-vs-full-LoRA note, or the honest "didn't test full precision, here's why the
literature says the gap is small + our held-out says quality sufficed"). Paged optimizers + Unsloth kernels
stack further (memory spikes handled without OOM — your smoke-run VRAM log). Worth-it proof: best-ckpt held-out
(table Q14) achieved ON a T4 for $0 — democratized fine-tuning isn't a slogan here, it's your receipts. Also
state the ceiling: 70B-QLoRA on T4 is still no (adapter+optimizer+activations overflow — know YOUR tier's limit).

**Q6. Unsloth + SFTTrainer: what does each contribute that raw PyTorch wouldn't?**

**Answer:** Unsloth: hand-optimized Triton kernels for the LoRA+quantized forward/backward (less VRAM, ~2×
faster on T4-class — your smoke-run time vs stock-PEFT estimate if measured, else the documented factor with
your observed step-time), plus one-line 4-bit load (`FastLanguageModel.from_pretrained`) that wires
quantization+LoRA compatibly (the footgun it removes: mismatched quant/adapter dtypes silently degrading —
name it). SFTTrainer (trl): response-masking, chat-template application, packing, checkpointing, eval hooks —
the training HYGIENE (`train.py` config: lr, epochs, batch, gradient accumulation for T4-sized batches). Raw
PyTorch would reimplement all of it buggily (masking off-by-ones, template mismatches that poison training —
your format-consistency audit exists because template mismatch is a silent killer). Knowing what the framework
guarantees (masking, template) vs what YOU guarantee (data quality, held-out honesty, curve reading) is the
senior split — state it.

---

## Part 3: Data & Training Discipline — "Where projects live or die"

**Q7. Dataset engineering for SFT: what did you do beyond "collect JSONL," and which step moved held-out most?**

**Answer:** Beyond collecting: CLEAN (boilerplate strip, whitespace normalize — Phase-1 cleaning lesson; quote
the decision), DEDUPE (exact + near-dup — duplicates overweight quirks AND leak across splits), FORMAT (single
instruction template WITH the base's chat template — mismatch = silent poisoning, verified by printing
tokenized samples), SPLIT (train/held-out with scripted contamination check), AUDIT (sample review, nonzero
reject rate with reasons — your Evals-A method reused). Which moved held-out most (quote YOUR delta — usually a
cleaning/dedupe/format fix beats any hyperparameter): e.g. "template fix +0.09, lr sweep ±0.02." The moral you
state: SFT is dataset distillation into weights — data quality IS the hyperparameter. Your 10 printed train
pairs (correct, consistent, PII-free) are the live exhibit; walk them.

**Q8. Read me two of your loss curves: one healthy, one sick, with diagnosis and action.**

**Answer:** (Open `loss_curves/`.) HEALTHY: train ↓ smoothly, held-out ↑ then plateau — action: stop at plateau
(best-ckpt = held-out peak, never train-loss minimum — your selection rule). SICK (pick YOURS): overfit
(train→0, held-out collapses — your 10-epoch/200-pair induced run: quote both curves; action: fewer epochs/more
data/lower lr); divergence (spike/NaN epoch 1 — your lr-1e-3 dead-end: action lr÷3–5, re-run; cause: step size
exploding low-precision updates); flatline (nothing moves — lr too low, or masking bug training on nothing —
diagnose by checking response-token loss ≠ 0). The dead-ends table (≥2 rescued failures with causes) is REQUIRED
evidence, not bonus — "clean first try" teaches nothing and convinces nobody. Curve literacy in one line:
"train loss measures fitting, held-out measures learning — ship the learner, not the fitter."

**Q9. Contamination: how did you guarantee held-out honesty, and what did the leak demo show?**

**Answer:** Guarantee: scripted near-dup scan (`difflib` threshold) between held-out and train + audit samples,
logged, in-repo, re-run per data change (not a one-time ceremony). Leak demo: 5 held-out prompts into train →
metric inflated +X (YOUR number — the price of dishonesty, quantified). Why it matters beyond ethics: leaked
held-out selects the checkpoint that MEMORIZES, not generalizes (best-ckpt-by-leaked-score ships the memorizer —
production pays). Same script guards DPO win-rate prompts and Evals-A golden (one discipline, three consumers —
name the chain). Interview closer: "our +0.XX survives the contamination script — run it yourself" (point at the
file). Skepticism about fine-tune claims is rational; your answer is executable.

---

## Part 4: Results & Safety — "Prove it helped, prove it didn't harm"

**Q10. Narrate your before/after table. What jumped, what didn't, and what's the headline?**

**Answer:** (Walk YOUR table.) Expected: FORMAT compliance jumps hardest (SFT's superpower — schema-validity
X%→Y%, quote the failure fixed verbatim); TASK accuracy rises (Z%→W% — real but smaller; capability was partly
present); headline = the quoted failure-fixed specimen (base's broken output vs tuned output side by side).
What DIDN'T move (name it — some capability metric flat because base already had it; flatness with headroom
analysis beats hiding). Refusal row: intact (or "regressed R%→S% — flagged, routed to DPO repair" — the honest
branch that MAKES Project B necessary, not optional). Metric-naming discipline: accuracy vs compliance vs refusal
are THREE claims with THREE numbers — conflating them ("model got better") is amateur; your split is the
professionalism.

**Q11. Refusal regression: did SFT erode safety tuning? How did you check, and what was the verdict?**

**Answer:** Check: Guardrails-A adversarial set re-run on base vs fine-tuned (SAME set — comparability), refusal
rate both columns (YOUR numbers). Mechanism if regressed: narrow-domain SFT shifts the output distribution toward
compliance-with-task; refusal behavior (learned in post-training) gets partially overwritten — catastrophic
forgetting's safety face (name it). Verdict branches: INTACT ("no regression — narrow data didn't touch refusal
manifolds; DPO still pursued for style/helpfulness, not repair" — valid); REGRESSED ("R%→S% — ship-blocker
declared, DPO repair prioritized as tag #1 with THESE specimens" — the ASEPTIC handoff to Project B). Either
verdict needs the numbers + 2 quoted specimens (a preserved refusal AND the riskiest near-miss). The principle:
every capability tune ships with a safety re-check, or safety is a rumor. Your re-check row is the proof it isn't.

**Q12. Overfitting on purpose: what did the 10-epoch/200-pair run teach that healthy training couldn't?**

**Answer:** (Quote both curves + a degeneration specimen.) Train loss → ~0 (perfect memorization); held-out
collapses (memorizer, not learner); outputs turn brittle (verbatim train phrases on near-miss prompts — quote
one; generalization replaced by retrieval-from-weights). Lessons only inducible-runs teach: (1) MORE TRAINING ≠
BETTER is visceral after watching your own curves cross; (2) the crossing POINT is data-size-dependent (200 pairs
cross at epoch ~3, full data never crossed in 3 epochs — scale buys headroom, stated with YOUR numbers);
(3) early-stopping needs HELD-OUT cadence (per-epoch scoring caught it — train-loss-only monitoring would have
shipped epoch 10). This run is also your "why Phase 3 exists" story: without held-out discipline, the memorizer
ships with a great train loss and a smile. Keep the PNGs — they're the most educational artifacts in the repo.

---

## Part 5: Artifacts & Scope — "Shippable, reproducible, bounded"

**Q13. Merge + GGUF + Ollama: what did each step do, and why does the artifact matter?**

**Answer:** MERGE: adapters (BA) folded into base weights (W + (α/r)BA → single fp16 model — no adapter runtime
needed; simpler serving, wider kernel support). GGUF QUANTIZE: fp16 → quantized single file (CPU-efficient
inference format — llama.cpp/Ollama native; size noted, e.g. Q4 ~4GB for 7B). OLLAMA: `create` + `run` —
YOUR model answering on CPU, no GPU (the democratization receipt: trained on borrowed T4, runs on laptop).
Reproducibility: data/ + train.py + pinned base hash → anyone rebuilds (state what you pinned; unpinned base
version = unreproducible tune). PEFT-vs-merged check (your parity note — same quality, simpler deploy). The
artifact isn't a souvenir — it's the deployable that LLMOps-B serves (the phase chain made concrete: tune →
export → serve → gate).

**Q14. Catastrophic forgetting probe: what base strength did you test, and what happened?**

**Answer:** (YOUR probe.) Design: pick a capability FAR from training (e.g. JSON-extractor tune → test creative
writing / multilingual / reasoning the base was good at — ideally a base strength you logged pre-tune).
Outcomes: INTACT (narrow SFT preserved it — common at low epochs/small r; state yours), DEGRADED (tune narrowed
the model — quote the degradation specimen; mitigation = replay data (mix base-domain samples into train) or
smaller r/fewer epochs — state which you'd try), or IMPROVED (rare, report honestly if so). Why it matters for
deploy: fine-tunes NARROW competence (your far-task probe: graceful degradation vs confident garbage — quote the
behavior); serving a narrowed model to general traffic needs routing (tuned model for its task, base for the
rest — the deployment implication, stated). Forgetting isn't a footnote — it's the tax line next to DPO's
alignment tax (name both taxes together in the capstone).

**Q15. When would you NOT fine-tune? (Talk yourself out of your own project.)**

**Answer:** (The tradeoff-framework answer with YOUR numbers.) Don't tune when: base already does it (no
headroom — your Phase 0 would have shown high scores; tune = expensive no-op); knowledge is fresh/fast-changing
(docs update weekly → RAG; retraining per doc-edit is absurd — quote YOUR retrain cost vs RAG re-index cost);
task needs reasoning the base lacks (SFT teaches format, not IQ — your far-task probe bounds the claim);
data < ~500 auditable pairs (noise-tuning — your pair-quality ablation's lesson pre-applied); latency allows
retrieval (RAG's ms are cheaper than GPU-hours when freshness matters). The honest close: "we tuned BECAUSE
[headroom proof + stability need + latency win], and here's the cheat-sheet row where we'd choose otherwise."
Recommending against your own technique on its merits is the strongest senior signal in this file.

---

## How to Use These Questions

1. **Open the curves** — healthy + sick PNGs visible; diagnose live, point at epochs.
2. **Quote the table** — before/after + refusal + dead-ends: numbers, specimens, verdicts.
3. **Demo the artifact** — `ollama run` your GGUF live: the tune answering on CPU.
4. **Name the taxes** — forgetting probe + refusal check + contamination script: bounded claims, executable proofs.
