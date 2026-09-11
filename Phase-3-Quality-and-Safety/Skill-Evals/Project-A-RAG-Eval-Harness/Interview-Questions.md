# Interview Questions — RAG Evaluation Harness (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual code and the numbers you measured** — golden-set composition,
audit logs, metric tables, noise floor, judge-agreement rates. Quote your comparison report; that
separates "knows Ragas exists" from "runs evals that gate releases."

---

## Part 1: Fundamentals — "Why eval at all?"

**Q1. Why do you need a golden dataset — and why did you build curated AND synthetic instead of one or the other?**

**Answer:** Without a fixed labeled set, every config comparison is vibes ("feels better on my 3 queries").
`golden.jsonl` fixes the questions, reference answers, and `must_hit` chunk IDs so dense vs hybrid vs rerank
run on IDENTICAL inputs — deltas become attributable. Curated pairs (hand-written, 50–100) are trustworthy
but slow and narrow; synthetic triples (LLM-generated from random chunks) scale coverage to paraphrases and
edge cases cheaply but inherit generator bias. Your audit log quantifies the tradeoff: X% synthetic reject
rate with reasons (unanswerable-alone, trivial, wrong reference). The rule: curated = trust anchor, synthetic
= coverage breadth, audit = the bridge. An all-synthetic set inflates scores on trivial questions (your
break-run proves it); an all-curated set of 20 can't cover 4 question types evenly.

**Q2. Walk me through what happens when you run `score` on one config, file by file.**

**Answer:** `harness.py` loads `golden.jsonl`, and per item × config calls the system under test (your Phase 2
RAG-A `ask` path with the config's flags: `--no-hybrid --no-rerank` for dense, etc.), capturing (answer,
retrieved chunk IDs, scores). `metrics.py` then scores two families: DETERMINISTIC retrieval metrics —
recall@k/MRR computed from `must_hit` vs retrieved IDs, zero LLM calls, exact; and JUDGE metrics — Ragas
faithfulness / answer relevancy / context precision / context recall, each an LLM call with the judge model
you logged. `compare.py` aggregates per-config × per-metric means + per-type splits + the noise column
(same-config-twice delta) into `scores.csv` + `report.md`. The two-family design is deliberate: never pay a
judge for what arithmetic computes (recall@k), and never trust arithmetic for what needs reading
(faithfulness).

**Q3. Why pin the system under test BEFORE writing eval code? What goes wrong otherwise?**

**Answer:** Your Phase 0 discipline: record the RAG-A commit, chunk size, and models at the top of `report.md`.
Otherwise the baseline moves mid-project (a corpus edit, a model re-pull) and every delta is uninterpretable —
"hybrid +0.06 recall" means nothing if dense's number came from a different index. Same reason for the
determinism check (5 queries × 2 runs): sampling nondeterminism becomes part of the noise floor instead of a
mystery. In interviews: "an eval is a measurement instrument; you calibrate (pin + noise-floor) before you
measure, same as any lab equipment." Evals B's `baseline.json` is this idea hardened into CI.

---

## Part 2: The Four RAG Metrics — "Each metric is a diagnosis"

**Q4. Define faithfulness, answer relevancy, context precision, context recall — and for each, say which half of the pipeline it blames.**

**Answer:** **Faithfulness** (generation blame): is every claim in the answer entailed by the retrieved context?
Low faithfulness with GOOD context = the generator hallucinates or over-extends — fix prompting/grounding, not
retrieval. **Answer relevancy** (generation blame): does the answer address the QUESTION (reverse check: can the
question be reconstructed from the answer)? Faithful-but-off-topic = retrieves fine, answers wrong — generation
framing bug. **Context precision** (retrieval blame): of retrieved chunks, how many are relevant (signal vs noise
— junk in top-k wastes context and invites hallucination)? **Context recall** (retrieval blame): of the relevant
chunks that EXIST, what fraction was found (misses = the answer was unformable no matter how good the generator)?
Your observations log should hold one real specimen of each failure — "low faithfulness WITH good context" vs
"low context recall" prescribe opposite fixes, and confusing them wastes sprints. That's the whole point of four
metrics instead of one vibes-score.

**Q5. My eval shows high answer relevancy but low faithfulness. What's happening, concretely?**

**Answer:** The system gives fluent, on-topic, UNSUPPORTED answers — the most dangerous RAG failure because it
reads well. Mechanism: retrieval missed (low context recall) or returned junk (low precision), and the generator
filled the gap from parametric knowledge instead of abstaining. Your empty-corpus break-run is the specimen:
context recall craters, relevancy stays oddly high, faithfulness collapses. Fixes in order: (1) abstention
threshold (`--min-score`) so unsupported answers never generate; (2) retrieval repair (the actual miss cause);
(3) stronger grounding instruction. Metric-split reading like this is what you demo live: point at the three
numbers and prescribe. Anyone can say "the answer was wrong"; you say "relevancy 0.9 + faithfulness 0.4 =
ungrounded fluency, fix the gate, not the prompt."

**Q6. Context precision vs context recall — why do you need both, and which does each RAG-A upgrade move?**

**Answer:** Precision = purity of what you got; recall = completeness of what exists. A system retrieving 1
perfect chunk scores perfect precision with terrible recall (answer incomplete); retrieving 20 chunks containing
the 3 good ones scores perfect recall with terrible precision (context bloated, generator distracted, cost up).
Your config table shows the division of labor: HYBRID moves recall (BM25 finds exact-term chunks dense missed —
more of the existing relevant set found); RERANK moves precision-flavored outcomes (top-1 correctness —
reordering the fused set so the best sits first). Quote the per-metric deltas. Threshold design (Evals B) then
follows: floor on recall (never miss), floor on faithfulness (never hallucinate) — precision monitored, not
gated, unless context-bloat costs bite.

---

## Part 3: Dataset Engineering — "The eval is only as good as its set"

**Q7. What makes a golden question GOOD vs vanity? How did you enforce the standard?**

**Answer:** Good: has a verifiable reference answer, `must_hit` chunk IDs you confirmed by eye, a type tag, and
HEADROOM behavior (system gets some right, some wrong — aces-everything teaches nothing, fails-everything
measures nothing; your Phase 1 verification enforced both directions). Vanity: trivially easy, ambiguous
reference, unanswerable-but-untagged, or all one type (recall the break-run: deleting unanswerables inflates
faithfulness — type balance IS the anti-gaming mechanism). Coverage rule: 4 types evenly (exact / paraphrase /
multi / unanswerable), because each type stresses a different stage (BM25 vs dense vs join vs abstention).
Fifty sharp questions beat five hundred soft ones — state your counts and the type split.

**Q8. Your synthetic audit rejected X%. What was wrong with the rejects, and why is a nonzero rate GOOD news?**

**Answer:** (Quote YOUR log.) Typical reject classes: question unanswerable from the chunk alone (generator
assumed broader context), trivially easy (lexical overlap gives it away — measures nothing), wrong reference
answer (generator hallucinated the answer — the eval set itself needs evals), duplicate intent of an existing
case. Nonzero reject rate proves the audit is REAL work, not rubber-stamping — a 0% rate means either a perfect
generator (it isn't) or a lazy auditor. The systematic generator weakness you found (name it) is itself a finding
about LLM-generated evals: they regress toward easy, answerable-from-chunk, single-fact questions — exactly the
distribution that flatters the system. That's why curated seeds anchor the set: humans write the hard multi-hop
and adversarial cases generators avoid.

**Q9. Contamination: what is it, how did you check, and what did the leak experiment prove?**

**Answer:** Contamination = test items (or near-dups) leaking into TRAINING data (fine-tuning pairs, few-shot
examples, even the generator's memory of the corpus phrasing) — scores then measure memorization, not capability.
Check: scripted near-dup scan (`difflib` threshold) between held-out/golden and every train set, logged, in-repo.
Your deliberate-leak run (5 held-out prompts into train) quantified the inflation: metric jumped +X — that number
is why the check script stays in the repo permanently. Same discipline guards the win-rate held-out (DPO) and the
SFT held-out (Project A). In interviews: "our +0.12 gain survives a contamination audit — here's the script" ends
the skepticism that kills most fine-tune claims.

---

## Part 4: Judges & Statistics — "Trust, but verify and quantify"

**Q10. What is LLM-as-a-judge mechanically, and what are its four biases with mitigations?**

**Answer:** Mechanically: a prompted LLM call over (question, answer, retrieved context, rubric) returning
score + justification — Ragas wraps this per metric with entailment-style checks (`judge.py` hand-rolls the same
for the add-on). Biases: (a) VERBOSITY — longer answers score higher regardless; mitigate with rubric-locked
brevity criteria + length-normalized reading of results. (b) SELF-PREFERENCE — judges favor their own model
family's style; mitigate by judging with a DIFFERENT family than the generator (and your judge-swap disagreement
rate quantifies it). (c) POSITION — pairwise judges prefer the first-presented; mitigate with order randomization
(your win-rate harness flips A/B — record the flip rate). (d) CALIBRATION DRIFT — scores shift across judge
versions; mitigate by logging judge model+version per run and re-anchoring on a fixed validation subset. The
meta-rule: the judge is ITSELF an unevaluated model until your human-agreement check (≥12/15) promotes it to
instrument.

**Q11. How did you validate the judge before trusting any config comparison?**

**Answer:** Two checks, both logged: (a) HUMAN agreement — I scored 15 items on faithfulness by hand; judge
matched ≥12 (below that, fix rubric/prompt FIRST — comparing configs with an untrusted judge is numerology;
record what rubric change closed YOUR gap). (b) JUDGE-vs-JUDGE — 10 items re-scored with a different model;
disagreement rate logged (this number bounds how seriously to take small deltas — if judges disagree by 0.08,
a 0.05 config "win" is noise). Only then do config deltas mean anything. Ordering matters absolutely:
validate → compare → gate. Evals B inherits this trust chain — its thresholds are only as honest as this step.

**Q12. What is the noise floor and how did you measure it? Why does every claim need it?**

**Answer:** Noise floor = |run1 − run2| of the SAME config (sampling + judge variance), per metric — your table's
rightmost column. Measured by scoring one config twice (different seed where sampling exists). Every claimed
improvement must CLEAR it: +0.03 on a metric with ±0.05 noise is not a finding, and your report says so
explicitly for at least one metric (the "didn't move" observation). This is the most-skipped step in amateur
evals and the single cheapest credibility upgrade: it converts "hybrid wins" into "hybrid wins faithfulness
+0.11 against ±0.03 noise." Thresholds in Evals B are set BELOW noise-aware significance — a floor inside the
noise band fires on luck, and your flake list proves you know it.

**Q13. Ragas vs DeepEval vs your hand-rolled `judge.py` — why all three, and where did they disagree?**

**Answer:** Ragas = primary engine (battle-tested RAG-metric prompts, comparable scores); DeepEval = cross-check
(different judge prompts — agreement with Ragas bounds prompt-sensitivity); `judge.py` = YOUR rubric klare
(built from scratch: rubric → prompt → parse → score, then diffed against Ragas). The disagreement analysis is
the deliverable, not the redundancy: where yours diverges from Ragas (quote 2–3 cases), adjudicate BY HAND and
decide who's right — that gap reveals rubric assumptions (e.g. Ragas penalizes concise-correct answers your
rubric rewards). Interview payoff: "off-the-shelf judges disagree with my rubric HERE, for THIS reason, and I
kept mine for the gate" demonstrates evaluation as engineering, not API-calling. (Full judge-building Q&A: Part 6.)

---

## Part 5: Comparison & Decisions — "From tables to verdicts"

**Q14. Walk me through your comparison report. What won, by how much, and on which question types?**

**Answer:** (Narrate YOUR `report.md`.) Shape: per-config means on 4 judge metrics + recall@k, split by type,
each with the noise column alongside. Expected story: hybrid lifts context recall on exact-term (+X, clears
noise); rerank lifts top-1/faithfulness on paraphrase+multi (+Y); relevancy flat everywhere (generator-bound);
unanswerables measured as abstention correctness, not scores. The verdict names the shipped config (full
hybrid+rerank, or hybrid-only if rerank's gain < its latency cost — "not worth it on this corpus" is a valid
verdict with the ms number attached). The per-type split is non-negotiable in the telling: global averages hide
that hybrid's win concentrates in exact-term — a stakeholder acting on the average mistunes the system.

**Q15. A metric didn't move. How do you know it's "no effect" vs "broken measurement"?**

**Answer:** Distinguish three ways: (a) noise check — delta < noise floor in BOTH directions across re-runs =
genuinely no effect (your documented non-mover); (b) headroom check — metric near ceiling already (relevancy
0.95 can't rise — saturation, not failure); (c) instrument check — metric flat because the JUDGE can't see the
change (e.g. recall@k computed on wrong `must_hit` IDs — verify by hand-scoring 5 items; if hand scores move and
the metric doesn't, the instrument is broken). Your observations log holds one "didn't move" verdict WITH the
disambiguation — that's the specimen. Amateurs delete flat metrics; you explain them.

**Q16. How does this harness feed Evals B, LLMOps, and fine-tuning? (The infrastructure view.)**

**Answer:** Downstream contracts: EVALS B imports `golden.jsonl` + metric definitions + thresholds (same cases,
now blocking); LLMOps A attaches these metric scores to TRACES (quality+cost in one view) and LLMOps B's canary
compares live sampled scores against `baselines.yml` (eval continuity); FINE-TUNING uses the harness as the
before/after scoreboard (SFT held-out metric + DPO win-rate are eval-harness outputs wearing different hats).
One harness, four consumers — that's why dataset quality and judge validation were front-loaded: every downstream
gate inherits this project's honesty. Say the dependency chain in one breath; it shows systems thinking.

---

## Part 6: Build-Your-Own Judge + Fine-tune vs Prompt vs RAG — "The add-on deep dive"

*(Deep dive — do this part after building `judge.py` + the tradeoff cheat-sheet.)*

**Q17. How did you build your own LLM judge from scratch? Walk through the five steps with YOUR rubric.**

**Answer:** (1) RUBRIC: dimensions + scale + anchors — yours (faithfulness / relevancy / style-safety), each
1–5 with a sentence per level (anchors are what separate a rubric from vibes; quote one level). (2) JUDGE
PROMPT: input + output-under-test + rubric + demand score PLUS justification (justification enables YOUR audit
of the judge — scoreless rationales and rationale-less scores are both undebuggable). (3) PARSE: extract the
number reliably (native `format="json"` constraint, not regex hope — Phase 1 lesson, third appearance).
(4) VALIDATE: human-labeled subset agreement (your ≥12/15 bar) + Ragas cross-check. (5) DIVERGENCE ANALYSIS:
where yours and Ragas disagree, hand-adjudicate (Q13's specimens). The build is ~100 lines; the credibility
comes from steps 4–5, not 1–3. Anyone can prompt a judge; you calibrated one.

**Q18. Judge risks again, but concretely: which bias bit YOU, and what did you change?**

**Answer:** (Name YOUR bite.) Candidates from your runs: verbosity (judge rewarded a bloated-but-faithful answer
over a terse-correct one — fix: brevity criterion in rubric, or length-stratified reading); position (flipped
A/B order changed X of 20 verdicts — fix: always report flip rate, randomize per matchup); self-preference
(same-family judge inflated generator scores vs cross-family judge by Δ — fix: cross-family judging for gates);
calibration drift (judge re-pull moved scores — fix: version-pinned judge + validation subset re-run). The
interview answer is always bite → number → fix, never a textbook list. Your audit log and judge-swap table are
the exhibits.

**Q19. Build the fine-tune vs prompt vs RAG decision framework. When is each the RIGHT call?**

**Answer:** PROMPT engineering: behavior/knowledge ALREADY in the base model, need format/style/elicitation —
cheapest (zero training), fastest to iterate, decision in minutes. RAG: knowledge EXTERNAL/fresh/proprietary or
fast-changing (docs, policies, user data) — model static, updates = edit docs; pays retrieval latency + infra.
FINE-TUNING (SFT/DPO): behavior must be BAKED IN (consistent format under prompt variation), latency forbids
retrieval, or prompting demonstrably fails (your SFT headroom proof: base scored poorly, tune fixed it) — pays
GPU + dataset + retraining-on-change + eval surface. Combos are normal (fine-tuned model INSIDE a RAG pipeline
— your capstone). The framework is a flowchart starting from "is the knowledge in the weights?" → "does it
change?" → "does prompting elicit it?" — each no leads to the next tool. Your cheat-sheet holds it on one page.

**Q20. Tradeoffs across the three: cost, latency, drift, data, eval surface — with YOUR numbers where they exist.**

**Answer:** COST: prompting ~$0 marginal (same inference); RAG adds embed+rerank per query (YOUR $/request from
LLMOps A: single-hop $X, multi-hop 3×); fine-tuning adds upfront GPU-hours (YOUR T4 hours) + near-zero marginal
(no retrieval step — the inference-cheapest option). LATENCY: fine-tuned fastest per request (single pass);
RAG slowest (embed+retrieve+rerank+generate chain — YOUR p50s); prompting in between. DRIFT/maintenance: RAG
updates instantly (edit docs, re-index); fine-tune needs retraining per change (stale-weight risk); prompts need
re-testing per model version (fragility). DATA: fine-tune hungriest (500–5k pairs + audit); RAG needs corpus +
chunking; prompting needs only examples. EVAL SURFACE: each adds failures — prompt fragility, retrieval misses,
adapter drift/forgetting. Cite your tables per row; the cheat-sheet compresses this to one page.

**Q21. Why is "I built my own judge" a strong interview talking point for senior roles?**

**Answer:** Because it compresses four senior signals into one artifact: (1) you treat quality as ENGINEERING
(rubrics, validation, noise floors) not taste; (2) you distrust your own automation (agreement checks,
divergence analysis — skepticism with receipts); (3) you think in tradeoffs (the framework doc proves breadth
beyond one technique); (4) you build leverage (your judge now gates CI and deploys — infra, not a notebook).
And it cost ~100 lines on top of existing harness infra — leverage per line is the senior flex. Close with the
line your report earns: "our shipped config won by +0.11 faithfulness against ±0.03 noise, judged by a
human-validated rubric, gated in CI" — measurement, validation, enforcement in one sentence.

---

## How to Use These Questions

1. **Open the report** — answer with `report.md` + `scores.csv` visible; point at rows, not memory.
2. **Quote the trust chain** — audit rate → human agreement → noise floor → delta. In that order, every time.
3. **Demo the break** — empty-corpus metric split, leak inflation, sabotage-vs-judge: live runs beat recaps.
4. **Connect downstream** — every answer ends where the harness's consumers (gate, canary, fine-tune) pick it up.
