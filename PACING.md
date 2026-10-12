# Pacing Plan — Phases 2–5 (weekends-only, alongside a 9–5)

**Calibration:** Phase 1 took ~1 month for 2 beginner projects at weekends-only. Phase 2–4
projects are bigger (5–6 build phases each), so budgets below are 2–3 weekends per project at
**~3 scheduled weekends per month** — the 4th weekend is life/buffer. Plan on 75% availability,
not 100%.

**Start:** Mon 12 Oct 2026 (prep/setup) → first build weekend Sat 17 Oct 2026 · **Horizon:** ~11 months → capstone live ~Sep 2027.

## Rules that matter more than dates

1. **DoD-gated, not calendar-gated.** A project is done when its Definition of Done is met and
   its tables are filled — not when its weekends run out. Slip the next block before you skip an
   ablation table; the tables are your interview capital.
2. **Friday-night setup (15–30 min):** read the coming build phase's checkboxes, queue
   `ollama pull` / `uv pip install`. Saturday morning should start *building*, not downloading.
   (First week only: use Mon 12 Oct evening for this prep instead.)
3. **Sunday closeout (15 min):** fill the "Observations worth writing down" bullets while fresh —
   they become interview answers verbatim.
4. **Re-calibrate after RAG-A.** It's your first intermediate project — your actual weekend count
   there resets every later budget. Update the dates below once it's done.
5. **Spine vs depth.** If you slip >2 weeks, defer DEPTH items (RAG-B, Agents-B, Guards-B, FT-B,
   extra frontier tracks) to *after* the capstone — defer, never skip silently. Never defer:
   RAG-A, Agents-A, Evals-A, Evals-B (LLMOps-B imports its gate), Guards-A, FT-A, LLMOps-A/B,
   the capstone, and the §2 design write-ups.

## Phase 2 — Building AI Apps (Oct 2026 → mid-Jan 2027)

| Project | Weekends | Window | Weekend-by-weekend |
| ------- | -------- | ------ | ------------------ |
| RAG-A Hybrid Search | 3 | Oct 17 → Nov 1 | W1 Oct 17–18 corpus + golden.jsonl first, ingestion reused from semantic-search · W2 Oct 24–25 BM25 + RRF fusion, per-type win records · W3 Oct 31–Nov 1 reranker + grounded generation + abstention, ablation table |
| RAG-B Agentic/Graph (DEPTH) | 3 | Nov 7 → Nov 22 | W1 Nov 7–8 extended golden set + router · W2 Nov 14–15 decompose + graph build · W3 Nov 21–22 confidence retry + trajectory report |
| Agents-A ReAct + MCP | 3 | Nov 28 → Dec 13 | W1 Nov 28–29 task set + tools/schemas, unit-tested · W2 Dec 5–6 the loop + error-as-observation · W3 Dec 12–13 MCP wiring + trace report |
| Agents-B Multi-Agent (DEPTH) | 3 | Dec 19 → Jan 10 (skip Dec 26–27) | W1 Dec 19–20 workers + state/reducers standalone · W2 Jan 2–3 graph + supervisor routing · W3 Jan 9–10 checkpoint kill-test + HITL gate + report |
| Phase close | 1 | Jan 16–17 | Both `Interview-Questions.md` out loud, README tables tidy, overflow buffer |

Dec 26–27: off (holidays). No working weekend there — that's the deal for staying on track elsewhere.

**Checkpoint:** you can whiteboard hybrid RAG and an agent loop, with your own numbers attached.

## Phase 3 — Quality & Safety (Jan → Apr 2027)

| Project | Weekends | Window | Weekend-by-weekend |
| ------- | -------- | ------ | ------------------ |
| Evals-A Harness | 3 | Jan 23 → Feb 7 | W1 Jan 23–24 curated golden set + synthetic gen + audit · W2 Jan 30–31 deterministic recall@k/MRR, 3 configs · W3 Feb 6–7 Ragas judge metrics + judge-vs-human validation + comparison report |
| Evals-B CI Gate | 2 | Feb 13 → Feb 21 | W1 Feb 13–14 eval cases as pytest + custom criteria, green locally, red-team locally · W2 Feb 20–21 GitHub Actions workflow + red PR proof + gate policy page |
| Guards-A I/O Validators | 3 | Feb 27 → Mar 14 | W1 Feb 27–28 adversarial.jsonl + input guards (dry-run) · W2 Mar 6–7 output guards + bounded reask · W3 Mar 13–14 FastAPI service + fail-closed proof + tuning report |
| Guards-B NeMo Rails (DEPTH) | 3 | Mar 20 → Apr 4 | W1 Mar 20–21 pinned setup + input/dialog rails (expect NeMo friction — it's budgeted) · W2 Mar 27–28 retrieval rails + poisoning ablation · W3 Apr 3–4 execution/output rails + config-only behavior demo |
| Phase close | 1 | Apr 10–11 | Q&A out loud + buffer |

**Checkpoint:** your RAG has a scored report, a CI gate that goes red, and an adversarial table.

## Phase 4 — Customization & Production (Apr → early Jul 2027)

| Project | Weekends | Window | Weekend-by-weekend |
| ------- | -------- | ------ | ------------------ |
| FT-A QLoRA SFT | 3 | Apr 17 → May 2 | W1 Apr 17–18 task + metric + locked held-out, dataset engineering starts · W2 Apr 24–25 dataset finish + smoke train + real SFT, loss curves · W3 May 1–2 merge → GGUF + before/after + adversarial re-check. Training runs on Colab T4 — queue jobs Saturday, evaluate Sunday |
| FT-B DPO (DEPTH) | 3 | May 8 → May 23 | W1 May 8–9 behavior targets + preference pairs + audit · W2 May 15–16 smoke DPO + β sweep · W3 May 22–23 win-rate + refusal repair + GGUF export |
| LLMOps-A Observability | 3 | May 29 → Jun 13 | W1 May 29–30 Langfuse stack + span instrumentation · W2 Jun 5–6 cost math + PII redaction + baselines.yml · W3 Jun 12–13 prompt A/B + ALERTS.md + handoff test |
| LLMOps-B Serving + gated CI/CD | 3 | Jun 19 → Jul 4 | W1 Jun 19–20 FastAPI serving + multi-stage Dockerfile · W2 Jun 26–27 minikube + probe drills (kill-a-pod, slow-start) · W3 Jul 3–4 eval-gated pipeline + canary both directions + release policy |
| Phase close | 1 | Jul 10–11 | Q&A + buffer |

**Checkpoint:** your own fine-tune, served on Kubernetes, deploys blocked by your own eval gate.

## Phase 5 — Synthesis & Frontier (Jul → Sep 2027)

| Item | Weekends | Window | Weekend-by-weekend |
| ---- | -------- | ------ | ------------------ |
| Frontier picks for the capstone (2–3 tracks) | 2 | Jul 17 → Jul 25 | Pick per capstone idea — §7 multimodal, §5 ACL retrieval, §8 cascade are common fits |
| **Capstone (§1)** | 5 | Jul 31 → Aug 29 | W1 Jul 31–Aug 1 scope/metrics doc + assemble unguarded happy path · W2 Aug 7–8 guards + adversarial sets on the assembled system · W3 Aug 14–15 tune-or-justify + capstone harness/gate · W4 Aug 21–22 serve + canary, keep it live · W5 Aug 28–29 write-up + demo + metrics page. §2 design write-ups fold into W2/W4 evenings |
| Remaining frontier (any order) | 3 | Sep 4 → Sep 19 | Sep 4–5, Sep 11–12, Sep 18–19. §3 distillation with local `deepseek-r1` traces is the highest-signal pick on your hardware |
| Final oral exam | — | Sep 18–19 | Phase-5 `Interview-Questions.md` Parts 1–3, out loud, against the live capstone |

**Done ≈ 19 Sep 2027** — just under a year from the Oct 12 start: a live URL, green CI, a metrics page, and twelve projects'
worth of measured tables behind it.

## If you add one weekday evening (optional)

~1 hour midweek absorbs all reading, Q&A prep, and note-polish — effectively buying back the
phase-close weeks and compressing the total toward ~10 months. Don't spend it building;
tired builds produce sloppy tables.
