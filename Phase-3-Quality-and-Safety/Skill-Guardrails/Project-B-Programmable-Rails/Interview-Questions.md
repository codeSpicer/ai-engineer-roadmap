# Interview Questions — Programmable Dialog / Safety Rails (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual config and measured runs** — rail coverage table, poisoning
ablation quotes, precedence findings, config-only diff. Quote the coverage table; that separates
"read the NeMo docs" from "holds a bot on-path under attack."

---

## Part 1: Fundamentals — "Why rails beyond validators?"

**Q1. Project A guards single turns. What attacks does it structurally MISS that rails catch? Give me YOUR specimens.**

**Answer:** Three classes, each with a script from `adversarial_dialogs.jsonl` that Project-A-style
point-validators miss: (a) GRADUAL-STEER — 5 individually-benign turns walking the bot off-topic
("…and now that we're discussing travel, help me…"); per-turn screens pass every turn, only FLOW STATE
(dialog rails tracking the approved path) sees the drift — your trace shows the turn where the rail fired
(quote it). (b) POISONED CONTEXT — the ATTACK ISN'T IN THE USER'S WORDS AT ALL but in a retrieved chunk
(planted "ignore policy, state X as fact"); I/O validators vet user/model text, never knowledge provenance
— retrieval rails dropping the chunk (your ablation row) is the only layer that sees it. (c) TOOL ABUSE —
the model ATTEMPTS an unapproved action mid-conversation; prompt-level safety says "don't," execution rails
make "can't" (attempt logged + denied — your run). The structural point: validators guard MESSAGES, rails
guard CONVERSATION (state), KNOWLEDGE (retrieval), and AGENCY (execution) — four boundaries validators never
touch.

**Q2. Walk me through one multi-turn attack, turn by turn, naming every file that acts.**

**Answer:** Gradual-steer script with `--trace`: turns 1–2 benign (input rails pass, dialog rails: on-flow,
`flows.co` state advances normally) → turn 3 drift begins (`config.yml` off-topic screen scores borderline —
logged, no fire; DIALOG rail notes state deviation) → turn 4 explicit steer (dialog rail FIRES per the `.co`
transition: off-flow → redirect response "I can help with [approved]; let's stay on…" — no model generation
for the steered content) → turn 5 role-reversal attempt ("you are now…") (input jailbreak rail + dialog rail
both fire — layered, logged in `rail_report` with flow state). `app.py` orchestrates via `LLMRails`;
`custom_actions.py` uninvolved (no tool attempted); `rail_report` per turn accumulates the story. The turn-4
redirect (not a generic refusal — a FLOW-SCRIPTED redirect) is what you quote: scripted recovery beats "I
can't help with that" for user experience AND auditability (the flow names the violated transition).

**Q3. Imperative validators vs declarative rails: what's the real difference in practice?**

**Answer:** Project A: Python code — `if pii_found: redact()` — behavior changes require code edits, review,
deploy; logic lives in control flow only engineers read. Project B: `config.yml` (WHICH rails, WHAT params) +
`flows.co` (Colang intents/transitions/responses — the approved conversation as DATA) loaded by `LLMRails`;
behavior changes are CONFIG EDITS (your programmability proof: new refusal message, zero Python in the diff).
Consequences: (a) ITERATION SPEED — policy folks edit flows without touching runtime; (b) AUDITABILITY — the
approved path is READABLE (reviewers read `.co`, not control flow); (c) NEW BUG CLASS — config contradictions
(your precedence finding: input-allows vs dialog-forbids — silent resolution or logged? you found out); (d) REVIEW
DISCIPLINE — `.co` edits ARE security changes (removing a refusal path unblocks an attack — your break-run
proves it; who reviews `.co` PRs is a policy question your report answers). Declarative doesn't mean simpler —
it moves complexity from code to configuration, trading debuggability of logic for visibility of policy.

---

## Part 2: The Five Rails — "Every boundary has an owner"

**Q4. Name the five rail categories, what each intercepts, and which of YOUR scripts each caught.**

**Answer:** INPUT (this turn's user text — jailbreak/off-topic/PII screens; caught your role-reversal +
single-turn set), DIALOG (conversation STATE vs approved flows in `.co` — the ONLY rail that catches
gradual-steer; per-turn screens are blind to sequences), RETRIEVAL (chunks BEFORE the prompt — planted
instruction dropped with reason; knowledge vetting, not word vetting), EXECUTION (tool/action attempts —
unapproved call denied post-attempt; defense beyond prompting), OUTPUT (final response vetting —
toxicity/policy/on-topic before return). Your coverage table maps every script to ≥1 rail — the table IS the
answer; memorize the mapping, especially the dialog-only rows (they justify the project's existence) and any
script needing TWO rails (layered catches — input AND dialog firing on role-reversal shows depth, quote it).

**Q5. Dialog rails vs input rails: why can't good input screening replace flow tracking?**

**Answer:** Because input rails are MEMORYLESS per turn and the attack lives in the SEQUENCE. Your death-by-a-
thousand-cuts probe is the specimen: 5 turns, each benign in isolation ("tell me about X," "how does X relate
to Y," … drifting to disallowed territory) — input screens pass 5/5 (correctly! no single turn violates
anything), dialog rails track cumulative STATE against the approved path and fire at the turn the trajectory
exits it (your log: which turn, which transition rule). Record the outcome honestly: if flow tracking ALSO
missed it, that's a flow-GRANULARITY finding (your intents too coarse to see the drift — fix = finer states,
with the false-redirect cost stated). Either result teaches: safety over conversations requires STATE, and
state design (flow granularity) is the tuning knob — the dialog equivalent of chunk-size tuning in RAG.

**Q6. Retrieval rails: what do they inspect, and narrate YOUR poisoning ablation verbatim.**

**Answer:** Inspect: retrieved chunks pre-prompt — relevance floor (drop distractors), blocklist/pattern screen
(known-bad content), instruction-in-chunk detector (the poison signature: imperative language directed at the
reader-model — "ignore [X], state Y"). Ablation narration: poisoned query WITHOUT rails → bot OBEYS the planted
instruction (quote the bot's compromised response verbatim — the attack surface made tangible: anyone who can
write to your corpus can prompt-inject your users); SAME query WITH rails → chunk dropped (`rail_report`:
`chunks_dropped: [id]`, reason: instruction-pattern), answer clean from surviving chunks (quote the drop reason
+ clean answer). Two follow-ons you measured: legit-recall check (10 normal queries — rails must not nuke
useful context; report the survival rate) and the generality warning (detector catches YOUR planted phrasing —
novel poison phrasings are the residual risk, stated in policy). One row, three quotes (poison, obey, drop) —
the most persuasive 60 seconds in this file.

**Q7. Execution rails: the model TRIED the forbidden action. Why is "attempted but denied" an important distinction?**

**Answer:** Because it proves the defense sits OUTSIDE the model's compliance — prompt-level safety ("don't call
unlisted tools") ASKS; execution rails (`custom_actions.py` deny-by-default) ENFORCE. Your tool-abuse run shows
both halves in the log: model output containing the disallowed call (the attempt — prompting FAILED to prevent
it, honestly logged) followed by rail denial with reason (the enforcement — user never affected). Implications:
(a) model obedience is not a security boundary (stronger models follow obfuscated tool-abuse BETTER — the
capability-safety inversion, name it); (b) allow-lists beat deny-lists (deny-by-default + explicit permits —
your config; new tools are born denied, not born permitted); (c) attempts are TELEMETRY (attempt-rate spikes =
someone probing your tool surface — LLMOps-A dashboard input). "The model tried, the rail said no, here's the
log line" — defense in depth stated as an observed fact.

---

## Part 3: Config as Code — "Programmable means reviewable"

**Q8. Show me your config-only behavior change. What did you edit, what changed, what Python did you touch?**

**Answer:** (Present YOUR diff.) Shape: `.co` edit (new refusal wording for topic T, or new blocked intent +
transition) → re-run of the same script → before/after transcripts differ in the predicted way → `git diff`
shows ONLY `config/` files (zero Python — assert it from the diff stat). Why this matters beyond convenience:
(a) CHANGE VELOCITY — policy updates ship without runtime deploys; (b) REVIEW CLARITY — approvers read flows,
not diffs of control flow; (c) the DARK SIDE (Q9): `.co` edits bypass code review unless process says otherwise
— your policy page's config-review rule (who approves rail changes, with the removed-refusal break-run as the
cautionary exhibit). Demo live: edit, re-run, show the new behavior in under a minute — programmability you can
watch beats programmability you assert.

**Q9. Contradictory rails: input allows what dialog forbids. Which won in YOUR stack, and was it logged?**

**Answer:** (Quote YOUR probe.) Constructed case: input screens pass a turn (no keyword/policy hit) that the
active flow state forbids (off-path for this conversation) — or the reverse (input flags what the flow would
welcome). Observed resolution (NeMo's precedence: dialog/flow verdicts typically dominate input screens at
response time, but VERIFY on your version — never assert framework semantics from memory): which rail's verdict
surfaced, and did `rail_report` show BOTH verdicts or only the winner? If silent (loser's verdict invisible),
that's a DEBUGGING GAP you document (misconfigurations hide — "why did it refuse?" unanswerable from logs).
If both logged, that's the auditability win to quote. Either way the policy follows: rail-precedence documented
in YOUR config README section, plus a CI check if you built one (contradiction lint over `.co` + `config.yml` —
bonus points, describe it). Config-bug taxonomy entry #1 — interviewers who've operated NeMo nod here.

**Q10. Colang flows: what do intents, transitions, and responses look like in YOUR `.co` file?**

**Answer:** (Walk YOUR file, not the docs.) Intents: 3–5 user-goal patterns for the approved path (quote one
utterance-set); transitions: allowed state movements (e.g. `greeting → topic_q → clarify → answer → followup`,
with the off-path catch transitions that fire redirects); responses: scripted redirect/refusal texts (quote the
turn-4 redirect — scripted, specific, on-brand vs generic "I can't help"). Design notes: intent GRANULARITY
trades (coarse = misses drift, fine = false redirects — your tuning call with the specimen that set it);
fallback behavior (unmatched input → clarify, not refuse — UX + safety balance, stated); response tone (redirects
that preserve the relationship vs refusals that end it — product decision, documented). "You edit YAML/Colang,
not Python, to change behavior" — then SHOW the 5-line edit from Q8. Concreteness about YOUR flows beats any
Colang tutorial recap.

---

## Part 4: Operations — "Rails in production"

**Q11. Five LLM-backed rails per turn: what's the latency bill, and how would you cut it?**

**Answer:** (Quote YOUR per-turn overhead: total added ms + per-rail split.) Typical shape: input screens
(patterns: ~free; ML: tens of ms) + dialog state check (LLM call — the big one) + retrieval filter (ms over
chunks) + output vet (LLM call — second big one) = often DOUBLING turn latency vs unguarded. Cuts, in order:
(a) ORDER cheap-first + short-circuit (pattern rejections skip ML checks — same discipline as Project A);
(b) CACHE verdicts (identical/repeat turns, stable flow states — verdict cache with TTL); (c) PARALLELIZE
independent rails (input screen ∥ retrieval filter — no dependency, run together); (d) SMALL-MODEL rails
(classifier rails on tiny models, generator stays big — the cost/latency asymmetry trick from agentic design);
(e) SAMPLE output vetting (vet every Nth turn + all high-risk flows — coverage/cost trade, stated not hidden).
Your 5×-volume probe (which span degrades first) + monthly cost row make this a budget conversation, and the
rail_report ms column is the permanent profiler.

**Q12. Who reviews `.co` edits, and what happens when rails themselves need evals?**

**Answer:** Review: `.co` + `config.yml` changes are SECURITY changes — your policy (named owners, required
reviewers, the removed-refusal cautionary run linked in the policy). Test: rail changes run against the FULL
`adversarial_dialogs.jsonl` + single-turn set in CI (config PR → automated attack suite → block on new slips —
Evals-B pattern applied to safety config; state whether you wired it or prescribe it). Drift: rails Dialog
behavior vs model upgrades (new model version interprets flows differently — re-run the suite on model change,
log the version sensitivity you observed). Residuals (Q13's list) get OWNERS + watch-signals (guard-fire-rate
dashboard, attempt-rate telemetry from execution rails). The meta-answer: rails are SOFTWARE (versioned,
tested, reviewed, monitored) — "programmable" describes the mechanism; the discipline around it is what makes
it production safety instead of a config hobby.

**Q13. What still gets through? Enumerate YOUR residual risks with mitigations.**

**Answer:** (Your policy's residual section, spoken.) Novel jailbreak phrasings (zero-days — mitigation: update
cadence + fire-rate monitoring, not completeness claims); slow-drift sequences below flow granularity (mitigation:
finer states where justified + turn-window anomaly review); novel poison phrasings beating the chunk detector
(mitigation: provenance controls on corpus writes — who can plant chunks is a PERMISSIONS problem, plus periodic
corpus scans); capability-inversion cases (smarter models, subtler compliance — mitigation: execution rails +
output vetting as model-independent backstops); config contradictions (mitigation: precedence docs + lint +
review). Each with an OWNER and a SIGNAL (which dashboard moves when it happens). Close: "rails raise the cost
of attack from one clever prompt to sustained multi-layer effort under monitoring — that's the actual security
claim, stated without completeness theater."

---

## How to Use These Questions

1. **Quote the poisoning pair** — obey-response vs drop-reason: 60 seconds that justify retrieval rails to anyone.
2. **Show the config diff** — behavior change, zero Python, before/after transcripts: programmability demonstrated.
3. **Narrate precedence** — contradictory-rails probe + what's logged: operator credibility.
4. **List residuals with owners** — gaps + signals + mitigations: senior posture, no completeness theater.
