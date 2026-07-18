# Interview Questions — Gap Topic: Agentic System Design / Agents-at-Scale

HIGHEST PRIORITY gap. Currently zero content in the roadmap. Study + design exercises.
Quiz after working through the architecture write-ups.

## Gap Topic — Agentic System Design (Pairs with Agents + LLMOps)

**Q1. How do you make an agent system robust at scale?**
Treat the agent like a distributed system, not a script:
- **Concurrency with limits**: bound parallel tool calls / sub-agents to avoid overload.
- **Idempotency**: retrying a tool call shouldn't double-apply side effects (use
  idempotency keys for writes/APIs).
- **Retries with backoff**: transient failures (rate limits, timeouts) recover gracefully.
- **Timeouts**: no tool/step runs forever; fail fast and surface the error.
- **Persistent state**: externalize state (DB, checkpoint) so crashes don't lose work.
- **Failure isolation**: one agent/sub-task failing shouldn't take down the whole run.
- **Observability**: trace every step (see LLMOps A) so you can debug at scale.

**Q2. MCP vs API wrapper — when does MCP earn its overhead?**
A **thin API/SDK client** suffices when one agent integrates one service, tightly coupled,
same language. **MCP** earns its overhead when tools are **reused across many
agents/clients/processes/languages** and you want a *standard* discovery + invocation
contract (the agent learns available tools dynamically, not via hardcoded code). MCP
shines in multi-agent or multi-tool ecosystems where rebuilding integration glue per
consumer is wasteful. If it's a single one-off call, MCP is overkill.

**Q3. Design tradeoffs in agent orchestration — centralized vs decentralized.**
- **Centralized (supervisor)**: easier to reason about, gate, and debug; single point of
  failure; can become a bottleneck/context hog.
- **Decentralized (swarm)**: resilient, parallel; harder to control, trace, and guarantee
  correctness.
Pick by need: most production systems start centralized for control, add decentralization
only where parallelism/robustness demands it.

**Q4. How do you handle cost and latency in a scaled agent system?**
- Cache repeated retrievals/tool results.
- Bound reasoning loops (max steps) and token budgets per run.
- Use cheaper models for routing/classification, expensive ones for synthesis.
- Route simple queries to skip agents entirely (dynamic routing, see RAG Project B).
- Observe per-request cost (LLMOps A) and set alerts.

**Q5. Where do you put human-in-the-loop in a scaled system?**
At the **highest-cost-of-mistake** boundary: before irreversible actions (send email,
charge payment, publish), not on every step (too slow). Combine with eval gates
(Phase 3 Evals B) so humans review only flagged/low-confidence cases. This is the
"best practices for agentic system design" the cohort Week 8 calls for — and exactly the
"real engineering" gap worth filling for interviews.
