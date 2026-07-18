# Project A — ReAct Tool-Using Agent (with MCP)

**Phase:** 2 — Building AI Apps · **Skill:** Agents · **Difficulty:** Intermediate

## Overview
A single agent that reasons, selects tools, and acts in a loop until it produces a final answer.
Includes **two tool-integration paths**: plain function-calling and a **Model Context Protocol (MCP)** server.

## Links to roadmap.sh/ai-engineer
- AI Agents (ReAct, tools / function calling)
- Model Context Protocol (MCP) — folded into this skill

## Concepts covered
The agent loop, tool/function-calling schemas, ReAct (reason -> act -> observe),
error handling, and connecting tools via MCP.

## Prerequisites
- Foundations Project A
- A function-calling-capable model

## Learning objectives
- Implement the reason/act/observe loop (ideally framework-free first)
- Define tools with clear schemas and robust error handling
- Expose/consume a tool through an MCP server

## Suggested build steps
1. Build a bare agent loop that calls the model and dispatches tool calls.
2. Add tools: web search, calculator, file read/write, and one small API.
3. Add error handling + a max-steps guard to prevent infinite loops.
4. Wrap one tool as an MCP server and have the agent consume it via MCP.
5. Test on multi-step tasks and inspect the reasoning trace.

## Reference material
- huijunwu/learn-claude-code (s01–s03): https://github.com/huijunwu/learn-claude-code
- LangChain DeepAgents Playbook (Level 2–3): https://github.com/sdivyanshu90/LangChain-DeepAgents-Playbook
- Model Context Protocol: https://modelcontextprotocol.io/

## Definition of done
- The agent completes multi-step tasks and can use at least one tool via MCP.
- You can read the trace and explain each tool decision.
