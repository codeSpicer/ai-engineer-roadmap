# Interview Questions — RAG Project A: Hybrid-Search Docs Q&A

Complete the project, then quiz yourself. Answers are detailed.

## Phase 2 — Building AI Apps · RAG · Project A

**Q1. What is RAG and why is it used instead of relying on the base model's knowledge?**
Retrieval-Augmented Generation grounds an LLM's answer in externally retrieved
context. You take the user query, retrieve relevant passages from a knowledge source
(docs, wiki, DB), and inject them into the prompt so the model answers *from* that
context.

Why not just prompt the model: (1) **Hallucination** — base models confidently invent
facts; grounding reduces this. (2) **Freshness** — models are frozen at training time;
RAG gives access to up-to-date/proprietary data without retraining. (3) **Citations**
— retrieved chunks let you show sources. (4) **Cost/agility** — update a document
store instead of fine-tuning. RAG trades some latency for verifiable, current answers.

**Q2. Dense vs keyword (BM25) retrieval — what's the difference and when does hybrid win?**
- **Dense retrieval** embeds query and documents into vectors and matches by semantic
  similarity. It handles paraphrase and meaning ("car" matches "automobile") but can
  miss exact technical terms and is sensitive to embedding quality.
- **Keyword / BM25** matches exact terms using TF-IDF-style statistics (term frequency,
  inverse document frequency, length normalization). It's excellent for specific
  identifiers, error codes, product names, and rare terms, but blind to synonyms.

**Hybrid wins** when queries mix both: a support question might contain an exact error
code (BM25 strength) and a vague description (dense strength). Neither alone covers
both. Hybrid retrieval fuses the two result sets, getting the precision of keyword
matching plus the recall of semantics.

**Q3. What is Reciprocal Rank Fusion (RRF) and why use it over score averaging?**
RRF combines multiple ranked result lists without needing to normalize their scores
(which is hard because BM25 and dense-retrieval scores live on different scales).

Formula: score(d) = Σ over retrievers of 1 / (k + rank(d)), where rank is the
document's position (1-based) in that retriever's list, and k is a small constant
(typically 60) to dampen top-rank dominance. A document ranked #1 by both methods gets
a high fused score; one ranked low by both gets near zero.

It's rank-based, so it doesn't care that BM25 scores are 0–20 and dense scores are
0–1. This robustness is why RRF is the standard fusion method in hybrid search.

**Q4. What does a cross-encoder reranker do, and why add it *after* retrieval?**
Retrieval (bi-encoder) encodes query and docs *separately*, then compares — fast, but
the two never "see" each other during encoding, so relevance is approximate. A
**cross-encoder** takes the query and a candidate passage *together* as one input and
outputs a single relevance score after full cross-attention. Because it attends to both
simultaneously, it's far more accurate at judging "does this passage actually answer
the query."

You add it *after* retrieval (not instead) for efficiency: retrieval over millions of
vectors must be cheap (bi-encoder + ANN index), but you only need to rerank the top
~20–50 fused candidates, where cross-encoder cost is acceptable. This two-stage design
is the standard "retrieve cheap, rerank precise" pattern.

**Q5. How do you ground answers with citations, and why does it matter?**
You instruct the LLM to answer strictly from the provided context and cite the source
chunk (by ID or filename) inline — e.g. "The refund window is 30 days [chunk_42]." You
then map the cited ID back to the stored chunk's metadata (source file, chunk index) to
render a clickable reference.

Citations matter because they make the answer **verifiable**: a user (or your eval
harness) can check the claim against the source. They also expose retrieval failures —
if the model cites a chunk that doesn't support the claim, you've found a grounding bug.

**Q6. How would you measure that hybrid + rerank actually improved quality?**
Use the eval harness (Phase 3 Evals A): build a golden Q/A dataset, then run the system
in three configs — (1) dense only, (2) dense + BM25 fusion, (3) + reranker — and score
each on faithfulness, answer relevancy, context precision/recall. Compare the scored
tables and pick the winner with evidence. If reranking doesn't move the metrics, it may
not be worth its latency cost for your corpus — measure, don't assume.

**Q7. What is chunking/indexing in this pipeline and how do they connect to Phase 1?**
Ingestion chunks documents (PDFs/wiki), embeds each chunk (Project B's embeddings), and
stores them in a vector DB with metadata (Project B's vector DB). Indexing (HNSW/IVF)
makes the similarity search fast. So this project reuses Phase 1's retrieval primitives
and adds the LLM generation + fusion + reranking on top to form a complete RAG system.
