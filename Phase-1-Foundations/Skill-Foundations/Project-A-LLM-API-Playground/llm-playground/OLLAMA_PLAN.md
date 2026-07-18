# LLM API Playground — Ollama Plan

## Phase 0: Setup

1. Verify Ollama works — pull a model and test it:
   ```
   ollama pull llama3.2
   ollama run llama3.2 "Hello, what is 2+2?"
   ```
2. Set up the project:
   ```
   mkdir llm-playground && cd llm-playground
   python3 -m venv .venv && source .venv/bin/activate
   pip install ollama
   ```
3. Create `cli.py` — start with a single function that calls `ollama.chat()` and prints the response.

## Phase 1: Core CLI (steps 2–3 from README)

- CLI takes `--prompt "your text"` → calls Ollama → prints response
- Add `--tokens` flag that uses `ollama.generate()` with `stream=False` to extract `eval_count`/`prompt_eval_count` from the response metadata (Ollama gives token counts natively)
- No cost needed — Ollama is free, but you can note the counts

## Phase 2: Generation control (step 4)

- Add `--temperature` and `--max-tokens` flags
- Ollama accepts `options={"temperature": 0.7, "num_predict": 256}` in the chat call
- Test the same prompt at temperature 0 vs 1.5 and observe the difference

## Phase 3: Structured output (step 5)

- Add `--json` flag that appends `"Respond with valid JSON only"` to the system prompt
- Parse the response with `json.loads()`, handle failures gracefully
- Ollama doesn't have native JSON mode (unlike OpenAI), so you'll learn why prompt engineering matters here

## Phase 4: Prompt patterns (step 6)

- Save 3 JSON templates: zero-shot, few-shot, chain-of-thought
- Example format:
  ```json
  {
    "zero_shot": { "system": "You are helpful.", "user": "{prompt}" },
    "few_shot": { "system": "Here are examples...", "user": "{prompt}" },
    "cot": { "system": "Think step by step.", "user": "{prompt}" }
  }
  ```
- Add `--template zero_shot|few_shot|cot` flag and compare outputs for the same task

## Ollama-specific notes

- **Ollama chat API**: `ollama.chat(model="llama3.2", messages=[...], options={...})`
- **Token counts**: Available in the response dict as `prompt_eval_count` and `eval_count` (no separate tokenizer needed)
- **No API key**: Ollama runs locally, so the `ollama` Python package connects to `http://localhost:11434` by default
- **It's stateless**: Each call is independent — no conversation memory unless you maintain the message list yourself
