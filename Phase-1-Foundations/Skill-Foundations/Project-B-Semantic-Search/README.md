# Project B — Semantic Search Over Your Notes

**Phase:** 1 — Foundations · **Skill:** Foundations · **Difficulty:** Beginner

## Overview
Build a semantic search engine over a folder of your own text/markdown notes.
**No generation yet** — this isolates embeddings + vector search so you understand
the retrieval half of RAG before adding an LLM.

## Links to roadmap.sh/ai-engineer
- Embeddings (OpenAI embeddings API + open-source embeddings)
- Vector Databases (indexing, similarity search, chunking)
- OpenSource AI (Ollama / Hugging Face for local embedding models)

## Concepts covered
Text chunking, embedding models, cosine similarity, nearest-neighbor search,
vector database basics, top-k retrieval.

## Prerequisites
- Project A completed
- `sentence-transformers` or an embeddings API

## Learning objectives
- Turn text into embeddings and understand what the vectors represent
- Store vectors in a vector DB and run similarity queries
- See how chunk size changes retrieval quality

## Suggested build steps
1. Load a folder of `.txt`/`.md` files and split into chunks.
2. Embed each chunk (local `sentence-transformers` or an embeddings API).
3. Store vectors in Chroma (or Qdrant) with metadata (source file, chunk index).
4. Build a `search "<query>"` command returning top-k chunks with scores + sources.
5. Experiment with chunk sizes and compare result quality.

## Reference material
- Chroma: https://github.com/chroma-core/chroma
- sentence-transformers: https://www.sbert.net/

## Definition of done
- Querying returns the most relevant chunks with source citations and scores.
- You can explain the effect of chunk size on retrieval quality.
