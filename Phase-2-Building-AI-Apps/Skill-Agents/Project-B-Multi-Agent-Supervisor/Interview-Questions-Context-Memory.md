# Interview Questions — Gap Topic: Context Engineering & Memory Systems

Cheap standalone study piece (no full project). Pairs with Agents Project B. Quiz after reading.

## Gap Topic — Context Engineering & Memory (2026 hiring buzzword, name it explicitly)

**Q1. What is context engineering, and how does it differ from prompt engineering?**
Prompt engineering tweaks the *wording* of a prompt. **Context engineering** is the
discipline of deciding *what information goes into the model's context window at each
step* — retrieval results, compressed history, summaries, tool outputs, a scratchpad.
The insight (LSP-era 2025/26): for agents, success is less about clever prompts and more
about **engineering the right context** so the model has what it needs and isn't drowned
in noise. It's a systems problem, not a phrasing problem.

**Q2. Name the memory types and when to use each.**
- **Short-term / in-context memory**: the current prompt + conversation history in the
  window. Default; limited by context size.
- **Working memory / scratchpad**: transient state the agent writes to reason through a
  task (intermediate steps, todos). Used within a single run.
- **Long-term memory**: persistent store across sessions — vector DB (semantic recall),
  KV store, or graph. Used when the agent must remember users, facts, or past interactions
  beyond the window.

Pick by horizon: same-turn → short-term; multi-step reasoning → working; cross-session →
long-term.

**Q3. What are common memory architectures?**
- **Buffering**: keep last N turns (simple, loses old context).
- **Summarization-based compaction**: periodically summarize history to fit the window
  (MemGPT-style), trading detail for space.
- **Semantic recall**: embed past interactions and retrieve relevant ones on demand
  (RAG over memory).
- **Self-editing memory**: the model actively writes/updates its own memory entries
  (e.g. "user prefers terse answers") for future use.

**Q4. How does this project's checkpointing map to "long-term memory"?**
In Agents Project B, **checkpointing** snapshots shared state so runs pause/resume — that
state *is* a form of persistent memory (the agent picks up where it left off). It's the
bridge between working memory (in-run state) and long-term memory (persisted, resumable).
Being able to articulate this connection is the deliverable of the deep-dive note.

**Q5. What are the failure modes of memory systems?**
Context **overflow** (too much retrieved/historical text degrades or truncates),
**stale memory** (outdated facts persisted), **distraction** (irrelevant memory retrieved
and attended to), and **cost** (long context is expensive per token). Good context
engineering is mostly about *avoiding* these — compressing, filtering, and retrieving
selectively.
