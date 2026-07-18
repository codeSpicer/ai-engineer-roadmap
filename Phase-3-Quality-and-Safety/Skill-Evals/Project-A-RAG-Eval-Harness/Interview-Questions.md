# Interview Questions — Evals Project A: RAG Evaluation Harness (with Dataset Engineering)

Complete the project, then quiz yourself. Answers are detailed.

## Phase 3 — Quality & Safety · Evals · Project A

**Q1. Why do you need a golden evaluation dataset, and what's the role of synthetic generation?**
You can't improve what you can't measure. A **golden dataset** is a labeled set of
(inputs, expected/reference outputs) you score your system against — giving reproducible,
comparable numbers instead of "it feels better."

Curating ~50–100 real Q/A pairs is high quality but slow and limited in coverage.
**Synthetic generation** uses an LLM to produce extra (question, answer, context)
triples from your corpus, scaling coverage to edge cases (tricky phrasings, negative
questions) cheaply. The catch: synthetic data can inherit model biases, so you validate
a sample by hand. A good set has both curated (trustworthy) and synthetic (broad) cases.

**Q2. Define faithfulness, answer relevancy, context precision, and context recall.**
- **Faithfulness**: is the answer *supported by the retrieved context* (no hallucination)?
  Measures whether the model stuck to the sources.
- **Answer relevancy**: does the answer actually address the user's question (regardless
  of faithfulness)? A faithful but off-topic answer scores low here.
- **Context precision**: of the chunks retrieved, how many were actually relevant?
  (signal vs noise — did retrieval pull junk?)
- **Context recall**: of all the relevant chunks that *exist* in the corpus, what
  fraction did retrieval successfully find? (did retrieval miss key info?)

Together they separate retrieval problems (precision/recall) from generation problems
(faithfulness/relevancy) — essential for debugging.

**Q3. What is LLM-as-a-judge and what are its main risks?**
LLM-as-a-judge uses an LLM to score outputs against a rubric (e.g. rate faithfulness
1–5 with justification). It's cheap and scalable versus human labeling.

Risks: (1) **bias** — judges favor longer answers, self-preference, or verbatim matches;
(2) **position bias** — prefers the first option in pairwise comparison; (3) **cost/latency**
at scale; (4) **disagreement with humans** — must validate the judge against a
human-labeled subset (compute correlation) before trusting it. Mitigate with clear
rubrics, blinded ordering, and spot-checking.

**Q4. How do you compare two retrieval configs and pick a winner with evidence?**
Run both configs (e.g. hybrid on vs off) through the same golden dataset in Ragas/DeepEval,
produce scored tables per metric, and compare means/distributions. "Winner" = the config
that improves the metrics you care about (e.g. +faithfulness, +context recall) without
regressing others, and the improvement is statistically visible (not noise on 5 samples).
Export a comparison report/dashboard so the decision is auditable.

**Q5. What is dataset engineering and why is it "folded into" this skill?**
Dataset engineering = the work of collecting, cleaning, formatting, and generating
evaluation (and training) data. It's not a separate roadmap node but it underpins both
evals (this project) and fine-tuning (Phase 4). Here it's the front-loaded step: a RAG
eval is only as good as its golden set, so dataset quality comes first.

**Q6. Why Ragas/DeepEval rather than hand-rolled scoring?**
They implement the RAG metrics (faithfulness via entailment checks, context
precision/recall, etc.) with battle-tested LLM-judge prompts and aggregations. You could
hand-roll, but these libraries save time and give comparable, reproducible scores. The
project uses them as the engine while you focus on dataset quality and comparison design.
