# Interview Questions — Gap Topic: LLM-as-Judge + Fine-tune vs Prompt vs RAG

Cheap add-on on top of Evals Project A. Pairs with Evals Project A. Quiz after building.

## Gap Topic — LLM-as-Judge & Tradeoff Framework (Pairs with Evals Project A)

**Q1. How would you build your own LLM judge from scratch?**
1. **Define a rubric**: the dimensions to score (faithfulness, relevancy, style, safety)
   with a scale and what each score means.
2. **Construct the judge prompt**: give the judge the input, the output under test, and
   the rubric; ask for a score + brief justification (chain-of-thought for calibration).
3. **Parse + score**: extract the numeric score (and optionally the rationale) reliably.
4. **Validate**: run your judge over a human-labeled subset and compute correlation
   (e.g. agreement with human ratings). If it disagrees systematically, fix the rubric
   or prompts.
5. **Compare** against off-the-shelf judges (Ragas/DeepEval) to find where they diverge
   and why — that gap is itself an interview talking point.

**Q2. What are the main risks of LLM-as-a-judge, and how do you mitigate them?**
- **Self-preference / verbosity bias**: judges favor longer, self-similar outputs. Mitigate
  with blind, rubric-locked scoring.
- **Position bias** (pairwise): prefer the first option. Mitigate by randomizing order.
- **Calibration drift**: scores not comparable across model versions. Mitigate by
  re-anchoring on a fixed validation set.
- **Cost/latency** at scale. Mitigate by judging samples, not every output.

**Q3. Build the fine-tune vs prompt vs RAG decision framework.**
- **Prompt engineering**: cheapest, zero training. Use when the behavior/knowledge
  *already exists* in the base model and you just need the right instruction/format.
- **RAG**: use when knowledge is **external, fresh, or proprietary** and changes often
  (docs, policies). Keeps the model static; updates happen in the document store.
- **Fine-tuning (SFT/DPO)**: use when **behavior/format/style must be baked in**, latency
  matters (no retrieval step), or prompting fails to elicit the pattern. Higher upfront
  cost (data + GPU) and slower to change than RAG.

**Q4. What are the tradeoffs you'd articulate in an interview?**
- **Cost**: prompting cheapest; RAG adds retrieval + possibly reranker cost; fine-tuning
  adds training + maintenance.
- **Latency**: fine-tuning can be fastest at inference (no retrieval); RAG adds round-trips.
- **Drift / maintenance**: RAG updates are instant (edit docs); fine-tuning needs retraining;
  prompting needs re-testing.
- **Data needs**: fine-tuning needs a quality dataset; RAG needs a corpus + chunking.
- **Eval surface**: each adds its own failure mode to monitor (prompt fragility, retrieval
  misses, adapter drift).

**Q5. Why is a "build your own LLM judge" a good interview talking point?**
It demonstrates you understand evaluation *as engineering*, not just calling an API — you
can design a rubric, handle judge bias, and validate against humans. It's low build cost
because you already have eval infra (Phase 3), and it shows end-to-end thinking about
quality, which senior roles probe.
