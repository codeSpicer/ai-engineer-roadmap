# Interview Questions — Agents Project A: ReAct Tool-Using Agent (with MCP)

Complete the project, then quiz yourself. Answers are detailed.

## Phase 2 — Building AI Apps · Agents · Project A

**Q1. What is the difference between a plain LLM and an Agent?**
A plain LLM is a stateless next-token predictor: you give it text, it returns text. An
**agent** wraps the LLM in a loop with **tools** and **observation**: it can take
actions in the world (call APIs, run code, search), see results, and decide the next
step. The LLM becomes the "brain" that plans and chooses actions; the agent is the
system that executes and feeds results back. Agents act; LLMs only answer.

**Q2. Explain the ReAct pattern step by step.**
ReAct = **Reason → Act → Observe**, repeated:
1. **Reason**: the model thinks (often in a "Thought:" step) about what to do next.
2. **Act**: it emits a tool call (e.g. `search("weather London")`).
3. **Observe**: the runtime executes the tool and returns the result as an observation.
4. Loop until the model emits a **Final Answer**.

This interleaving of reasoning and acting lets the model adapt mid-task when an early
result changes its plan — unlike a fixed chain-of-thought that can't act.

**Q3. What is tool / function calling and why do tools need schemas?**
Tool calling is the model emitting a structured request to invoke a known function with
arguments, instead of free text. Schemas (JSON Schema) define each tool's name,
description, and parameter types. They matter because: (a) the runtime must know what
tools exist and how to call them; (b) the model uses the description to pick the right
tool; (c) the runtime validates/parses arguments safely before execution. Without
schemas, you'd be parsing fragile natural language.

**Q4. Why add a max-steps guard and robust error handling?**
- **Max-steps guard**: prevents infinite loops. A confused agent can call tools
  forever (cost + hang). Capping steps forces termination.
- **Error handling**: tools fail (network down, bad args, timeout). The agent should
  catch the error, observe it, and either retry with corrected args or give up
  gracefully — not crash the whole run. Well-handled errors become observations the
  model can reason about.

**Q5. What is MCP (Model Context Protocol) and how does it differ from plain function calling?**
MCP is a **standard protocol for exposing and consuming tools** across process and
language boundaries. A tool runs as an MCP *server*; the agent (client) discovers its
tools and calls them over a defined transport.

Difference from plain function calling: plain calling is usually **in-process** —
functions defined in your Python and called directly by the agent framework. MCP
**decouples** the tool from the agent: the tool can run in another process, another
language, or be shared across many agents/clients. It gives a standard contract
(discovery, schema, invocation) so you don't rebuild integration glue per tool. Think
"USB-C for AI tools" vs hard-wiring each one.

**Q6. Why implement the agent loop framework-free first?**
Building it by hand (call model → parse tool call → dispatch → feed observation) forces
you to understand every moving part: prompt construction, parsing model output,
executing tools, managing history. Frameworks (LangChain, etc.) abstract this away; you
learn more by doing it once raw, then appreciate the framework later. It also makes
debugging and the "reasoning trace" inspection the project requires much clearer.
