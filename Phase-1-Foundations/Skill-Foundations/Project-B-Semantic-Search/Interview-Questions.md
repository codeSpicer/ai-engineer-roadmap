# Interview Questions — Project B: Semantic Search Over Your Notes

Complete the project, then quiz yourself. Answers are detailed.

## Phase 1 — Foundations · Project B

**Q1. What is an embedding and what does the vector actually represent?**
An embedding is a fixed-length dense vector (e.g. 384 or 1536 floats) produced by a
neural model that maps text into a continuous space where **semantic similarity is
encoded as geometric proximity**. Tokens/words/sentences with similar meaning land
close together; unrelated text lands far apart.

The vector doesn't "mean" anything human-readable per dimension — dimensions are
learned features (not "dimension 3 = topic, dimension 7 = sentiment"). What matters is
the *relative* positions: cosine similarity between two embedding vectors approximates
how related their meanings are. This is why embeddings power search: you compare your
query's vector against document vectors instead of matching keywords.

**Q2. What is chunking and how does chunk size affect retrieval quality?**
Chunking splits long documents into smaller passages before embedding, because
embedding whole books loses granularity and blows the context window. Typical sizes
are 200–1000 tokens with optional overlap.

Effects of size:
- **Too small**: loses surrounding context, so a chunk may be semantically ambiguous
  ("it" refers to something in the previous chunk). Retrieval returns precise but
  context-poor snippets.
- **Too large**: each chunk becomes a bland average of many topics, so similarity
  scores get noisy and the model gets fed irrelevant text (wasting tokens and
  diluting grounding).
- **Overlap** (e.g. 10–20%): reduces boundary loss by letting a concept span chunks,
  at the cost of duplicated storage.

The right size is empirical — this project has you experiment and observe quality
changes, which is the real lesson.

**Q3. What is cosine similarity and why use it over Euclidean distance for text?**
Cosine similarity measures the cosine of the angle between two vectors:
cos(a,b) = (a·b) / (|a||b|). It ignores vector magnitude and looks only at direction.

This matters because embeddings of long vs short texts of the same topic can have very
different magnitudes (lengths) but point the same way. Euclidean distance would
penalize the longer one for its magnitude, not its meaning. Cosine focuses on
semantics (direction), which is what we care about for text. Values range from -1
(opposite) to 1 (identical); for normalized embeddings it equals the dot product.

**Q4. What is a vector database and what operations does it provide beyond a flat list?**
A vector DB (Chroma, Qdrant, Pinecone, pgvector) stores vectors plus metadata and
supports:
- **Similarity / nearest-neighbor search**: given a query vector, return top-k most
  similar.
- **Indexing**: data structures (HNSW, IVF) that make search sub-linear instead of
  scanning every vector — essential at scale.
- **Metadata filtering**: restrict search to chunks from a specific file/source/date
  before or after similarity ranking.
- **Persistence and upsert**: store, update, and version collections.

A flat Python list with cosine sim works for hundreds of notes; a vector DB is what
makes millions of vectors fast and filterable.

**Q5. Why build semantic search *before* adding an LLM (no generation yet)?**
This project deliberately isolates the **retrieval half of RAG** so you understand
embeddings and vector search on their own. If you bolt generation on immediately,
failures blur together: is the answer wrong because retrieval fetched the wrong chunk,
or because the LLM misunderstood a good chunk? By building retrieval first and
validating that "search returns the most relevant chunks with sources," you establish
a trustworthy retrieval layer — the foundation RAG later depends on. It also teaches
you that a lot of "RAG quality" is really retrieval quality.

**Q6. What is top-k retrieval and why k (not just "the best one")?**
Top-k returns the k nearest chunks (e.g. 5). You rarely want just the single best
match because: (a) a query may need several complementary facts spread across chunks;
(b) the #1 result can be a false-positive that a reranker or the LLM would discard;
(c) more context usually helps grounding. k is a tunable knob — too low loses coverage,
too high adds noise and token cost. Hybrid RAG later fuses and reranks these candidates.
