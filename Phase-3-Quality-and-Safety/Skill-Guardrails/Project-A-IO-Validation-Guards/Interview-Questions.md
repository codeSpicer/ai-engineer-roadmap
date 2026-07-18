# Interview Questions — Guardrails Project A: Input/Output Validation Guards

Complete the project, then quiz yourself. Answers are detailed.

## Phase 3 — Quality & Safety · Guardrails · Project A

**Q1. What is the difference between input and output validation, with examples?**
- **Input validation** runs *before* the model sees the user message. Examples: PII
  detection (block/redact names, emails), jailbreak-pattern regex, toxicity screening,
  competitor-mention blocking, schema/format enforcement on the incoming request.
- **Output validation** runs *after* generation, before the response is returned.
  Examples: toxicity filter on the reply, competitor-check, format/regex enforcement
  (must be valid JSON), length limits.

The split matters: input guards protect the model and your costs; output guards protect
the end user from a bad generation. Defense in depth = both.

**Q2. What are fail actions — reject, repair, reask — and when do you pick each?**
- **Reject**: block and return an error. Use when the input is unsafe/illegal (jailbreak,
  PII you can't process). Clear boundary, no model call wasted.
- **Repair**: auto-fix and continue. Use when the issue is mechanical — e.g. redact PII,
  strip disallowed content, reformat to schema. Keeps the flow smooth.
- **Reask**: send the model a corrected prompt (e.g. "respond in valid JSON") and retry.
  Use when the output was almost right but malformed.

Choice depends on severity and recoverability: unrecoverable → reject; fixable → repair;
recoverable with another attempt → reask.

**Q3. Why enforce structured-output (schema) at the guard layer too, not just the prompt?**
Prompt-level JSON requests are suggestions the model can ignore. The guard layer
enforces the schema *downstream* — if generation drifts, the guard rejects or repairs it.
This is defense in depth: even a prompt-injection or a model glitch that breaks format
gets caught before it reaches the user or a downstream system that trusted the contract.

**Q4. What is PII detection and why is it a guardrail concern?**
PII (personally identifiable information — names, emails, phone numbers, IDs) leaking
into prompts or responses creates privacy and compliance risk (GDPR, etc.). A guardrail
detects PII and either rejects the input or redacts it (repair) before processing or
before returning output. It's a core AI-safety/ethics control, not just formatting.

**Q5. How would you expose this as a REST service with FastAPI?**
Wrap the guarded LLM call in a FastAPI endpoint (e.g. `POST /generate`). The handler
runs input guards → calls the model → runs output guards → returns the validated
response (or a 4xx on reject). Test with adversarial inputs (jailbreak strings, PII,
bad JSON) to confirm unsafe ones are blocked/repaired and safe ones pass through. This
makes the guardrail a reusable, production-shaped component.

**Q6. How does this map to roadmap.sh's AI Safety & Ethics node?**
roadmap.sh lists prompt injection, bias, and privacy under AI Safety & Ethics. This
project turns those *concepts* into *hands-on enforcement*: you don't just read about
prompt injection — you build validators that detect and block it. That practical layer
is what makes the node interview-credible.
