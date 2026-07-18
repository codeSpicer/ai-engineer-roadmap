#!/usr/bin/env python3
"""LLM API Playground — Ollama CLI

Supports:
  --prompt           Prompt text (required unless --chat)
  --model            Model name (default: llama3.2:latest)
  --tokens           Print token usage counts and timing breakdown
  --temperature      Generation temperature (0.0-2.0)
  --max-tokens       Max tokens to generate (num_predict)
  --json             Force JSON output (native format + system prompt)
  --template         Prompt template: zero_shot, few_shot, cot
  --stream           Stream output token by token
  --seed             Fixed seed for reproducible sampling
  --top-p            Nucleus sampling threshold (0.0-1.0)
  --top-k            Top-k sampling cutoff
  --repeat-penalty   Penalty applied to repeated tokens (>1.0 discourages repeats)
  --num-ctx          Context window size in tokens
  --chat             Interactive multi-turn REPL (keeps conversation history)

See README.md for a full explanation of what each flag controls.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import ollama

# ── Prompt templates (Phase 4) ──────────────────────────────────────────────

TEMPLATES: Dict[str, Dict[str, str]] = {
    "zero_shot": {
        "system": "You are a helpful assistant.",
        "user": "{prompt}",
    },
    "few_shot": {
        "system": (
            "Here are examples of the task:\n\n"
            'Q: "Classify the sentiment: I love this product!"\n'
            'A: {"sentiment": "positive", "confidence": 0.95}\n\n'
            'Q: "Classify the sentiment: This is terrible."\n'
            'A: {"sentiment": "negative", "confidence": 0.92}\n\n'
            "Now answer the user's query in the same format."
        ),
        "user": "{prompt}",
    },
    "cot": {
        "system": "Think step by step before giving your final answer. "
        "Show your reasoning, then provide the answer on a new line "
        'prefixed with "ANSWER:".',
        "user": "{prompt}",
    },
}


# ── Argument parsing ────────────────────────────────────────────────────────

def _temperature_type(value: str) -> float:
    """Validates temperature falls within Ollama's sane 0.0-2.0 range."""
    f = float(value)
    if not 0.0 <= f <= 2.0:
        raise argparse.ArgumentTypeError(
            f"temperature must be between 0.0 and 2.0, got {f}"
        )
    return f


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LLM API Playground — Chat with Ollama"
    )
    parser.add_argument(
        "--prompt", "-p", type=str, default=None,
        help="The prompt to send to the model (required unless --chat)",
    )
    parser.add_argument(
        "--model", "-m", type=str, default="llama3.2:latest",
        help="Ollama model name (default: llama3.2:latest)",
    )
    parser.add_argument(
        "--tokens", action="store_true",
        help="Print token usage counts and timing breakdown (uses generate endpoint)",
    )
    parser.add_argument(
        "--temperature", "-t", type=_temperature_type, default=None,
        help="Generation temperature (0.0 to 2.0)",
    )
    parser.add_argument(
        "--max-tokens", "-n", type=int, default=None,
        help="Maximum tokens to generate (num_predict)",
    )
    parser.add_argument(
        "--json", dest="json_mode", action="store_true",
        help="Force JSON output (native Ollama format + system prompt)",
    )
    parser.add_argument(
        "--template", choices=["zero_shot", "few_shot", "cot"],
        default=None,
        help="Apply a prompt template",
    )
    parser.add_argument(
        "--stream", "-s", action="store_true",
        help="Stream output token by token",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Fixed seed for reproducible sampling (same seed + same options = same output)",
    )
    parser.add_argument(
        "--top-p", type=float, default=None,
        help="Nucleus sampling threshold (0.0-1.0)",
    )
    parser.add_argument(
        "--top-k", type=int, default=None,
        help="Top-k sampling cutoff (only the k highest-probability tokens are considered)",
    )
    parser.add_argument(
        "--repeat-penalty", type=float, default=None,
        help="Penalty for repeated tokens; >1.0 discourages repetition",
    )
    parser.add_argument(
        "--num-ctx", type=int, default=None,
        help="Context window size in tokens (prompt + generated output combined)",
    )
    parser.add_argument(
        "--chat", action="store_true",
        help="Interactive multi-turn REPL that keeps conversation history",
    )
    args = parser.parse_args(argv)

    if not args.chat and not args.prompt:
        parser.error("--prompt is required unless --chat is set")

    return args


# ── Build messages ──────────────────────────────────────────────────────────

def build_messages(
    prompt: str,
    template: Optional[str],
    json_mode: bool,
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []

    system_parts: List[str] = []

    if template:
        system_parts.append(TEMPLATES[template]["system"])

    if json_mode:
        system_parts.append(
            "Respond with valid JSON only. Do not include any other text, "
            "markdown fences, or explanations."
        )

    if system_parts:
        messages.append({"role": "system", "content": "\n\n".join(system_parts)})

    if template:
        messages.append({
            "role": "user",
            "content": TEMPLATES[template]["user"].format(prompt=prompt),
        })
    else:
        messages.append({"role": "user", "content": prompt})

    return messages


# ── Build options ───────────────────────────────────────────────────────────

def build_options(args: argparse.Namespace) -> Dict[str, Any]:
    """Collects every explicitly-set sampling/runtime flag into Ollama's options dict.

    Only flags the user actually passed are included — anything left as None
    is omitted so Ollama falls back to its own defaults for that parameter.
    """
    options: Dict[str, Any] = {}
    if args.temperature is not None:
        options["temperature"] = args.temperature
    if args.max_tokens is not None:
        options["num_predict"] = args.max_tokens
    if args.seed is not None:
        options["seed"] = args.seed
    if args.top_p is not None:
        options["top_p"] = args.top_p
    if args.top_k is not None:
        options["top_k"] = args.top_k
    if args.repeat_penalty is not None:
        options["repeat_penalty"] = args.repeat_penalty
    if args.num_ctx is not None:
        options["num_ctx"] = args.num_ctx
    return options


# ── Error-handling wrapper ──────────────────────────────────────────────────

def _call_ollama(fn, **kwargs):
    """Runs an ollama client call with friendly, actionable error messages."""
    try:
        return fn(**kwargs)
    except ollama.ResponseError as e:
        print(f"[!] Ollama returned an error: {e.error}", file=sys.stderr)
        if getattr(e, "status_code", None) == 404:
            print(
                "    Hint: the model may not be pulled yet — try "
                f"`ollama pull {kwargs.get('model', '<model>')}`.",
                file=sys.stderr,
            )
        sys.exit(1)
    except ConnectionError:
        print(
            "[!] Could not connect to Ollama. Is the server running? "
            "Try `ollama serve` in another terminal.",
            file=sys.stderr,
        )
        sys.exit(1)


# ── Token mode (Phase 1) ────────────────────────────────────────────────────

def run_with_tokens(
    model: str,
    messages: List[Dict[str, str]],
    options: Dict[str, Any],
    json_mode: bool,
) -> None:
    response = _call_ollama(
        ollama.generate,
        model=model,
        prompt=messages[-1]["content"],
        system=messages[0]["content"] if messages and messages[0]["role"] == "system" else "",
        options=options,
        format="json" if json_mode else None,
        stream=False,
    )
    print(response["response"])
    print()
    print(f"Prompt tokens:    {response.get('prompt_eval_count', 'N/A')}")
    print(f"Output tokens:    {response.get('eval_count', 'N/A')}")

    # Full timing breakdown — Ollama reports each phase separately, all in nanoseconds.
    load = response.get("load_duration")
    prompt_eval = response.get("prompt_eval_duration")
    eval_dur = response.get("eval_duration")
    total = response.get("total_duration")
    if load is not None:
        print(f"Model load time:  {load / 1e9:.2f}s")
    if prompt_eval is not None:
        print(f"Prompt eval time: {prompt_eval / 1e9:.2f}s")
    if eval_dur is not None:
        print(f"Generation time:  {eval_dur / 1e9:.2f}s")
    if total is not None:
        print(f"Total duration:   {total / 1e9:.2f}s")


# ── Stream mode ─────────────────────────────────────────────────────────────

def run_stream(
    model: str,
    messages: List[Dict[str, str]],
    options: Dict[str, Any],
    json_mode: bool,
) -> None:
    stream = _call_ollama(
        ollama.chat,
        model=model,
        messages=messages,
        options=options,
        format="json" if json_mode else None,
        stream=True,
    )
    for chunk in stream:
        content = chunk["message"]["content"]
        print(content, end="", flush=True)
    print()


# ── Normal mode ─────────────────────────────────────────────────────────────

def run_normal(
    model: str,
    messages: List[Dict[str, str]],
    options: Dict[str, Any],
    json_mode: bool,
) -> None:
    response = _call_ollama(
        ollama.chat,
        model=model,
        messages=messages,
        options=options,
        format="json" if json_mode else None,
        stream=False,
    )
    content = response["message"]["content"]

    if json_mode:
        _handle_json_response(content)
    else:
        print(content)


# ── Chat REPL mode ───────────────────────────────────────────────────────────

def run_chat_repl(
    model: str,
    template: Optional[str],
    json_mode: bool,
    options: Dict[str, Any],
) -> None:
    """Interactive multi-turn chat. Unlike the other modes, this keeps the
    full message history and re-sends it on every turn, so the model has
    conversational context. Type 'exit' or 'quit' to leave.
    """
    messages: List[Dict[str, str]] = []

    system_parts: List[str] = []
    if template:
        system_parts.append(TEMPLATES[template]["system"])
    if json_mode:
        system_parts.append(
            "Respond with valid JSON only. Do not include any other text, "
            "markdown fences, or explanations."
        )
    if system_parts:
        messages.append({"role": "system", "content": "\n\n".join(system_parts)})

    print("Chat mode — type 'exit' or 'quit' to leave, Ctrl+C to abort.\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        stream = _call_ollama(
            ollama.chat,
            model=model,
            messages=messages,
            options=options,
            format="json" if json_mode else None,
            stream=True,
        )

        print("model> ", end="", flush=True)
        full_reply = ""
        for chunk in stream:
            piece = chunk["message"]["content"]
            print(piece, end="", flush=True)
            full_reply += piece
        print("\n")

        messages.append({"role": "assistant", "content": full_reply})


# ── JSON handling (Phase 3) ─────────────────────────────────────────────────

def _handle_json_response(content: str) -> None:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()

    try:
        parsed = json.loads(stripped)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print("[!] Failed to parse JSON. Raw response:", file=sys.stderr)
        print(content, file=sys.stderr)
        sys.exit(1)


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    options = build_options(args)

    if args.chat:
        run_chat_repl(args.model, args.template, args.json_mode, options)
        return

    messages = build_messages(args.prompt, args.template, args.json_mode)

    if args.tokens:
        run_with_tokens(args.model, messages, options, args.json_mode)
    elif args.stream:
        run_stream(args.model, messages, options, args.json_mode)
    else:
        run_normal(args.model, messages, options, args.json_mode)


if __name__ == "__main__":
    main()