# Interview Questions — Project A: LLM API Playground

Complete the project, then quiz yourself. Answers are detailed — read them, then
close the file and re-explain in your own words.

## Phase 1 — Foundations · Project A

**Q1. What is tokenization and why does it matter for cost and context limits?**
Tokenization is the process of splitting raw text into tokens — the atomic units a
model actually reads and generates. Tokens are usually subword pieces (not whole
words): "embedding" might become "embed" + "ding", and "unbelievable" might become
"un" + "believ" + "able". The exact split depends on the model's trained tokenizer
(BPE, WordPiece, or SentencePiece).

It matters for two concrete reasons. First, **cost**: providers bill per token, and
the token count = input tokens + output tokens. If you don't understand tokenization
you can't estimate or control spend — a verbose system prompt quietly multiplies
across every request. Second, **context limits**: every model has a fixed context
window (e.g. 8k, 32k, 128k tokens). Everything — system prompt, history, retrieved
context, and the generation — must fit. If you overflow, the model truncates or
errors. Counting tokens lets you design prompts that fit and catch bloat early.

**Q2. Explain temperature, top-p, and top-k, and how they interact.**
These three parameters control the randomness of generation, and they layer on top
of each other.

- **Temperature** rescales the model's raw output logits before softmax: P(token) =
  exp(logit/T) / Σ exp(logit_j/T). At T→0 the distribution collapses toward the
  single highest logit (greedy, near-deterministic). At T=1 the raw trained
  distribution passes through. At T>1 gaps shrink, flattening the distribution so
  low-probability tokens compete (more variety, eventually incoherent).
- **Top-k** truncates the vocabulary to only the k highest-probability tokens before
  sampling. k=1 is greedy; large k is barely a constraint.
- **Top-p (nucleus sampling)** keeps the smallest set of tokens whose cumulative
  probability reaches p (e.g. 0.9), then samples from those.

Interaction: temperature reshapes the distribution's shape; top-k then top-p cut it
down to a shortlist; finally we sample from that shortlist. So high temperature with
a tight top-k stays coherent (only 3 candidates), while high temperature with open
top-k diverges wildly. You tune them together, not independently.

**Q3. What's the difference between `--max-tokens` (num_predict) and `--num-ctx` (context window)?**
They are completely different limits. `--max-tokens` (Ollama's num_predict) is a
**hard cap on how many new tokens this one call is allowed to generate**. When hit,
generation stops immediately — mid-word if necessary, with no graceful wrap-up. It
does not bound the input.

`--num-ctx` (context window) is the **total tokens the model can attend to at once**:
your prompt + system message + chat history + the generated response, all combined.
If your prompt alone exceeds num_ctx, the model must truncate or error. You can blow
the context window even with max-tokens unset, and you can hit max-tokens while still
well under the context window. Understanding this distinction is essential for
debugging "why did my response get cut off" vs "why did my input get ignored."

**Q4. What is the role of system vs user messages?**
In a chat template, **system messages** carry persistent instructions that shape the
model's behavior, persona, and constraints for the whole conversation (e.g. "You are
a terse SQL expert"). They're set once and rarely change per turn. **User messages**
are the actual turn input from the human. There may also be assistant messages
(history) and tool messages (function results). The model's chat template wraps each
with role tags and special tokens so the model knows who is speaking. Getting the
separation right matters: putting behavior in the system message (not repeating it in
every user turn) saves tokens and keeps instructions stable.

**Q5. How do you force valid JSON output, and why is relying on the prompt alone unreliable?**
Two mechanisms stacked: (1) a system-prompt instruction telling the model to respond
with JSON only, and (2) a native decoding constraint (e.g. Ollama's `format="json"`,
or `response_format` in the OpenAI API) that restricts token selection at the decoding
level so invalid JSON simply cannot be produced.

Prompt-only reliance is unreliable because the model is still a probabilistic
next-token predictor — it may wrap output in ```json fences, add commentary, or
deviate under pressure. Decoding-level constraints enforce structure token-by-token,
which is far stronger. Even with both, models sometimes add fences, so you still strip
them and `json.loads()` defensively, failing gracefully on parse error. For shaped
output (not just "valid JSON"), pass a full JSON schema so the model is constrained to
the right keys and types.

**Q6. Why does the same prompt give different outputs, and how do you make it reproducible?**
Because sampling is stochastic. Unless you force greedy decoding (temperature 0,
top-k 1), each generated token is drawn from a probability distribution, so runs
diverge. Even "identical" settings vary because the RNG seed defaults to random.

To reproduce: fix the **seed** (`--seed 42`) so the RNG is deterministic, and pin
temperature/top-p/top-k. With a fixed seed and greedy or low-temperature sampling, the
same prompt yields the same output. This is why the playground exposes `--seed` — it
lets you isolate one variable (e.g. sweep temperature) without random noise
confounding the comparison.

**Q7. What are zero-shot, few-shot, and chain-of-thought prompting, and when does each help?**
- **Zero-shot**: ask directly, no examples. Best when the task is well within the
  model's training (classification, simple Q&A).
- **Few-shot**: prepend a few (input, output) exemplars in the prompt to demonstrate
  the desired pattern. Helps when format/style matters or the task is unusual — the
  model imitates the examples.
- **Chain-of-thought (CoT)**: instruct or demonstrate step-by-step reasoning ("think
  step by step") so the model reasons before answering. Dramatically improves
  multi-step math/logic tasks where jumping to the answer fails.

The playground's `--template` flag wraps the prompt in these framings so you can
compare them on the same task — a direct way to feel when CoT actually changes the result.
