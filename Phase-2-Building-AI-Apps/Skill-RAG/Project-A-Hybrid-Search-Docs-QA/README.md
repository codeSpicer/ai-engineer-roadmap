# Project A — Hybrid-Search Docs Q&A

**Phase:** 2 — Building AI Apps · **Skill:** RAG · **Difficulty:** Intermediate

## Overview
A question-answering system over a real document corpus that answers with citations,
using **hybrid retrieval** (BM25 keyword + dense vectors with Reciprocal Rank Fusion) plus reranking.

## Links to roadmap.sh/ai-engineer
- RAG (implementing RAG: chunking, indexing, retrieval, generation)
- Embeddings + Vector Databases

## Concepts covered
Chunking strategies, dense vs keyword (BM25) retrieval, Reciprocal Rank Fusion,
reranking, grounded generation with citations.

## Prerequisites
- Foundations Projects A & B
- Vector DB (Chroma/Qdrant), an LLM for generation

## Learning objectives
- Build an end-to-end RAG pipeline that grounds answers in retrieved context
- Combine BM25 + vector search and understand when hybrid beats pure vector
- Add a reranker and measure the quality difference

## Suggested build steps
1. Ingest a document set (PDFs / a wiki dump); chunk + embed into a vector DB.
2. Implement dense retrieval and BM25 retrieval separately.
3. Combine them with Reciprocal Rank Fusion.
4. Add a cross-encoder reranker over the fused candidates.
5. Generate answers with inline citations to source chunks.

## Reference material
- Gauntlet-AIDP/rag-cookbook (steps 01–03): https://github.com/Gauntlet-AIDP/rag-cookbook
- tkeitzl/rag-from-scratch: https://github.com/tkeitzl/rag-from-scratch
- NirDiamant/RAG_Techniques: https://github.com/NirDiamant/RAG_Techniques

## Definition of done
- Answers cite their sources and visibly improve when hybrid + rerank are enabled.
- You can explain when hybrid search outperforms pure vector search.
