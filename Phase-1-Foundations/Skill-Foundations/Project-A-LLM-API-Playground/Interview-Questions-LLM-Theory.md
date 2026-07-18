# Interview Questions — Gap Topic: LLM Theory (conceptual, interviews)

Reading + written summary only — articulate, don't build. Complete the reading, then quiz.

## Gap Topic — LLM Fundamentals (Pairs with Foundations Project A)

**Q1. Explain self-attention in one paragraph, with the math intuition.**
Self-attention lets every token in a sequence relate to every other token in parallel.
Each token's embedding is projected into three vectors: a **Query (Q)**, **Key (K)**,
and **Value (V)**. For token i, its attention score against token j is the scaled dot
product Q_i · K_jᵀ divided by √d (d = head dimension, for stable gradients), passed
through softmax to get weights, then used to take a weighted sum of the V vectors. So
each token's output is a context-aware mixture of all tokens' values, weighted by how
relevant their keys are to its query. Multi-head attention runs this in parallel subspaces
to capture different relationship types (syntax, coreference, etc.).

**Q2. What is tokenization and vectorization, and how do they connect to attention?**
**Tokenization** converts raw text into discrete tokens (subwords) the model ingests.
**Vectorization** (embedding) maps each token (and positional info) into a dense vector
the attention math operates on. So: text → tokens → vectors → self-attention mixes those
vectors → richer representations. You can't attend over text; you attend over vectors.

**Q3. What is the difference between pre-training and post-training?**
- **Pre-training**: train on massive unlabeled text with a self-supervised objective
  (next-token prediction). This is where the model learns language, world knowledge, and
  reasoning patterns. Hugely expensive, done once by the lab.
- **Post-training**: adapt the pre-trained model to be useful/aligned: **SFT** (learn to
  follow instructions on curated demos), then **preference optimization** (RLHF/DPO) to
  match human preferences for helpfulness/safety. Cheaper, done on smaller curated data.

**Q4. Walk through the end-to-end LLM lifecycle.**
Data collection/cleaning → **pre-training** (foundation model) → **post-training**
(SFT + preference/RLHF) → **evaluation** (benchmarks, human evals) → **deployment**
(serving, optimization) → **monitoring/observability** (traces, cost, drift) → iterate
(retrain or fine-tune). Each stage has its own tooling, failure modes, and cost profile.

**Q5. What are the main failure modes an interviewer might probe?**
Hallucination (confident fabrication), bias (learned from data), brittleness to prompt
changes, context-window limits (lost long-range info), reasoning gaps on multi-step
tasks, and cost/latency at scale. Being able to name these *and* the mitigations
(RAG, evals, guardrails, fine-tuning) is the point of the reading.
