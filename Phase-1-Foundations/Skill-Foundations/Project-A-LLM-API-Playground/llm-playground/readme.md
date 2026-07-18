# Ollama CLI Playground

A command-line wrapper around the [Ollama](https://ollama.com) Python client for
experimenting with local LLM generation: sampling parameters, prompt templates,
JSON-constrained output, streaming, and multi-turn chat.

---

## Setup

```bash
pip install -r requirements.txt
ollama serve                     # in a separate terminal, if not already running
ollama pull llama3.2:latest      # or whichever model you want to use
```

## Basic usage

```bash
python cli.py --prompt "Explain recursion in one paragraph"
```

## All flags

| Flag               | Short | Type   | Default               | What it does                                                                                       |
| ------------------ | ----- | ------ | --------------------- | -------------------------------------------------------------------------------------------------- |
| `--prompt`         | `-p`  | str    | —                     | The prompt text. Required unless`--chat` is set.                                                   |
| `--model`          | `-m`  | str    | `llama3.2:latest`     | Which pulled Ollama model to use.                                                                  |
| `--tokens`         |       | flag   | off                   | Print prompt/output token counts and a full timing breakdown. Uses the`generate` endpoint.         |
| `--temperature`    | `-t`  | float  | Ollama default (~0.8) | Randomness of sampling,`0.0`–`2.0`. See below.                                                     |
| `--max-tokens`     | `-n`  | int    | unlimited             | Hard cap on tokens generated (`num_predict`). See below.                                           |
| `--json`           |       | flag   | off                   | Forces JSON output, via both a native decoding constraint and a system-prompt instruction.         |
| `--template`       |       | choice | none                  | Wraps the prompt in a preset system prompt:`zero_shot`, `few_shot`, `cot`.                         |
| `--stream`         | `-s`  | flag   | off                   | Print tokens as they're generated instead of waiting for the full response.                        |
| `--seed`           |       | int    | random                | Fixes the RNG seed so identical settings reproduce identical output.                               |
| `--top-p`          |       | float  | Ollama default (0.9)  | Nucleus sampling — only tokens whose cumulative probability is within this threshold are eligible. |
| `--top-k`          |       | int    | Ollama default (40)   | Only the k highest-probability tokens are eligible, before top-p is applied.                       |
| `--repeat-penalty` |       | float  | Ollama default (1.1)  | Values above 1.0 discourage the model from repeating itself.                                       |
| `--num-ctx`        |       | int    | model default         | Context window size in tokens (prompt + generated output combined).                                |
| `--chat`           |       | flag   | off                   | Drops into an interactive REPL that keeps full conversation history across turns.                  |

---

## How the generation actually works

### Temperature

The model doesn't output a token directly — at every step it produces a raw
score (**logit**) for every token in its vocabulary. Those scores are turned
into a probability distribution with softmax:

```
P(token_i) = exp(logit_i / T) / Σ exp(logit_j / T)
```

`T` is the temperature, and it divides every logit _before_ the softmax:

- **Low T (→ 0):** gaps between logits get exaggerated, so the single
  highest-scoring token dominates. Output becomes close to deterministic
  (greedy decoding).
- **T = 1:** logits pass through unmodified — the model's raw trained
  distribution.
- **High T (> 1):** gaps between logits shrink, flattening the distribution.
  Lower-probability tokens become competitive → more variety, but higher risk
  of incoherence at the extreme.

Temperature isn't the whole story, though. Ollama also applies **top-k** and
**top-p** filtering on top of the temperature-scaled distribution (defaults
40 and 0.9), so sampling is always restricted to a shortlist of plausible
tokens even at high temperature. This script now exposes both as flags so you
can isolate their effects — e.g. high temperature with a tight `top-k` stays
much more coherent than high temperature with an open `top-k`.

### `--max-tokens` (`num_predict`)

This is a **hard cutoff**, not a soft budget. The server-side loop is
roughly:

1. Generate one token.
2. If it's an end-of-sequence token → stop naturally.
3. If the token count has hit `num_predict` → **stop immediately**, mid-word
   if necessary.
4. Otherwise, generate the next token and repeat.

So `--max-tokens 20` on a request that would naturally take 200 tokens gives
you the first 20 tokens and nothing else — no graceful wrap-up.

This is a **different limit** from `--num-ctx` (context window): `num_ctx` is
the total tokens the model can attend to at once (prompt + response combined);
`num_predict`/`--max-tokens` only caps how much this one call is allowed to
generate. You can hit the context window even with `--max-tokens` unset.

### Two different endpoints

- `ollama.generate()` — raw completion. You pass `prompt` and `system` as
  separate plain strings; there's no chat templating. This is the only path
  in this script that returns token-count metadata (`prompt_eval_count`,
  `eval_count`) and per-phase timing, which is why `--tokens` uses it.
- `ollama.chat()` — takes a structured `messages` list and applies the
  model's chat template (role tags, special tokens) for you. Used for normal,
  streaming, and REPL mode. Doesn't return token-count metadata, even when
  streaming.

### JSON mode

Two mechanisms are stacked for reliability:

1. A system-prompt instruction telling the model to respond with JSON only.
2. Ollama's native `format="json"` parameter, which constrains decoding
   directly at the token level rather than just hoping the model complies.

Even with both, models sometimes wrap output in ` ```json ` fences anyway —
`_handle_json_response()` strips those before calling `json.loads()`, and
exits with the raw text on stderr if parsing still fails.

---

## What changed from the original version

- Added `--seed` for reproducible sampling — fix it to compare other
  parameters (like temperature) without random noise confounding the result.
- Added `--top-p`, `--top-k`, `--repeat-penalty`, `--num-ctx` as flags —
  previously silently using Ollama's defaults with no way to inspect or tune
  them.
- `--json` now uses native `format="json"` decoding in addition to the
  system-prompt instruction, instead of relying on the system prompt alone.
- Added `--chat` — an interactive multi-turn REPL. Every previous mode was
  stateless (one call, one response); this persists `messages` across turns.
- Added `_call_ollama()` error-handling wrapper — catches connection failures
  (Ollama not running) and model/response errors (e.g. model not pulled) with
  actionable messages instead of a raw traceback.
- `--tokens` mode now prints the full timing breakdown (`load_duration`,
  `prompt_eval_duration`, `eval_duration`) alongside `total_duration`, not
  just the total.
- Temperature is validated at parse time (`0.0`–`2.0`) instead of failing
  later inside Ollama.
- `--prompt` is no longer unconditionally required — it's optional when
  `--chat` is set, since the REPL takes input interactively instead.

---

## Ideas to explore further

1. **Isolate temperature's effect** by fixing `--seed` and sweeping
   temperature values on the same prompt — you'll see the same starting
   point diverge more as T increases.
2. **Cross `--temperature` with `--top-k`**: try high temperature with a
   small top-k (e.g. 5) vs. a large one (e.g. 100) and compare coherence.
3. **Deliberately overflow `--num-ctx`** with a very long prompt and observe
   how Ollama truncates or behaves at the boundary.
4. **Compare token counts** between `generate` (`--tokens`) and what `chat`
   would consume for equivalent content — `generate` skips chat-template
   wrapping, so prompt token counts can differ.
5. **Extend `--chat`** to support saving/loading conversation history to a
   file, so you can resume a session later.
6. **Add a `--num-ctx` auto-probe** that binary-searches for the actual
   context limit of a given model on your hardware.
7. **Try structured-output schemas**: Ollama's `format` parameter can accept
   a full JSON schema (not just `"json"`), which constrains the _shape_ of
   the output, not just that it's valid JSON — worth testing against models
   of different sizes to see how well they follow it.

# Here's a set of commands that isolate one variable at a time, so you can actually see cause and effect instead of just getting different outputs each run.

## 1. Temperature — same prompt, three extremes

```bash
python ollama_playground.py -p "Write a two-sentence story about a lighthouse keeper." -t 0.0
python ollama_playground.py -p "Write a two-sentence story about a lighthouse keeper." -t 0.8
python ollama_playground.py -p "Write a two-sentence story about a lighthouse keeper." -t 1.8
```

Run the `-t 0.0` one twice — it should come back nearly identical both times (greedy decoding). Run `-t 1.8` a few times — watch it get looser, and eventually start losing coherence.

## 2. Isolate temperature from randomness with `--seed`

```bash
python ollama_playground.py -p "Describe a color that doesn't exist." -t 0.3 --seed 42
python ollama_playground.py -p "Describe a color that doesn't exist." -t 1.5 --seed 42
```

Same seed, different temperature. This shows temperature's effect on its own — without `--seed`, you can't tell if a difference is from temperature or just random luck.

## 3. `--max-tokens` hard cutoff

```bash
python ollama_playground.py -p "Explain how a car engine works in detail." -n 15
```

Watch it stop mid-sentence, exactly at the cutoff — no wrap-up, no ellipsis.

## 4. `top-k` reining in a high temperature

```bash
python ollama_playground.py -p "Continue this story: The door creaked open and" -t 1.7 --top-k 100
python ollama_playground.py -p "Continue this story: The door creaked open and" -t 1.7 --top-k 3
```

Same wild temperature, but the second one stays far more coherent because it's only choosing between 3 candidate tokens each step.

## 5. `--tokens` — see the accounting and timing

```bash
python ollama_playground.py -p "What is the capital of France?" --tokens
```

Check `prompt_eval_count` vs `eval_count`, and compare `prompt_eval_duration` vs `eval_duration` — prompt processing is usually much faster per-token than generation.

## 6. JSON mode

```bash
python ollama_playground.py -p "Extract the name and age: John is 34 years old." --json
```

Should print clean, parsed JSON. Try it without `--json` on the same prompt to see the difference in raw output.

## 7. Templates — same question, three framings

```bash
python ollama_playground.py -p "Classify the sentiment: The food was cold but the service was excellent." --template few_shot
python ollama_playground.py -p "If a train leaves at 3pm going 60mph, and another leaves at 4pm going 80mph from 100 miles behind, when do they meet?" --template cot
```

The `cot` one should show visible step-by-step reasoning before a final `ANSWER:` line — compare it to running the same prompt with no `--template` at all.

## 8. Streaming vs waiting

```bash
python ollama_playground.py -p "Write a short poem about autumn." --stream
```

Mostly a UX difference, but useful to watch generation speed token-by-token rather than getting one static block.

## 9. `--repeat-penalty` on a prompt prone to looping

```bash
python ollama_playground.py -p "List synonyms for 'happy', repeating as many as you can think of." --repeat-penalty 1.0
python ollama_playground.py -p "List synonyms for 'happy', repeating as many as you can think of." --repeat-penalty 1.5
```

At `1.0` (no penalty) small models sometimes get stuck looping the same word or phrase. `1.5` should force more variety.

## 10. Overflow `--num-ctx` on purpose

```bash
python ollama_playground.py -p "$(python3 -c "print('Summarize this. ' + 'The quick brown fox jumps over the lazy dog. ' * 300)")" --num-ctx 512 --tokens
```

This builds a prompt way longer than a 512-token context window can hold. Watch how `prompt_eval_count` and the response behave when the input exceeds `num_ctx` — good way to see truncation happen instead of just reading about it.

## 11. Chat REPL — test whether it actually remembers

```bash
python ollama_playground.py --chat
```

Then type:

```
you> My name is Akshat and I have two cats.
you> What's my name, and how many pets do I have?
```

The second answer should correctly reference the first turn — that's the multi-turn state working. Compare this by running two separate `-p` calls instead (no `--chat`) and asking the second question cold — it'll have no idea what you're referring to.
