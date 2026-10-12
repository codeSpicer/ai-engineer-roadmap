# ollama-react-agent — ReAct Tool-Using Agent (with MCP)

> Standalone repo for this project. Curriculum source: `ai-engineer-roadmap`
> Phase 2 · Skill Agents · Project A.

**Phase:** 2 — Building AI Apps · **Skill:** Agents · **Difficulty:** Intermediate

A single agent that reasons, selects tools, and acts in a loop until it produces a final answer.
Includes **two tool-integration paths**: plain in-process function-calling and a
**Model Context Protocol (MCP)** server. **Local-first: Ollama function-calling model, zero API keys.**
Build the loop **framework-free first** (raw `ollama.chat` + manual dispatch), then compare against
a framework — the hand-rolled version is where the learning lives.

An agent = LLM brain + tool hands + observation loop. The LLM never touches the world directly;
it emits structured tool requests, your runtime executes them, results come back as observations,
and the loop repeats until Final Answer or max-steps.

## Links to roadmap.sh/ai-engineer

- AI Agents (ReAct, tools / function calling)
- Model Context Protocol (MCP) — folded into this skill

## Concepts covered

The agent loop (reason → act → observe), tool schemas (JSON Schema as the model/runtime contract),
ReAct prompting (Thought/Action/Observation interleaving), native function-calling vs prompt-parsed
actions, error-as-observation handling, max-steps termination guards, reasoning-trace inspection,
MCP (server/client, discovery, transport decoupling), framework-free vs framework debugging tradeoffs.

## Prerequisites

- Foundations Project A (sampling params, system/user roles, JSON mode — all reused under the hood)
- Ollama with a function-calling-capable model (`qwen3.5:4b` — tier guide for 16GB Macs in root `MODELS.md`)
- `uv pip install ollama mcp` (+ `requests` for web-search/API tools)

## Learning objectives

- Implement the reason/act/observe loop by hand and read a full trace explaining each tool decision
- Define tools with clear JSON schemas, descriptions that drive selection, and validated args
- Make tool failures into observations the model can recover from (not crashes)
- Expose one tool as an MCP server and consume it through MCP — and articulate what MCP buys over in-process calls

## How it works (the loop)

```
user task
  │
  ▼
prompt = system (role + tool schemas + ReAct format) + history (thoughts, actions, observations)
  │  ollama.chat(model, messages, tools=[...])
  ▼
model output:  Thought: ...  →  Action: tool_name(args)   OR   Final Answer: ...
  │                                              │
  │ dispatch                                     └─ done → return answer + trace
  ▼
registry[tool_name](validated_args)  →  Observation: <result or ERROR: ...>
  │  append to history; steps += 1; if steps > MAX → force-terminate
  └─ loop (model sees the observation, reasons again)

Two wirings for the SAME tool:
  in-process:  registry["read_file"] = python function      (direct call)
  MCP:         registry["read_file"] = mcp_client.call(...) (via MCP server subprocess)
```

The trace (every Thought/Action/Observation with timestamps) is the primary artifact —
"you can read the trace and explain each tool decision" is the definition of done.

## First-principles guide — read this if ReAct / MCP feels fuzzy

### How an LLM "calls a tool" (it's not magic)

1. The LLM never touches files or the web itself. Your code passes it `tools=[...]`
   schemas (these live in `react_agent/tools.py`).
2. The model replies with a structured `tool_calls` object, e.g.
   `calculator(expression="17*23")` — not the answer, just a _request_.
3. Your `dispatch(name, args)` runs the real Python function, gets a string back
   like `"391"`, appends it as an `Observation` message, and calls the model again.
4. The model sees the result and reasons again. That
   Thought → Action → Observation repeat _is_ ReAct.

Worked trace for `evals/tasks.md` S1 ("What is 17\*23?"):

```
User task → Model: call calculator(17*23) → you run it → Observation: 391
→ Model: Final Answer: 391
```

### MCP in one paragraph

MCP is the same thing with one extra hop: instead of `dispatch()` calling the Python
function directly, it asks a separate MCP server process over stdio. Think USB-C vs
hard-wired — same tool, decoupled. Same task, same pass rate, small +ms latency.
That latency delta _is_ the MCP tradeoff interviewers ask about.

### Watch in this order

[www.youtube.com/watch?v=bOhK-FRR-Ac](https://www.youtube.com/watch?v=bOhK-FRR-Ac)

- Ollama native tool-calling (what `qwen3.5:4b` does): https://www.youtube.com/watch?v=jzruyK0xNPg
- MCP from zero, hands-on playlist: https://www.youtube.com/playlist?list=PLlrxD0HtieHjYfVUpGl_-ai7D6FRBjV-d
- Code-along companion: https://github.com/microsoft/mcp-for-beginners
- Ollama tool-calling docs: https://docs.ollama.com/capabilities/tool-calling

### Micro-task ladder (15–20 min each, in order)

1. **Be the loop on paper.** Take S1, write out _your_ Thought / Action / Observation /
   Final Answer by hand. That's all ReAct is.
2. **See a raw `tool_calls` object.** No loop yet — one `ollama.chat(model="qwen3.5:4b", messages=[...], tools=TOOLS)`, print `response.message.tool_calls`. Prove the model
   emits a request, not text.
3. **Hand-run 2 steps.** Copy the `tool_calls` args, call `dispatch("calculator", args)`
   yourself, send the result back as `{"role": "tool", "content": "391"}` in a second
   `ollama.chat`. Watch it produce the final answer. This is the whole loop, manually.
4. **Close the loop (Phase 2).** Wrap step 3 in `while steps < 5`. Run no-tool task N1
   (haiku — correct = _zero_ `tool_calls`) and error task E1 (`note.md` lowercase →
   `ERROR: file not found` observation → model retries `NOTES.md`).
5. **Break it on purpose.** max-steps=1 on 3-step task M2, kill network during
   `web_search`, ask for `/etc/passwd`. Each must end as a readable `ERROR`
   observation, never a crash.
6. **MCP swap (Phase 4).** Expose just `read_file` as an MCP server, route that one entry
   through `mcp_client` instead of direct call. Run S2 both ways — same pass, small +ms.

If you do 2 and 3, step 4 clicks fast.

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
ollama serve
ollama pull qwen3.5:4b

# Sanity: model must support tools — if it emits fake JSON instead of tool_calls, switch models
python -m react_agent run "what is 17 * 23?" --trace
python -m react_agent run "read NOTES.md and summarize it" --trace
python -m react_agent run "search the web for <topic> and save findings to out.md" --trace --mcp
```

| Flag          | Where | Default       | Meaning                                                           |
| ------------- | ----- | ------------- | ----------------------------------------------------------------- |
| `--trace`     | run   | off           | print every Thought/Action/Observation                            |
| `--max-steps` | run   | `10`          | loop guard before forced termination                              |
| `--mcp`       | run   | off           | route eligible tools through the MCP server instead of in-process |
| `--model`     | run   | `qwen3.5:4b`  | must support native`tools=` calling                               |
| `--log`       | run   | `trace.jsonl` | append machine-readable trajectory per run                        |

## Project layout (files you will create)

```
react-tool-agent/
├── requirements.txt
├── react_agent/
│   ├── __main__.py        `python -m react_agent` entry
│   ├── cli.py             run subcommand, flags, pretty trace printing
│   ├── loop.py            THE agent loop (prompt build → chat → dispatch → observe)
│   ├── tools.py           tool implementations + JSON SCHEMAS + registry
│   ├── mcp_server.py      same tools exposed as an MCP server (stdio)
│   ├── mcp_client.py      client wrapper matching the in-process registry interface
│   └── trace.py           JSONL trajectory log (thoughts, calls, args, results, ms)
├── evals/
│   └── tasks.md           8–12 multi-step tasks with expected tool sequences
└── README.md              this file + your measured tables
```

Tool set to implement (each: name, description, JSON schema, handler, error paths):
`calculator` (safe eval, no `eval()` on raw input) · `read_file` / `write_file` (sandboxed to workdir) ·
`web_search` (DuckDuckGo API or requests scraper) · one small JSON API (weather/time/stocks — your pick).

---

## Build phases (do these in order — they ARE the curriculum)

### Phase 0 — Task set first (before any agent code)

- [x] Write `evals/tasks.md` with 8–12 tasks across 4 buckets:
  - **single-tool** (2–3): "what is 17\*23" → calculator only.
  - **multi-step** (3–4): "search X, save summary to file" → search → write.
  - **error-recovery** (2–3): task whose first attempt SHOULD fail (bad path, missing arg) → agent must retry corrected.
  - **no-tool** (1–2): "write a haiku" → must answer directly with zero tool calls (over-triggering is a bug).
- [x] Verify: for each task you can state the EXPECTED tool sequence. If you can't, the task is vague — rewrite it.

### Phase 1 — Tools + schemas (no LLM yet)

- [x] `tools.py`: implement the 4–5 tools as plain functions with JSON schemas
      (`name`, `description`, `parameters` with types/required). Descriptions must say WHEN to use the tool —
      the model selects tools by reading these, so "reads a file" < "reads a UTF-8 text file under workdir; use when the task references a local file."
- [x] Unit-test each tool directly (bad args, missing file, network down) — every failure returns a STRING error,
      never raises out of the registry.
- [x] Verify: call each tool from a REPL with good + bad inputs; all bad inputs produce clean error strings.

### Phase 2 — The loop, framework-free (the core)

- [x] `loop.py`: system prompt (role + tool list + ReAct format + "Final Answer:" convention) →
      `ollama.chat(tools=...)` → if `tool_calls`, validate args against schema → dispatch → append observation → repeat.
- [x] Native tool-calling first (`tools=` param). `qwen3.5:4b` uses native
      `tool_calls` (S1: `calculator({'expression': '17 * 23'})` → `391`); no fake
      JSON observed — no model switch needed.
- [x] `--max-steps` guard: `--max-steps 1` on `9*10` stops after 1 Action/Observation
      with `Stopped after 1 steps without a Final Answer (partial trace above)` — no hang.
- [x] Verify: S1 (`17*23` → `391`, 2 steps) + N1 (haiku, zero tool calls) pass
      with traces narratable line by line (Thought → Action → Observation → Final Answer).

- **Status: Phase 2 complete (2026-09-27).** `qwen3.5:4b` native `tool_calls` confirmed,
  guard confirmed, S1+N1 traces saved in-session.

### Phase 3 — Errors as observations + multi-step

- [x] Every tool exception → `"ERROR: <what> — <how to fix>"` observation fed back to the model
      (E1: `ERROR: file not found: note.md — available files: NOTES.md, prices.txt` → retried `NOTES.md`).
- [x] Ran multi-step (M2-variant: `price.txt`→ERROR→`prices.txt`→`calculator(2.50+3.20+1.80)`→`write_file(total.txt)`=7.5)
  - error-recovery (E1 3 steps; big-number E2 `12769*83`→`1059827`, 2 steps); traces kept in-session.
- [x] Verify: E1 shows ERROR observation → corrected `read_file(NOTES.md)` → summary success. No crash on first error.

- **Status: Phase 3 complete (2026-09-27).** Known gaps: small-number E2 answered `96` from weights with zero
  calls (under-triggering); `error.txt` probe hit a no-verify-then-stop loop until max-steps (see observation 6).

### Phase 4 — MCP server + client (same tools, second wiring)

- [x] `mcp_server.py`: exposes `read_file` via `@mcp.tool()` on `MCPServer("react-tools")` over stdio
      (mcp 2.x API: `from mcp.server.mcpserver import MCPServer`; body delegates to `tools.read_file`).
- [x] `mcp_client.py`: `read_file_via_mcp(path)` + `registry_with_mcp()` exposing the identical
      name→function interface, so `loop.py` can't tell which wiring serves the call.
- [x] `--mcp` flag swaps the `read_file` registry entry to MCP-backed; S2 run both ways.
- [x] Verify: S2 identical summaries both wirings; trace shows `Action:mcp` vs `Action:in-process`;
      MCP hop measured ~926ms vs ~0ms in-process (fresh subprocess spawn per call).

- **Status: Phase 4 complete (2026-09-27).**

### Phase 5 — Trace report (the deliverable)

- [x] Full task set run twice (in-process, MCP where applicable); table below.
- [x] Two annotated traces (clean multi-step M2; error→recovery E1) — see below.
- [x] Verdict: wasted steps, description mis-selections, MCP cost/benefit — see below.

- **Status: Phase 5 complete (2026-09-28).**

#### Pass table (final)

| Task                   | Expected                                 | In-process                                                                 | MCP                                                                                       | Steps | Notes                                                                                                                                                         |
| ---------------------- | ---------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S1`17*23`              | `[calculator]`                           | pass (`391`)                                                               | pass (`391`, `Action:mcp` only labels `read_file`; calculator stays in-process by design) | 2     | native`tool_calls`                                                                                                                                            |
| S2 read`NOTES.md`      | `[read_file]`                            | pass                                                                       | pass (identical summary,`Action:mcp`)                                                     | 2     | same output both wirings (`True`)                                                                                                                             |
| S3 Berlin weather      | `[get_weather]`                          | pass (`24.3°C`, live Open-Meteo)                                           | n/a (not MCP-routed)                                                                      | 2     | live API, not fixture                                                                                                                                         |
| M1 search→save         | `[web_search, write_file]`               | pass (`out.md` 1544 chars; model ran 2 searches unprompted before writing) | n/a                                                                                       | 5     | extra search = wasted step, still correct                                                                                                                     |
| M2 read→compute→write  | `[read_file, calculator, write_file]`    | pass (`total.md` = 7.5)                                                    | pass (`total_mcp.md` = 7.5)                                                               | 4     | cleanest trace (annotated below)                                                                                                                              |
| M3 two searches→file   | `[web_search, web_search, write_file]`   | not run (M1 covers the pattern; DDG rate limits)                           | n/a                                                                                       | —     | skipped deliberately                                                                                                                                          |
| E1`note.md` lowercase  | `[read_file→ERROR, read_file→success]`   | pass (ERROR + available-files hint →`NOTES.md` → summary)                  | pass                                                                                      | 3     | annotated below; E1 fixture is case-sensitive on Linux, but macOS FS is case-insensitive so E1 must use the truly-missing`note.md` (singular), not `notes.md` |
| E2`twelve times eight` | `[calculator→ERROR, calculator→success]` | fail-as-designed (answered`96` from weights, zero calls)                   | n/a                                                                                       | 1     | under-triggering finding; big-number variant (`12769×83`→`1059827`) passes with tool                                                                          |
| N1 haiku               | `[]`                                     | pass (zero calls)                                                          | n/a                                                                                       | 1     | no over-triggering                                                                                                                                            |
| N2 sky blue            | `[]`                                     | pass (zero calls)                                                          | n/a                                                                                       | 1     | no over-triggering                                                                                                                                            |

Bucket roll-up: single-tool 3/3 · multi-step 2/2 run (M3 skipped) · error-recovery E1 pass + E2 documented fail · no-tool 2/2.

#### Annotated trace 1 — clean multi-step (M2 in-process)

`Read prices.txt, add up all the prices, write the total to total.md:`

1. `read_file(prices.txt)` → `apples 2.50 / bread 3.20 / milk 1.80` — model must ground in the file, not guess.
2. `calculator(2.50 + 3.20 + 1.80)` → `7.5` — exact decimal string passed, no words-to-digits needed here.
3. `write_file(total.md, 'Total: $7.50')` → `Wrote 12 chars` — task's persist step; file on disk confirms end-to-end.
4. Thought `Final Answer: $7.50` with no further calls — correct stop (contrast the `error.txt` no-verify loop in observation 6).

#### Annotated trace 2 — error→recovery (E1 in-process)

`Read note.md (lowercase) and summarize it:`

1. `read_file(note.md)` → `ERROR: file not found: note.md — available files: NOTES.md, prices.txt` — the ERROR-as-observation; the available-files hint is what makes recovery possible.md
2.
3. `read_file(NOTES.md)` → file contents — model visibly corrects the singular→plural/uppercase path from the hint, no new reasoning needed.
4. Thought + `Final Answer` summary of NOTES.md — recovery complete in 3 steps, never a crash.

#### Verdict (1 page, compressed)

- **Wasted steps:** M1 ran a second unprompted `web_search` before writing (5 steps for a 2-search-then-write task — correct but unminimal); the `error.txt` probe (observation 6) never stopped after `write_file` succeeded and burned all 10 steps re-reading. Fix for both: system-prompt rule "after `write_file` succeeds, give Final Answer — don't re-read what you just wrote", plus preferring the first sufficient search result.
- **Description mis-selections:** none observed — but one UNDER-trigger: small-number E2 (`twelve times eight`) answered `96` from weights with zero calls, while the big-number variant forced `calculator`. The calculator description ("pass digits only — spell out words as numbers first") works when the model reaches for the tool; the gap is the model deciding it doesn't need the tool for easy arithmetic. Rewrite candidate: append "Always use this tool for arithmetic — never compute in your head."
- **MCP cost/benefit (measured):** ~926ms per `read_file` via MCP vs ~0ms in-process (fresh subprocess spawn per call), identical output. Benefit: any MCP client can use the tool without importing the codebase; loop.py is wiring-agnostic. Cost: ~1s/call latency + second process to debug. Worth it for shared/reused tools, not for hot-loop-internal helpers. Persistent session (not per-call spawn) is the obvious next optimization.
- **Break-it results (experiment 3):** `--max-steps 1` force-terminates with partial trace (no hang); sandbox `_resolve` rejects `/etc/passwd`-style escapes as `ERROR: path escapes workdir`; MCP spawn failure returns `ERROR: MCP server failed to start` (no traceback). Network-kill mid-`web_search` not run (live DDG worked throughout).

---

## Core experiments (fill in YOUR numbers)

### 1. Task-set pass table ← the core objective

| Task bucket (tasks)    | in-process pass/total                                                | MCP pass/total             | avg steps        | notes (mis-selections, fixes)                   |
| ---------------------- | -------------------------------------------------------------------- | -------------------------- | ---------------- | ----------------------------------------------- |
| single-tool (S1–S3)    | 3/3 (S1`391`; S2 summary; S3 `24.3°C` live)                          | 2/2 (S1, S2 identical)     | 2                | native`tool_calls`, no fake JSON (`qwen3.5:4b`) |
| multi-step (M1–M3)     | 2/2 run (M1`out.md` 5 steps; M2 `total.md`=7.5, 4 steps; M3 skipped) | 1/1 (M2`total_mcp.md`=7.5) | 4–5              | M1 ran an extra unprompted search; M2 clean     |
| error-recovery (E1–E2) | E1 pass (3 steps); E2 fail-as-designed, big-number variant passes    | E1 pass                    | E1: 3; E2-big: 2 | small-number E2 = under-triggering finding      |
| no-tool (N1–N2)        | 2/2 (zero calls both)                                                | n/a                        | 1                | no over-triggering                              |

**What to look for:** single-tool ≈100% both wirings; multi-step is where steps get wasted;
error-recovery is where error-as-observation earns its keep; no-tool catches over-triggering
(a model that calls search for a haiku has a prompting problem).

### 2. Description-driven selection

Deliberately weaken one tool description ("does file stuff") and re-run 3 tasks that need it —
record mis-selection rate. Restore the precise description, re-run. This is your concrete proof that
schemas/descriptions ARE the tool-selection mechanism, not decoration.

### 3. Break it deliberately

- `--max-steps 2` on a 4-step task — confirm forced termination with a readable partial trace, not a hang.
- Kill network mid `web_search` task — the error must appear as an Observation the model reasons about.
- Ask a task referencing a file outside the sandbox (`/etc/passwd`-style) — confirm refusal/containment.
- `--mcp` with the MCP server NOT running — confirm a clean actionable error, not a traceback.

### 4. Model swap

Run the same 3 tasks on two Ollama models (e.g. `qwen3.5:4b` vs a larger `qwen` 7–8b).
Record: native tool-call compliance (did it use `tool_calls` or fake JSON?), steps wasted, pass/fail.
Tool-use ability varies enormously by model — your table makes that concrete.

## Observations worth writing down as you go

1. **Description → selection causality**: the before/after from experiment 2, verbatim.
2. **Native vs fake tool calls**: `qwen3.5:4b` uses native `tool_calls` throughout (S1, M2-variant, E1, big-number E2) — no fake JSON; minimum viable model confirmed.
3. **Error-message design**: `ERROR: file not found: note.md — available files: NOTES.md, prices.txt` rescued E1/M2-variant (model retried corrected name).
4. **MCP hop cost**: ~926ms per `read_file` via MCP vs ~0ms in-process (fresh `python -m react_agent.mcp_server`
   subprocess spawn per call). Same output both wirings (`True` on equality check) — interoperability costs ~1s/call.
5. **Over-triggering instances**: none on N1 (haiku, zero calls). UNDER-triggering instead: small-number E2 answered from weights with zero calls; big numbers force the tool path.
6. **No-verify-then-stop loop (2026-09-27):** `read note.txt → save error in error.txt` wrote the file at step 2 but re-read `error.txt`/`notes.md` until `--max-steps 10` killed it. Fix: prompt rule "after `write_file` succeeds, give Final Answer — don't re-read what you just wrote".

## Definition of done

- [x] The agent completes multi-step tasks end-to-end (M1 `out.md`, M2 `total.md`/`total_mcp.md`) and `read_file` goes through MCP (S2, M2, E1 via `--mcp`).
- [x] Every run has a trace narratable Thought → Action → Observation (annotated M2 + E1 above).
- [x] Task table filled for both wirings; E1 shows visible self-correction (`note.md` ERROR → `NOTES.md`).
- [x] ReAct = model requests / runtime executes / observation loops; schemas drive selection; max-steps prevents hangs; MCP = same tool + ~1s subprocess cost for cross-client reuse.

## Reference material

- huijunwu/learn-claude-code (s01–s03): https://github.com/huijunwu/learn-claude-code
- LangChain DeepAgents Playbook (Level 2–3): https://github.com/sdivyanshu90/LangChain-DeepAgents-Playbook
- Model Context Protocol: https://modelcontextprotocol.io/ · MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Ollama function calling: https://ollama.com/blog/tool-support

## Next

Project B turns this single loop into a TEAM: supervisor + specialists + shared state + human gates (LangGraph).
Keep `tools.py` — the workers reuse these tools.
