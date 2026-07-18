# Interview Questions — Fine-Tuning Project B: Preference Tuning with DPO

Complete the project, then quiz yourself. Answers are detailed.

## Phase 4 — Customization & Production · Fine-Tuning · Project B

**Q1. What is DPO and how does it relate to RLHF?**
DPO (Direct Preference Optimization) aligns a model to human preferences by training
directly on **(chosen, rejected)** pairs using a classification-style loss — no separate
reward model and no RL loop.

Classic **RLHF** is a three-stage pipeline: (1) SFT, (2) train a reward model on human
preference comparisons, (3) optimize the policy against that reward with RL (PPO),
which is unstable and complex. **DPO collapses stages 2–3** into one supervised step:
it directly increases the likelihood of the chosen response and decreases the rejected
one, relative to the reference (SFT) model. Simpler, more stable, no reward-model
training.

**Q2. SFT vs DPO — when do you use each?**
- **SFT** (Project A) teaches *capability and format*: "here's how to do the task /
  structure the answer." It's about knowledge/behavior acquisition.
- **DPO** (Project B) teaches *preference/alignment*: "of two valid answers, this style
  / safety / tone is better." It refines an already-capable SFT model toward desired
  behavior.

You run DPO *on top of* an SFT checkpoint — it assumes the model can already do the task
and just needs to prefer the right variant.

**Q3. What is a preference dataset and how do you build one?**
A preference dataset is pairs of (prompt, chosen_response, rejected_response) where
"chosen" is the preferred behavior (helpful, safe, on-style) and "rejected" is the
undesired one. You build it by: curating human-labeled comparisons, or synthetically
generating both variants (e.g. a polite vs rude answer to the same prompt) and labeling
which is chosen. Quality of these pairs drives alignment quality — noisy labels produce
muddled behavior.

**Q4. How do you measure DPO success?**
**Win-rate**: have a judge (LLM-as-judge or human) compare the DPO model's outputs vs the
pre-DPO (SFT) model's on a held-out set of target behaviors (helpfulness, safety, tone).
If the DPO model wins more often, alignment improved. You can also track the DPO loss
converging and spot-check qualitative samples. The project's definition of done is a
*measurable* win-rate gain.

**Q5. Why is DPO considered "beyond roadmap.sh"?**
roadmap.sh's Fine-tuning node covers the basics (hosted fine-tuning, SFT-style
adaptation). DPO/preference optimization is alignment work that goes deeper into
post-training — our project extends the roadmap into RLHF-adjacent territory that senior
roles expect you to understand.

**Q6. What's the intuition behind the DPO loss?**
DPO maximizes the log-probability gap between chosen and rejected responses, but
**regularized** by how far the policy has drifted from the reference (SFT) model via a
β (beta) term. β controls the tradeoff: high β = stay close to the original (safe but
weak alignment), low β = align hard but risk degeneration. This implicit reward modeling
is why DPO needs no explicit reward model — the reference model *is* the baseline.
