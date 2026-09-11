# Interview Questions — Agentic / Graph RAG (with Answers)

These questions simulate a real technical interview for an AI engineering role. Each answer is
grounded in **this project's actual code and the numbers you measured** — router logs, graph paths,
retry traces, per-path latency. Quote your path-vs-baseline table; that separates "knows the buzzwords"
from "shipped an agentic pipeline."

---

## Part 1: Fundamentals — "Why isn't naive RAG enough?"

**Q1. What exactly breaks in "always retrieve then generate," and give me a query from YOUR set for each break?**

**Answer:** Naive RAG (Project A) runs one fixed path — embed, top-k, generate — for every input. Three
failure classes, each with a golden example you logged in Phase 0:

(a) **Wasted retrieval.** Greetings, chitchat, simple math ("hi, what can you do?", "what is 17*23?")
pay full retrieval cost (embed ~190ms + lookup + rerank) for zero benefit — the answer was in the model's
weights. Your DIRECT-route bucket proves the waste: same answer, retrieval skipped, latency collapsed.

(b) **Unrepresentable intent.** Multi-hop questions ("which company acquired X in 2023, and what was their
revenue?") need TWO facts chained. One query embedding averages both intents into a vector similar to
neither; single-pass top-5 contains half the answer at best. You verified this by running Project A on the
multi-hop set and logging the partial/wrong answers — that failure table is the project's founding document.

(c) **No recovery.** A bad first pass (paraphrased query, wrong synonyms) stays bad — the pipeline has no
mechanism to notice and try differently. Your retry-triggering bucket (first-pass top-1 wrong, rephrased
second-pass hits) is the concrete specimen.

If you can't name one query per bucket from your own golden set, you haven't done Phase 0.

**Q2. What makes this system "agentic" rather than just a bigger pipeline?**

**Answer:** A pipeline executes fixed stages; an agent makes DECISIONS with observation feedback. Three
decision points here, each logged in `trace.jsonl`: (1) `router.py` chooses the path per query (DIRECT /
SINGLE / MULTI_HOP) with a reason string — the path isn't predetermined; (2) `decompose.py` + graph
assembly choose HOW to gather context (sub-question chain, traversal depth, widen strategy); (3)
`confidence.py` → `retry.py` observes the outcome (scores, citation coverage) and decides whether to try
again differently or stop. Fixed pipeline: same steps regardless. Agentic: the trajectory of query X differs
from query Y because intermediate observations changed the plan — and `--trace` shows you exactly where it
branched. The price (Q16) is latency, cost, and debuggability — agency is a tradeoff, not an upgrade.

**Q3. Walk me through one multi-hop query end to end, naming every file that touches it.**

**Answer:** Take "company that acquired X → their revenue" with `--trace`: (1) `router.py` LLM-classifies
→ `{"route": "MULTI_HOP", "reason": "requires chaining two facts", "confidence": 0.9}`; (2) `decompose.py`
splits → `["Who acquired X in 2023?", "What was <answer1>'s 2023 revenue?"]`; (3) sub-q1 goes through
Project A's hybrid path (embed → Chroma top-20 + BM25 top-20 → `fusion.py` RRF → `rerank.py` top-5) → fact 1
(e.g. "Acme"); (4) sub-q2 instantiated with fact 1, retrieved the same way → fact 2; (5) `graph.py`
`traverse(seed_entities=["X","Acme"], max_hops=2)` BFS-returns the path `X -[acquired_by]-> Acme
-[revenue_2023]-> $Y` with source-chunk IDs on each edge; (6) assembly orders graph paths FIRST (precise
relations) then vector chunks (prose context) → `generate.py` grounded prompt → answer with per-hop
citations; (7) `confidence.py` checks (rerank scores + citation coverage) → pass → return. The trace JSONL
line contains route, sub-queries, graph path, ranks, retry history, prompt hash, answer — narrate any run
from that line alone.

---

## Part 2: Routing & Decomposition — "Deciding how to retrieve"

**Q4. How does the router work mechanically, and how did you measure whether it's any good?**

**Answer:** `router.py` is ONE LLM call: system prompt defines three routes with 2 few-shot examples each,
forced JSON output `{"route", "reason", "confidence"}` via native `format="json"` (same decoding-constraint
lesson as Phase 1 JSON mode — prompt alone drifts). `--route` overrides for debugging. Quality = confusion
measured on YOUR golden buckets: % no-retrieval → DIRECT (want 100%), % multi-hop → MULTI_HOP, % single-hop
→ SINGLE. Every misroute is logged with its reason string — you prompt-fix from those verbatim strings, not
from theory. Known confusion pair to quote: underspecified single-hop ("tell me about Acme") vs multi-hop —
record which way yours errs and the example you fixed. A router at 90% with logged reasons beats a "smarter"
router you can't debug.

**Q5. Query decomposition — what does it actually do, and when does it fail?**

**Answer:** `decompose.py` turns one unretrievable question into an ORDERED chain of retrievable ones:
"company that acquired X in 2023 → their revenue" becomes "Who acquired X in 2023?" then "What was
<answer1>'s revenue?" — each sub-query embeds cleanly (single intent → sharp vector), results chain
(answer1 instantiates sub-q2). It fails when: sub-questions aren't independent (answer1 wrong poisons
everything downstream — error COMPOUNDS, the chaining hazard); the decomposition itself needs knowledge
the model lacks (it splits wrong); or ordering is wrong (asks revenue before identifying the company).
Your Phase 2 verification isolates this: questions fixed by decomposition ALONE (no graph) vs still-failing
(graph needed) — that split is your answer to "what does decomposition buy by itself."

**Q6. Router says SINGLE but the question needed MULTI — what happens? Trace the damage.**

**Answer:** The query takes Project A's single-pass path: one embedding, fused top-20, rerank, generate.
Best case the top-5 contains one hop's facts and the answer is half-right with citations covering only half
the claims (your citation-coverage check in `confidence.py` should FAIL this — zero resolvable citations for
the second claim → retry triggers, possibly rescuing via rephrase). Worst case the answer fluently chains a
retrieved fact with a hallucinated bridge ("Acme acquired X, and Acme's revenue was $Z" where $Z is invented)
— cited hallucination, the agentic version of Project A's worst failure. This is why the confidence gate
checks CITATIONS, not just scores: a high rerank score on half the evidence must still fail. Quote your
misroute example and whether retry rescued it.

---

## Part 3: Knowledge Graphs — "Relations, not just similarity"

**Q7. Vector search finds similar text. What does the graph find that vectors can't?**

**Answer:** EXPLICIT RELATIONS. Vector search answers "text about X" — it retrieves passages whose pooled
embedding points near the query. A knowledge graph (`graph.py`, NetworkX `DiGraph`) stores
`(head_entity, relation, tail_entity)` triples with source-chunk IDs on edges: `(X, acquired_by, Acme)`,
`(Acme, revenue_2023, $Y)`. For "company that acquired X → revenue," no single passage may state the full
chain — the answer lives in the JOIN across two facts. BFS traversal from seed entities walks edges
(`X → acquired_by → Acme → revenue_2023 → $Y`) and returns the PATH, each hop citable to its chunk. Vectors
find "things described similarly"; traversal finds "things connected by a named relationship." Your graph
ablation (Q14) quantifies exactly which questions need the join.

**Q8. How do triples get into the graph? Walk me through extract → build → traverse.**

**Answer:** (1) `extract.py`: per chunk (start with 20–50, quality over coverage), an LLM call emits
`[(head, relation, tail)]` with the source chunk ID attached to each triple — relation vocabulary is
open (whatever the model emits), which is both the power and the mess. (2) `graph.py` builds nodes
(entities, with alias list) and directed edges (relation label + `source_chunk` attr), persists via pickle
(`graph.pkl`, regenerable with `build-graph`). (3) At query time: link query nouns to nodes (YOUR
implementation: exact/alias match — note the limitation in Q9), BFS from seeds to `max_hops=2`, return paths
(entity-path + relation-labels + supporting chunk IDs). `--show-graph` prints the matched entities and edges
— the graph equivalent of `--show-context`.

**Q9. What's the weakest link in YOUR graph pipeline? (There's always one.)**

**Answer:** Seed-entity linking. Your exact/alias match breaks on paraphrase: graph node "Acme Corp" vs query
"Acme" vs chunk text "the company" — the traversal seed misses, BFS starts from nothing, graph path comes back
empty, and the system silently falls back to vector-only. You have a concrete miss logged (the "Acme Corp" vs
"Acme" deliberate-break run). Honest follow-through: production fixes are embedding-based entity linking
(embed mention, nearest node) or canonicalization at extraction (LLM normalizes aliases to one node ID) —
both add their own error modes. Stating "my graph works when entities match strings and degrades to vector
search otherwise, here's the example" is the senior answer. Never claim the graph "understands" — it matches
and traverses.

**Q10. Graph + vector assembly — how do you combine them, and why that order?**

**Answer:** Graph paths FIRST (precise, relational, each hop citable), vector top-k AFTER (supporting prose,
definitions, context the triples strip away). Rationale: triples are lossy (they discard dates' nuance,
qualifiers, negation) while vectors are blurry (similar but unjoined). Paths answer the JOIN; chunks let the
generator phrase it correctly and catch extraction errors (if a path claims a relation the chunk contradicts,
the generator sees both — your spot-checks should include one such conflict). Regression guard: re-run the
FULL Project A single-hop set with graph enabled — graph context must not pollute simple queries. Any
single-hop regression is an assembly bug (fix: only include graph paths when route is MULTI_HOP, or threshold
on path relevance).

---

## Part 4: Confidence & Retry — "The self-correction loop"

**Q11. How does the system know its first attempt was bad? Define the confidence gate precisely.**

**Answer:** `confidence.py` fails the attempt if ANY of: (a) best rerank score < calibrated threshold (same
per-corpus calibration as Project A's `--min-score` — score ceiling means corpus gap); (b) answer has zero
resolvable citations (claims point nowhere — grounding failure regardless of scores); (c) router confidence
< 0.5 on a SINGLE route (the path itself was a guess). Output is `{"pass": bool, "reason": string}` — the
reason selects the retry strategy (low-score → widen k/hops; no-citations → rephrase; low-route-confidence →
escalate to MULTI). Testing the gate matters as much as the retry: feed it a KNOWN-good answer (must pass)
and a KNOWN-bad one (must fail) — a gate that passes everything is decoration.

**Q12. What are the retry strategies, in order, and why that order?**

**Answer:** `retry.py`, cheapest-first: (1) LLM REPHRASE → re-retrieve (fixes vocabulary mismatch, costs one
embed + lookup — your rescue-rate table should show this fixes the most); (2) WIDEN: `k` 20→40, hops 2→3
(fixes recall misses, costs more candidates through the reranker — quote the ms); (3) BM25-HEAVY fusion
(fixes exact-term misses the dense path dropped — reweight RRF inputs toward keyword ranks). Max 2 rounds,
then HONEST abstention with all attempts logged — never a third round, never silent hallucination. Order
rationale: try the cheap semantic fix before the expensive recall fix before the modality switch. Your table
(X of Y first-pass failures rescued, by which strategy, ms per rescue) is the evidence.

**Q13. Retry loops can spin forever or burn money. What are YOUR guardrails?**

**Answer:** Three hard limits: `--max-retries 2` (attempt count bound — your `--max-retries 0` break-run proves
the failure it prevents); per-path TIMEOUT (a MULTI+retry chain at 10k req/day needs a deadline — your latency
forensics set it, and timeout yields the best-so-far answer or abstention, never a hang); and STRATEGY
EXHAUSTION (each strategy tried once — no rephrase→rephrase loops). Also: retry only triggers on gate FAIL
with a reason, never "just to be safe" — unconditional retry doubles cost for zero expected gain. At scale
this becomes the agentic-system-design topic from the roadmap gaps (budgets, idempotency, circuit breakers) —
name that connection.

---

## Part 5: Tradeoffs & Production — "When does agentic earn its complexity?"

**Q14. Graph ablation: which questions actually NEED the graph? (Decomposition-only vs full multi.)**

**Answer:** Run the multi-hop set twice: decompose+vector-only (`--route single` + decompose, graph disabled)
vs full MULTI path. Expected split: questions answerable from TWO retrievable passages (each sub-query hits
independently) pass WITHOUT the graph — decomposition suffices. Questions whose middle hop is never stated
plainly in one chunk (relation implied across sentences, entity referenced by pronoun/alias) NEED traversal.
Your table names members of each class. Interview moral: Graph RAG earns its complexity (extraction cost,
linking fragility, traversal latency) ONLY for the second class — for the first, it's overhead. "We added the
graph because questions A, B need joins; questions C, D pass without it" beats any architecture diagram.

**Q15. Break down per-path latency. What does each decision cost?**

**Answer:** Your `--trace` timing, four rows (quote yours; expected shape): DIRECT ≈ one LLM call (fastest,
no embed); SINGLE ≈ Project A cost (embed ~190ms + rerank + generation); MULTI ≈ 2–3× SINGLE (router call +
2+ retrieval chains + extraction-free traversal + longer generation prompt); MULTI+retry ≈ worst case
(everything above × attempts — the long tail). Two consequences: (a) the router SAVES money on DIRECT queries
(quantify: X% of your traffic × SINGLE-cost avoided); (b) p99 is set by the retry chain, so production needs
per-path timeouts and a latency budget per query class. At 10k req/day you'd cache DIRECT answers, cap MULTI
concurrency, and alert on retry-rate spikes (retry storm = corpus or model regression).

**Q16. Name the full complexity bill. Why might a team choose NOT to build this?**

**Answer:** Bill: router LLM call per query (+latency, +misroute class of bugs); extraction LLM calls per
chunk at build time (+build cost, +stale-graph maintenance on corpus change); entity-linking fragility (Q9 —
silent fallback); retry multiplying worst-case cost (2–3× per query); trajectory storage/observability burden;
and debugging across FIVE interacting stages instead of one. A team chooses plain hybrid RAG when: queries are
single-hop (your single-hop set passes WITHOUT any of this), corpus relations are flat, latency SLOs are tight,
or eval shows the router's rescue rate below the misroute rate. Agentic RAG is indicated by measured multi-hop
demand + your ablation delta — "our multi-hop pass rate went X→Y at +Zms p50" is the entire business case.

**Q17. How do you eval an agentic system? (Harder than evaling a pipeline.)**

**Answer:** Three layers beyond Project A's recall@5: (a) PATH accuracy — did the router choose the right
route per bucket (confusion matrix from your golden set); each misroute is a labeled eval failure. (b) OUTCOME
per bucket — DIRECT correctness (no hallucination without retrieval), SINGLE parity with Project A (no
regression!), MULTI pass rate vs Project A baseline (the headline delta). (c) TRAJECTORY audits — sample
traces reviewed by eye: is the reason string honest, does the graph path support the answer, did retry trigger
for the logged reason. Plus the standard harness: curated + synthetic golden Q/A, faithfulness/citation checks
(Phase 3 evals consume these traces). Without path-level eval you're grading the answer while blind to whether
the system took a sane route to get there.

**Q18. Force `--route direct` on a factual question. What happens, and what does it prove?**

**Answer:** The generator answers from parametric knowledge with ZERO citations — fluent, confident, possibly
right, possibly stale or invented, and provably ungrounded (trace shows no retrieval stage). It proves the
router's safety role: skipping retrieval isn't an optimization, it's a correctness decision, and a wrong skip
produces the exact failure RAG exists to prevent. This is also the cheapest demo of why citations are load-
bearing (Q11 in Project A): no citations = no verifiability = no trust, regardless of answer quality. Keep this
break-run in your back pocket for interviews — narrating it live takes 30 seconds and lands harder than any
definition.

---

## How to Use These Questions

1. **Narrate from traces** — every answer should reference a `--trace` line, a table row, or a logged graph path.
2. **Name your failures** — the misroute, the linking miss, the unrescued retry: concrete misses with reasons.
3. **Argue the tradeoff** — for router, graph, and retry alike: what it cost (ms, calls, bugs) vs what it fixed (which questions).
4. **Connect forward** — retry budgets → agentic system design gap topic; trajectory logs → Phase 3 eval inputs.
