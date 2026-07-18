# Project B — Agentic / Graph RAG

**Phase:** 2 — Building AI Apps · **Skill:** RAG · **Difficulty:** Intermediate

## Overview
A RAG assistant that **decides how to retrieve**: whether to retrieve at all, which method to use,
and whether to retry — plus knowledge-graph traversal for multi-hop questions.
This extends *beyond* what roadmap.sh covers.

## Links to roadmap.sh/ai-engineer
- RAG (advanced) + AI Agents (dynamic retrieval decisions)
- Extends beyond the roadmap into Agentic RAG and Graph RAG

## Concepts covered
Dynamic retrieval routing, query decomposition, multi-hop reasoning,
knowledge graphs (entities + relationships), self-correction/retry.

## Prerequisites
- RAG Project A
- Basic agent/tool-calling and graph concepts (nodes/edges)

## Learning objectives
- Let an agent choose the retrieval strategy per query
- Build and traverse a small knowledge graph for multi-hop questions
- Add retry logic when retrieval quality is poor

## Suggested build steps
1. Start from Project A's pipeline.
2. Add a router that classifies queries: answer-directly vs retrieve vs multi-hop.
3. Extract entities/relationships into a graph store (Neo4j or in-memory NetworkX).
4. Implement graph traversal to gather multi-hop context before vector search.
5. Add a self-check that retries with a different strategy on low-confidence answers.

## Reference material
- Gauntlet-AIDP/rag-cookbook (steps 04 Graph RAG, 05 Agentic RAG): https://github.com/Gauntlet-AIDP/rag-cookbook
- NirDiamant/RAG_Techniques (advanced notebooks): https://github.com/NirDiamant/RAG_Techniques

## Definition of done
- The system answers a multi-hop question that Project A cannot, and skips retrieval when unnecessary.
- You can trace why a given query took a given retrieval path.
