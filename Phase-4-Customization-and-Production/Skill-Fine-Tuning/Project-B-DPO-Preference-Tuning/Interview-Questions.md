# Interview Questions — Preference Tuning with DPO (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual runs and artifacts** — pair audits, β sweep, win-rate table,
repair deltas, ablation rows. Quote the win-rate table; that separates "read the DPO paper" from
"aligned a model."

---

## Part 1: Fundamentals — "SFT vs DPO, RLHF vs DPO"

**Q1. SFT teaches capability, DPO teaches preference — make that concrete with YOUR behaviors.**

**Answer:** SFT (Project A): "produce valid JSON with fields X/Y" — the model LEARNS the shape (couldn't do
it reliably before; compliance X%→Y%). DPO (this project): given TWO valid JSONs, prefer the terse-helpful
one / given TWO answers, prefer the refusing-safe one — the model already CAN produce both variants (SFT
gave it the range); DPO shifts WHICH it reaches for. Your behavior tags make it tangible: tag "refusal-crisp"
(chosen refuses crisply vs rejected lectures-or-complies — same prompt, both fluent, one safe), tag "cite-style"
(chosen cites per claim vs rejected dumps sources at the end). SFT's loss rewards imitating the single target;
DPO's loss rewards RANKING chosen over rejected. "SFT teaches the shape of right; DPO teaches the choice among
rights" — then show one pair where both responses are CORRECT and only preference differs (that's the DPO-only
territory SFT can never reach).

**Q2. RLHF in three stages, then DPO's collapse — with the "why simpler wins" reasoning.**

**Answer:** Classic RLHF: (1) SFT (capable policy), (2) REWARD MODEL trained on human pairwise preferences
(a separate model predicting "human would prefer A" — expensive to train well, gameable, drifts), (3) PPO
reinforcement loop optimizing the policy against the reward model (unstable: KL tuning, value heads, mode
collapse — the RL zoo). DPO COLLAPSES 2–3 into one supervised step: the pairwise loss directly pushes
log-prob(chosen) above log-prob(rejected), β-regularized against the frozen SFT reference — the reference IS
the implicit reward baseline, so no reward model exists to game or maintain. Why simpler wins here: no RL
variance (deterministic gradients on pairs), no reward-model maintenance, runnable on a T4 (YOUR receipt —
PPO at this tier is masochism). What you LOSE vs full RLHF (honest): online exploration (DPO learns only from
given pairs, never tries novel responses for reward — the offline limitation, stated) and complex multi-attribute
reward shaping (one β leash vs a shaped reward landscape). For 1–3 crisp behaviors on a small model, the trade
is overwhelmingly DPO's — your win-rate is the evidence.

**Q3. The DPO loss in one paragraph — no hand-waving, and explain β like a leash.**

**Answer:** Per pair: loss = −log σ(β · [(log π(chosen) − log π_ref(chosen)) − (log π(rejected) −
log π_ref(rejected))]) — the policy must assign chosen HIGHER relative-likelihood (vs reference) than rejected,
with β scaling how hard that gap is pushed; the reference terms ANCHOR both (drifting from SFT on everything
costs loss even while widening the pair gap — that's the KL leash inside the math). β as leash: HIGH β (0.5) =
short leash — tiny steps from reference (safe: no degeneration; weak: win-rate barely moves — YOUR row);
LOW β (0.01) = long leash — hard alignment push (win-rate jumps; degeneration specimens appear — YOUR quote).
β=0.1 default = the leash length the field converged on, and YOUR sweep re-derives it instead of inheriting it
("we ship 0.1 because OUR rows 0.01/0.1/0.5 show…"). If pressed deeper: β→0 approaches unregularized preference
maximization (reward-hacking territory — your 5-epoch run lives here); β→∞ approaches frozen SFT. The sweep
table IS the loss-function understanding, measured.

---

## Part 2: Data — "Pairs are everything"

**Q4. What makes a preference pair GOOD? Show me your best and worst pair and the rewrite.**

**Answer:** GOOD: chosen−rejected differ in EXACTLY the tagged behavior, all else equal (same facts, length,
fluency — the gap ISOLATES the lesson; the model learns "prefer refusal-crispness," not "prefer short answers
about topics I like"). YOUR best pair (quote it): stranger test passes (which is chosen is obvious without
explanation). YOUR worst-first-draft (quote it): differed in EVERYTHING (chosen: correct+safe+terse; rejected:
wrong+rude+verbose — teaches nothing attributable; audit rejected it for [reason]). Rewrite: hold facts/length
fixed, vary ONLY the tag (rejected = same answer, compliant-but-unsafe / verbose). Audit stats quoted (rate +
top reject reasons — "multi-gap pairs" likely #1). The principle, stated hard: DPO learns the DIFFERENCE, so
pair design IS objective design — sloppy pairs train sloppy preferences with mathematical certainty. Your
audited-vs-noisy ablation (win-rate gap) prices the discipline.

**Q5. How did you build 300–1000 pairs without hand-writing each? Where does synthesis break?**

**Answer:** Pipeline: hand-write 20–50 SEED pairs per tag (the quality anchors) → LLM-synthesize variants
(prompt: "given this pair, produce 5 new prompts with the same behavior contrast, same facts-held-fixed
discipline") → AUDIT sample (30+, accept/reject + reasons — your log). Synthesis breaks characteristically:
DRIFT (variants widen the gap beyond the tag — multi-gap creep; caught by audit reason counts), TRIVIALITY
(rejected absurdly bad — pairs teach nothing; the eval-vanity mirror in data form), REVERSAL (synthesized
"chosen" actually worse on the tag — label noise, the 20%-flip experiment's real-world cousin), and
SELF-SIMILARITY (all variants one template — diversity collapse; check via embedding-spread or eyeball
clustering). Mitigations you used (quote): seed anchoring, per-batch audits (not end-only), diversity prompts,
the stranger test. Counts: seeds → synthesized → audited-accepted per tag (YOUR funnel numbers — the data
supply chain made visible).

**Q6. The flipped-pair experiment: you swapped 20% of labels and trained. What happened, exactly?**

**Answer:** (Quote YOUR collapse.) Expected: win-rate craters toward/below 50 (model learns anti-preference on
the flipped fifth — gradient signal contradicts itself), loss still DECREASES (the treacherous part — training
looks healthy while alignment inverts; loss monitors optimization, NOT objective correctness). Specimens: outputs
exhibiting the REJECTED behavior confidently (quote one — the model learned the wrong lesson WELL). Lessons:
(a) label noise isn't symmetric friction, it's ACTIVE MISDIRECTION (20% flips ≠ 20% slower — it's negative
teaching); (b) loss curves can't detect it (only held-out win-rate + sample reading can — your eval discipline
justified again); (c) audit ROI priced (your audited-vs-noisy gap IS the cost of skipping Phase 1 care).
Production moral: preference pipelines need label QA gates (audits, agreement checks on labelers, flip-detection
via suspicious-pair review) as load-bearing infra — "data quality" isn't a slogan, it's the ±30 win-rate points
in your ablation.

---

## Part 3: Training & Evaluation — "Win-rate honesty"

**Q7. Win-rate: define the protocol precisely enough that I'd trust it. What are its attack surfaces?**

**Answer:** Protocol (`winrate.py`): LOCKED held-out prompts (never in pairs, contamination-checked) → generate
from SFT and DPO models (same sampling params) → BLIND pairwise presentation to judge (order RANDOMIZED per
matchup — position bias control, YOUR flip-rate measured) → judge picks winner per YOUR rubric (tagged
behaviors, anchored scale) → win-rate = DPO-wins / decided (ties reported separately, not split). Attack
surfaces + YOUR controls: POSITION bias (flipped-order re-score of 20 matchups — flip rate quoted; high flips =
judge unfit, re-rubric); VERBOSITY bias (DPO answers longer? length-stratify: win-rate within length bands —
if DPO wins only by length, that's reward hacking, not alignment); JUDGE FAMILY bias (same-family judge
inflates — cross-family check or human spot audit of 15 matchups, agreement quoted); TIE-HIDING (lopsided ties
buried — report tie rate + read 5 ties aloud). "65% win-rate" without protocol + controls is a number; with
them it's evidence. Your table carries the footnotes — point at them.

**Q8. Narrate your β sweep. Which β shipped, and what specimen decided it?**

**Answer:** (Walk YOUR three rows.) Expected shape: β=0.5 — loss smooth, win-rate ~55 (leash too short —
alignment whisper; specimen: outputs barely moved from SFT); β=0.1 — win-rate PEAK (~your 65–80; specimens show
chosen behavior cleanly, no degeneration); β=0.01 — win-rate similar-or-higher BUT degeneration specimens
(safety-preamble bloat, hedging tics, length explosion — quote YOURS; the leash too long). SHIP = 0.1 (peak
win-rate with zero degeneration specimens — the two-criterion rule: maximize wins SUBJECT TO no pathology).
The specimens decide as much as the numbers (a higher-win β with degeneration quotes LOSES — stated policy).
Also note epoch interaction (1 epoch — your 5-epoch run shows β×epochs jointly overdose; leash AND duration).
"Our β isn't a default, it's a measured optimum with pathology bounds" — the sentence that ends follow-ups.

**Q9. Over-optimization on purpose: what did 5 epochs on 200 pairs produce? Quote the pathology.**

**Answer:** (YOUR specimens — the funniest, most instructive quotes in this file.) Classic pathologies:
SAFETY-BLOAT (every answer opens with a paragraph of preamble regardless of prompt — alignment signal
over-amplified into tic); LENGTH EXPLOSION (verbosity bias in pairs/judge rewarded longer = longer learned —
your length stats per epoch); HEDGING CREEP ("as an AI…" infestation — the preference learned as style-mimicry,
not judgment); CAPABILITY EROSION (SFT-task metric dips — alignment tax turning into alignment eviction).
Mechanism: fixed pair set + many epochs = memorize the pair distribution's SURFACE (not the behavior) while the
β leash stretches across repetitions. Cures observed (not theorized): stop at 1 epoch (YOUR rule), bigger pair
sets (dilute memorization), higher β (shorter leash per step). This run is DPO's overfitting portrait — hang it
next to SFT's 10-epoch memorizer (the two PNGs side by side tell the full post-training cautionary tale).

---

## Part 4: Repair & Taxes — "Alignment's balance sheet"

**Q10. Refusal repair: SFT broke it (or didn't) — DPO fixed it (or confirmed it). Numbers and specimens.**

**Answer:** (YOUR balance sheet.) If SFT REGRESSED (R%→S% on Guardrails-A set): DPO tag #1 was refusal-repair
pairs → post-DPO refusal T% (repaired toward R — full or partial, stated honestly) WITH win-rate on other tags
intact (repair didn't cost helpfulness — or cost X points, the trade stated). Specimens: the SFT-compliant
failure (model helping where it should refuse — quoted) vs DPO's crisp refusal (quoted) — the before/after
that justifies the project to anyone. If SFT DIDN'T regress: "no repair needed — refusal R%→R%±noise; DPO
pursued style/helpfulness tags; the re-check still ran because ASSUMING safety survives tuning is how
regressions ship." Either branch demonstrates the discipline: every tune ships with its safety balance sheet
(capability Δ, refusal Δ, alignment-tax Δ). Unmeasured safety after weight changes is a rumor — your table
makes it a reading.

**Q11. Alignment tax: what did DPO cost in capability? Is the tax acceptable?**

**Answer:** (YOUR SFT-task re-score: pre-DPO vs post-DPO on Project A's held-out.) Tax = capability delta
(typically small-negative to flat: −0–3 points — the policy mass moved from task-peaks to preference-peaks).
Acceptability rule (state YOURS): tax acceptable iff (win-rate gain × behavior value) ≫ (capability loss × task
criticality) — e.g. −1pt JSON accuracy for +20pt refusal-crispness on a user-facing bot: ship it; −8pt accuracy
for +5pt terseness on an extraction pipeline: revert it. Mitigations if tax bites: fewer epochs, higher β,
mix SFT-format pairs into DPO training (replay — the forgetting antidote shared with SFT), narrower tags.
Report BOTH taxes together in the capstone (SFT forgetting + DPO tax = full post-training cost ledger). "Taxes
are real, measured, and priced into the ship decision" — the adult answer to "any downsides?"

**Q12. DPO vs RAG vs prompting for YOUR behaviors — why was weight-change the right tool for THESE tags?**

**Answer:** Per-tag justification (the framework applied, not recited): refusal-crispness → DPO (behavioral
default under ADVERSARIAL pressure — prompts degrade under jailbreaks, retrieval irrelevant to refusal style;
baked-in default survives what instructions don't — your red-team refusal specimens pre/post prove it);
cite-style/tone → DPO-or-prompting (honest split: prompting ALMOST worked — base followed style 70% — but
variance under rephrasing failed the consistency bar; DPO bought the last 25 points + robustness — quote the
variance numbers); knowledge tags → NOT DPO (a tag needing fresh facts belongs in RAG — if you tried one, show
why it underperformed vs retrieval; if you didn't, state the exclusion rule). The meta-lesson: DPO for DEFAULTS
(what the model reaches for unprompted), RAG for KNOWLEDGE (what changes), prompting for the REST. Your tags
sorted into those buckets with one specimen each — the framework with YOUR data.

---

## Part 5: Limits — "What DPO can't do"

**Q13. Offline limitation: DPO never explores. What can't it learn that online RL could?**

**Answer:** DPO learns ONLY from given pairs (offline) — it reweights toward chosen variants it has SEEN, never
discovers better responses by trying (no exploration, no environmental reward). Concretely unlearnable: novel
strategies absent from pairs (a smarter refusal framing nobody wrote — DPO can't invent it; PPO-with-reward
could stumble into it via sampling + reward); multi-step behavior chains (tool-use policies with delayed payoff
— pairwise static judgments don't capture sequential credit assignment); behaviors where "better" needs
INTERACTION to judge (dialog repair skill — static pairs flatten it). Your evidence of the boundary: a held-out
prompt where BOTH SFT and DPO fail identically (the gap pairs never covered — quote it; more epochs wouldn't
help, only NEW pair coverage would). Implication: DPO saturates at pair-distribution quality (your noisy-ablation
restated as a ceiling), and the upgrade path is online methods or richer pair mining (self-play, judge-ranked
sampling — name them as future work, not magic).

**Q14. Reward hacking in miniature: did your model game the judge? How did you check?**

**Answer:** (YOUR check.) Hacking signatures to hunt: length-win correlation (win-rate computed within
length bands — if DPO wins only long, it's verbosity gaming, YOUR band table); judge-pleasing tics (safety
preambles, hedging, flattery — specimen hunt in DPO outputs; your 5-epoch run OVERFLOWS with these, the 1-epoch
ship build should show ~none — compare the two explicitly); rubric-gaming (citations sprinkled decoratively
without supporting claims — faithfulness spot-check on 10 DPO wins). Controls that caught-or-cleared yours:
band analysis + human spot audit (15 matchups, agreement quoted) + the degeneration-specimen gate in β selection
(pathology = auto-reject regardless of win-rate). The honest close: "our 1-epoch build shows no hacking
signatures by THESE checks; the 5-epoch build shows all of them — hacking is a dose phenomenon, and our dose is
measured." Small-scale reward hacking observed + bounded beats "our model doesn't do that" every time.

---

## How to Use These Questions

1. **Show pairs first** — best pair, worst draft, rewrite: data discipline before math.
2. **Walk the sweep** — three β rows with specimens: the leash, measured, pathology-bounded.
3. **Quote both pathologies** — flip-collapse + epoch-bloat: failure literacy is alignment literacy.
4. **Close the ledger** — win-rate, repair delta, alignment tax, SFT-tax total: the balance sheet.
