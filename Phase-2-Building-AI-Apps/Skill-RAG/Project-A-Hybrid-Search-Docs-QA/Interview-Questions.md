# Interview Questions — Hybrid-Search Docs Q&A (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual code and the numbers you measured** — not generic definitions.
Quote your ablation table; that is what separates "read about RAG" from "built RAG."

---

## Part 1: Fundamentals — "Explain RAG like I'm new to this"

**Q1. What is RAG and why use it instead of just prompting a bigger model?**

**Answer:** Retrieval-Augmented Generation grounds an LLM's answer in externally retrieved passages.
Flow in this project (`generate.py` + `cli.py:ask`): query → hybrid retrieve → rerank → top-5 chunks
with IDs → prompt (instruction + numbered chunks + query) → `ollama.chat()` → answer with `[chunk_id]`
citations resolved against stored metadata.

Four reasons it beats relying on base knowledge: (1) **Hallucination control** — claims must come from
provided context, and citations make each claim checkable. (2) **Freshness/proprietary data** — the model
is frozen at training; updating `corpus/` + re-running `index` teaches it your docs with zero retraining.
(3) **Verifiability** — every answer ships sources (file + page), so a user or eval harness can audit it.
(4) **Cost/agility** — editing a document beats fine-tuning a model. The price is latency (embed + retrieve +
rerank + generate) and a whole new failure surface (everything in Q12).

**Q2. Walk me through what happens when I ask a question, end to end.**

**Answer:** Trace one `ask --trace` call through the pipeline diagram in the README: (1) `embedder.py`
embeds the query with `nomic-embed-text` (~190ms on CPU, the latency bottleneck); (2) `store.py` queries
Chroma for dense top-20 while `bm25.py` tokenizes the same query and scores the BM25 index for sparse
top-20 — these run independently; (3) `fusion.py` merges both ranked lists with RRF (`k=60`) into fused
top-20; (4) `rerank.py` runs the cross-encoder over query×each candidate jointly and keeps top-5;
(5) `generate.py` assembles the grounded prompt (system instruction + 5 numbered chunks + query) and calls
`ollama.chat()`; (6) citation IDs in the answer are parsed back to `{source, page, chunk_index}` metadata
and rendered as Sources. `trace.py` logs every stage (ranks, scores, prompt, answer) to JSONL — that log
is how you attribute any failure to retrieval vs generation.

**Q3. How does this project connect to Phase 1? What did you reuse vs build new?**

**Answer:** Phase 1 split the RAG loop in half deliberately. Project A (playground) taught generation
mechanics — sampling params, roles, JSON mode — reused here inside `generate.py`'s prompt construction and
the router/extractor prompts in Project B. Project B (semantic search) taught retrieval — `loader.py`,
`chunker.py`, `embedder.py`, `store.py` are copied forward nearly verbatim, extended with PDF parsing
(page numbers in metadata) and recursive splitting. What's genuinely NEW here: the second retriever
(`bm25.py`), the combiner (`fusion.py`), the precision stage (`rerank.py`), the grounded generator with
citation parsing (`generate.py`), abstention (`--min-score`), and the trace log. Interview framing:
"Phase 1 gave me retrieval primitives I trust; this project is the generation + fusion layer on top."

---

## Part 2: Retrieval Mechanics — "Dense vs BM25 vs hybrid"

**Q4. Dense vs keyword (BM25) retrieval — what's the real difference, and give me a query each one wins.**

**Answer:** Dense retrieval (`store.py`) embeds query and chunks into one vector space and matches by
cosine angle — it understands paraphrase ("car" ≈ "automobile") but is blind to exact rare strings and
sensitive to embedding quality. BM25 (`bm25.py`) is pure term statistics over tokenized text: term frequency
(how often the term appears in this chunk), inverse document frequency (rare-across-corpus terms weigh more),
length normalization (long chunks don't win by verbosity). It nails exact identifiers and rare terms but
fails on synonyms.

From your golden set: an exact-term query like an error code or product name ranks #1 under BM25 while dense
buries it (different surface form, weak semantic signal); a paraphrase query with zero shared words ("how does
attention handle word order" → "positional encodings") ranks ~0.72+ under dense while BM25 returns nothing.
That pair of measurements IS the hybrid justification — quote both.

**Q5. Explain BM25's formula intuition without hand-waving. What do TF, IDF, and length-norm each do?**

**Answer:** For query term q in chunk D: contribution ≈ `IDF(q) × TF_saturated(q,D) × length_norm(D)`.
**TF with saturation**: more occurrences help, but with diminishing returns (the 10th occurrence matters far
less than the 1st — BM25's `k1` parameter controls that curve, unlike raw TF-IDF's linearity). **IDF**:
`log((N - df + 0.5)/(df + 0.5))` — terms appearing in few chunks (error codes, surnames) get large weights;
terms everywhere ("the", "model") get near-zero. **Length norm** (`b` parameter): divides by chunk length
relative to average, so a 1200-char chunk doesn't outscore an 800-char chunk just for containing more words.
Practical consequence you observed: BM25 needs a real tokenizer (lowercase, stopword strip in `bm25.py`) —
indexing raw text with punctuation attached silently breaks term matching, the keyword equivalent of the
embedding model-mismatch bug.

**Q6. What is Reciprocal Rank Fusion and why ranks instead of scores?**

**Answer:** RRF fuses ranked lists without comparing their scores: `score(d) = Σ 1/(k + rank(d))`, ranks
1-based, `k=60` constant dampening top-rank dominance (`fusion.py`). A chunk ranked #1 dense + #2 BM25 scores
`1/61 + 1/62 ≈ 0.0325`; a chunk ranked #15 in one list only scores `1/75 ≈ 0.013`. Sum over retrievers, sort,
take top-20.

Why not average scores: BM25 scores live ~0–20, cosine similarities ~0–1 — any weighting is arbitrary and
corpus-dependent, and normalizing them destroys information. Ranks are already normalized (1st is 1st in any
system). That's RRF's robustness: it works the day you swap embedding models or retune BM25 `k1`/`b` without
recalibrating fusion weights. Asymmetric hits (in one list only) correctly get a single term — no imputation,
no invented rank. Your ablation table proves the payoff: fused recall@5 ≥ max(dense, BM25) on mixed query types.

**Q7. When does hybrid LOSE to pure dense? Be honest.**

**Answer:** On pure-paraphrase queries against clean prose, BM25 contributes noise — its top-20 contains
lexically overlapping distractors that dilute the fused list, and RRF can demote the dense winner. You should
have at least one golden example where dense-only top-1 beats hybrid top-1. The honest interview answer:
hybrid wins on mixed/realistic workloads (codes + prose + names); on synonym-heavy conceptual Q&A over clean
docs, dense-only ties or edges it. That's why `--no-hybrid` exists as a permanent ablation switch, not a
temporary debug flag — corpus character decides, not dogma.

---

## Part 3: Reranking — "Why a second model after retrieval?"

**Q8. Bi-encoder vs cross-encoder — what's actually different inside the models?**

**Answer:** The bi-encoder (your `nomic-embed-text`) encodes query and chunk SEPARATELY into vectors, once
each, then compares with cosine. Query and passage never see each other during encoding — fast (precompute
all chunk vectors at index time), but relevance is approximate geometry. The cross-encoder
(`ms-marco-MiniLM-L-6-v2` in `rerank.py`) takes query+passage CONCATENATED as one input and runs full
self-attention across both jointly, outputting a single relevance logit. "Does this passage answer this
query" is judged with cross-attention between query tokens and passage tokens — far more accurate, because
the model can align "refund window" in the query against "returns accepted within 30 days" in the passage
token-by-token instead of comparing two pooled averages.

**Q9. Why rerank AFTER retrieval instead of just using the cross-encoder for everything?**

**Answer:** Cost scaling. Cross-encoder inference is per-(query, passage) pair — scoring 800k chunks per
query is infeasible (that's the "retrieve cheap, rerank precise" pattern). Bi-encoder + ANN index reduces
millions → 20 candidates in milliseconds (vectors precomputed); the cross-encoder then scores only those 20
(+100–500ms CPU in your measurements — quote yours). Rerank moves top-1 correctness more than recall@5: it
reorders good candidates, it rarely rescues a miss the fusion stage dropped. If your ablation shows recall@5
flat but top-1 up, that's exactly the expected signature — say so.

**Q10. When is the reranker NOT worth its latency?**

**Answer:** Three cases from your data: (a) exact-term queries where BM25 already ranks the answer #1 —
reranking reshuffles correctly-ordered results for no gain; (b) corpus gaps (unanswerable questions) — reranking
irrelevant candidates just picks the best irrelevant one with more confidence; (c) tiny corpora where fused
top-5 is already correct — the +200ms buys nothing. Your Phase 6 verdict should name which bucket this
happened in, with the ms number. "We kept the reranker behind a flag because on exact-term queries it added
Xms for zero top-1 delta" is a senior answer.

---

## Part 4: Generation & Grounding — "Citations, abstention, hallucinations"

**Q11. How do citations actually work here, mechanically?**

**Answer:** Not post-hoc decoration. `generate.py` numbers the top-5 chunks (`[1]`–`[5]`, each with its
`source#chunk_index` ID) and the system instruction orders the model to cite per claim ("answer ONLY from
context, cite [id] per claim"). The response parser extracts `[n]` markers and joins them back to stored
metadata (`source file, page`) for rendering. A citation is therefore a POINTER into retrieved context, and
your spot-check (10 answers by eye: does the cited chunk actually contain the claim?) tests pointer validity.
A citation to a non-supporting chunk is a grounding bug — the most important bug class in RAG, and the one
your eval harness in Phase 3 will score as faithfulness.

**Q12. My RAG answer is wrong. How do you tell whether retrieval or generation is at fault?**

**Answer:** Open the trace log — this is the attribution boundary the whole project is built around.
If the retrieved top-5 CONTAINS the answer and the response is wrong → generation bug (prompt assembly,
instruction weakness, model capability, context ordering). If the top-5 DOESN'T contain it → retrieval bug,
full stop — no prompt engineering fixes wrong context. Your Phase 6 table should classify every miss this way.
Follow-up they always ask: "retrieval bug, now what?" → check chunking (answer split across boundary? fix
overlap), corpus gap (answer absent? abstention, not tuning), query-document mismatch (paraphrase? rephrase or
BM25 weight), threshold too aggressive. Never tune the generator for a retrieval miss.

**Q13. What is abstention and how did you calibrate the threshold?**

**Answer:** Abstention = the system says "I don't have that in the corpus" instead of generating from
irrelevant context. Mechanism: `--min-score` on the best rerank score (fallback: best dense cosine) —
below threshold, skip generation entirely. Calibration is empirical per model per corpus: plot best-score
distributions for answerable vs unanswerable golden questions and pick the value separating them (your README
score bands — 0.7+/0.5–0.7/<0.5 — are the starting prior, YOUR measured cutoff is the answer). Without it,
off-corpus queries produce confident hallucinations WITH citations — the worst RAG failure because citations
lend false authority. Your deliberately-broken run (off-corpus query with and without `--min-score`) is the demo.

**Q14. Why does the system prompt say "answer ONLY from context" — and when does the model disobey?**

**Answer:** The instruction constrains the model to the provided chunks, converting open-ended generation into
reading comprehension. It fails when: context is empty/irrelevant (model falls back to parametric knowledge —
hence abstention must trigger BEFORE generation, not as an instruction); the question needs synthesis across
chunks the prompt presents poorly ordered (graph paths first, prose after — your Project B ordering rule);
or the model is weak at instruction-following (your model-swap finding: smaller Ollama models obey grounding
instructions worse). Instruction + threshold + citation parsing are three independent guard layers — name all three.

---

## Part 5: Production & Evaluation — "Prove it's better, then ship it"

**Q15. How did you prove hybrid + rerank actually helped? Walk me through the ablation.**

**Answer:** Fixed golden set (20–30 Q/A with `must_hit` chunk IDs), three configs run identically:
(1) dense-only (`--no-hybrid --no-rerank`), (2) hybrid RRF (`--no-rerank`), (3) full (hybrid + rerank).
Per question: hit/miss at k=5, rank of first correct, abstention correctness on unanswerables. Report recall@5
and top-1-correct per question TYPE (exact-term / paraphrase / multi-fact / unanswerable), not just global
averages — the type split is where the story lives (hybrid dominates exact-term, rerank moves top-1 on
paraphrase/multi-fact). Change ONE variable between configs, keep chunking/model/k fixed. This exact harness
becomes Phase 3's eval project — say that.

**Q16. Break down query latency. What dominates, and what do you optimize first at 10× QPS?**

**Answer:** Your `--trace` timing (quote yours; expected shape): query-embed ~190ms + BM25 ~single-digit ms +
RRF negligible + rerank +100–500ms + generation seconds. Generation dominates wall-clock, rerank second,
embedding third; BM25/fusion are noise. At 10× QPS optimize in that order: stream generation tokens (perceived
latency), cache frequent queries (exact-match embed cache is nearly free), GPU/quantize the embedder and
reranker, batch concurrent rerank pairs, and only then touch ANN tuning. Never optimize the 5% slice first.

**Q17. What breaks moving this from laptop to production?**

**Answer:** Same data flow, split into services: ingest worker (watches corpus → chunk/embed/upsert
incrementally — full re-embeds stop being affordable past thousands of docs), serving API (embed query →
ANN lookup → rerank → generate with timeouts per stage), managed vector store (Chroma SQLite → Qdrant/Pinecone
past single-node scale), plus the Phase-1 lessons hardened: model version pinned in index metadata (upgrade =
scheduled full re-embed), deletion tombstoning (your deliberate-break run proves orphans otherwise linger),
per-stage latency metrics (your trace timing is the prototype), and the abstention signal in the API contract
so clients distinguish "answered" from "no good match."

**Q18. Where does naive RAG like this one still fail — what motivates Project B?**

**Answer:** Three failures this pipeline CANNOT fix by tuning: (a) it retrieves identically for greetings and
research questions — wasted work on no-retrieval queries; (b) one embedding can't capture multi-hop intent
("company that acquired X → their revenue") — needs decomposition + relation traversal, not better chunking;
(c) one-shot retrieval has no recovery — a bad first pass stays bad. Those are Project B's router, graph, and
retry loop respectively. Name a golden question from YOUR set in each bucket that this project fails — that's
the handoff.

---

## How to Use These Questions

1. **Answer out loud** — if you can't explain RRF's formula or bi-vs-cross-encoder without notes, revisit the code.
2. **Quote your tables** — every claim ("hybrid wins exact-term") needs your recall@5 delta attached.
3. **Demo the breaks** — rerun the deliberate-break experiments live; narrating a rescued failure beats reciting theory.
4. **Attribute precisely** — for any wrong answer, first sentence is always "retrieval or generation?" with trace evidence.
