# Interview Questions — Guardrails Project B: Programmable Dialog / Safety Rails

Complete the project, then quiz yourself. Answers are detailed.

## Phase 3 — Quality & Safety · Guardrails · Project B

**Q1. What are the five rail categories in NeMo Guardrails, and what does each control?**
1. **Input rails**: filter/block the user's incoming message (jailbreak detection,
   off-topic checks, PII) before it reaches the model.
2. **Dialog rails**: control the *flow* of conversation — allowed topics, transitions,
   and Colang-defined dialog flows that keep the bot on an approved path.
3. **Retrieval rails**: filter/guard the context chunks a RAG pipeline retrieves before
   they're passed to the model (block unsafe or irrelevant context).
4. **Output rails**: vet the model's response (toxicity, policy compliance) before return.
5. **Execution rails**: govern actions/tools the bot can trigger (prevent unsafe calls).

Together they wrap the bot on every boundary — in, during, retrieved, out, and acting.

**Q2. What is a dialog rail and how does it resist jailbreaks / off-topic drift?**
A dialog rail enforces a defined conversation structure (Colang `.co` flows declaring
allowed intents and transitions). If a user tries to derail ("ignore previous
instructions, do X"), the rail detects the off-topic/jailbreak intent and redirects or
refuses per the configured flow. The bot stays on its approved path instead of
following an injected instruction — which a plain prompt guard might miss because the
attack is conversational, not just a keyword.

**Q3. What is a retrieval rail and why is it valuable in RAG?**
In RAG, the model's answer is only as safe as its retrieved context. A retrieval rail
inspects the chunks returned by the vector DB and filters out unsafe, off-policy, or
irrelevant passages before they reach the prompt. This stops the model from being
poisoned by a bad retrieved chunk (a real attack surface: someone plants malicious text
in a indexed doc). It's guardrails applied to the *knowledge*, not just the words.

**Q4. How do Colang flows and config.yml work together?**
`config.yml` declares the model and rail configurations (which rails are active, models
to use). The `.co` (Colang) file defines the dialog flows — the allowed intents,
responses, and transitions between conversation states. At runtime, `LLMRails` loads
both and orchestrates: routing user input through input/dialog/retrieval/output rails
around the model call. You edit YAML/Colang, not Python, to change behavior — that's the
"programmable" part.

**Q5. How is this different from Project A's validator approach?**
Project A wraps the model with discrete programmatic validators (PII, toxicity, regex) —
imperative guards you code. Project B uses a **declarative, flow-based** system
(NeMo) where safety is expressed as dialog/retrieval/execution *rails* in config. B is
broader (covers dialog flow and retrieval/execution, not just I/O validation) and more
about conversation control; A is more about point validators. They're complementary
layers.

**Q6. Why does the project say "test adversarial prompts and confirm the bot stays on the approved path"?**
Because the definition of done is behavioral: the bot must *refuse* off-topic/jailbreak
attempts and follow the defined flow. You prove it by actually attacking it (prompt
injection strings, topic switches) and verifying the rails catch each. If an attack
slips through, the rail config is incomplete — that's the test, not just "did it run."
