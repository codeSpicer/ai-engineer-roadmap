# Pacing Plan — Phases 2–5 (weekends-only, alongside a 9–5)

**Calibration:** Phase 1 took ~1 month for 2 beginner projects at weekends-only. Phase 2–4
projects are bigger (5–6 build phases each), so budgets below are 2–3 weekends per project at
**~3 scheduled weekends per month** — the 4th weekend is life/buffer. Plan on 75% availability,
not 100%.

**Start:** Sat 12 Sep 2026 · **Horizon:** ~12 months → capstone live ~Sep 2027.

## Rules that matter more than dates

1. **DoD-gated, not calendar-gated.** A project is done when its Definition of Done is met and
   its tables are filled — not when its weekends run out. Slip the next block before you skip an
   ablation table; the tables are your interview capital.
2. **Friday-night setup (15–30 min):** read the coming build phase's checkboxes, queue
   `ollama pull` / `pip install`. Saturday morning should start *building*, not downloading.
3. **Sunday closeout (15 min):** fill the "Observations worth writing down" bullets while fresh —
   they become interview answers verbatim.
4. **Re-calibrate after RAG-A.** It's your first intermediate project — your actual weekend count
   there resets every later budget. Update the dates below once it's done.
5. **Spine vs depth.** If you slip >2 weeks, defer DEPTH items (RAG-B, Agents-B, Guards-B, FT-B,
   extra frontier tracks) to *after* the capstone — defer, never skip silently. Never defer:
   RAG-A, Agents-A, Evals-A, Evals-B (LLMOps-B imports its gate), Guards-A, FT-A, LLMOps-A/B,
   the capstone, and the §2 design write-ups.

## Phase 2 — Building AI Apps (Sep → mid-Dec 2026)

| Project | Weekends | Window | Weekend-by-weekend |
| ------- | -------- | ------ | ------------------ |
| RAG-A Hybrid Search | 3 | Sep 12 → Sep 27 | W1 corpus + golden.jsonl first, ingestion reused from semantic-search · W2 BM25 + RRF fusion, per-type win records · W3 reranker + grounded generation + abstention, ablation table |
| RAG-B Agentic/Graph (DEPTH) | 3 | Oct 3 → Oct 18 | W1 extended golden set + router · W2 decompose + graph build · W3 confidence retry + trajectory report |
| Agents-A ReAct + MCP | 3 | Oct 24 → Nov 8 | W1 task set + tools/schemas, unit-tested · W2 the loop + error-as-observation · W3 MCP wiring + trace report |
| Agents-B Multi-Agent (DEPTH) | 3 | Nov 14 → Nov 29 | W1 workers + state/reducers standalone · W2 graph + supervisor routing · W3 checkpoint kill-test + HITL gate + report |
| Phase close | 1–2 | Dec 5 → Dec 13 | Both `Interview-Questions.md` out loud, README tables tidy, overflow buffer. Late Dec: off |

**Checkpoint:** you can whiteboard hybrid RAG and an agent loop, with your own numbers attached.

## Phase 3 — Quality & Safety (Jan → Mar 2027)

| Project | Weekends | Window | Weekend-by-weekend |
| ------- | -------- | ------ | ------------------ |
| Evals-A Harness | 3 | Jan 9 → Jan 24 | W1 curated golden set + synthetic gen + audit · W2 deterministic recall@k/MRR, 3 configs · W3 Ragas judge metrics + judge-vs-human validation + comparison report |
| Evals-B CI Gate | 2 | Jan 30 → Feb 7 | W1 eval cases as pytest + custom criteria, green locally, red-team locally · W2 GitHub Actions workflow + red PR proof + gate policy page |
| Guards-A I/O Validators | 3 | Feb 13 → Feb 28 | W1 adversarial.jsonl + input guards (dry-run) · W2 output guards + bounded reask · W3 FastAPI service + fail-closed proof + tuning report |
| Guards-B NeMo Rails (DEPTH) | 3 | Mar 6 → Mar 21 | W1 pinned setup + input/dialog rails (expect NeMo friction — it's budgeted) · W2 retrieval rails + poisoning ablation · W3 execution/output rails + config-only behavior demo |
| Phase close | 1 | Mar 27 | Q&A out loud + buffer |

**Checkpoint:** your RAG has a scored report, a CI gate that goes red, and an adversarial table.

## Phase 4 — Customization & Production (Apr → early Jul 2027)

| Project | Weekends | Window | Weekend-by-weekend |
| ------- | -------- | ------ | ------------------ |
| FT-A QLoRA SFT | 3 | Apr 10 → Apr 25 | W1 task + metric + locked held-out, dataset engineering starts · W2 dataset finish + smoke train + real SFT, loss curves · W3 merge → GGUF + before/after + adversarial re-check. Training runs on Colab T4 — queue jobs Saturday, evaluate Sunday |
| FT-B DPO (DEPTH) | 3 | May 1 → May 16 | W1 behavior targets + preference pairs + audit · W2 smoke DPO + β sweep · W3 win-rate + refusal repair + GGUF export |
| LLMOps-A Observability | 3 | May 22 → Jun 6 | W1 Langfuse stack + span instrumentation · W2 cost math + PII redaction + baselines.yml · W3 prompt A/B + ALERTS.md + handoff test |
| LLMOps-B Serving + gated CI/CD | 3 | Jun 12 → Jun 27 | W1 FastAPI serving + multi-stage Dockerfile · W2 minikube + probe drills (kill-a-pod, slow-start) · W3 eval-gated pipeline + canary both directions + release policy |
| Phase close | 1 | Jul 3 | Q&A + buffer |

**Checkpoint:** your own fine-tune, served on Kubernetes, deploys blocked by your own eval gate.

## Phase 5 — Synthesis & Frontier (Jul → Sep 2027)

| Item | Weekends | Window | Weekend-by-weekend |
| ---- | -------- | ------ | ------------------ |
| Frontier picks for the capstone (2–3 tracks) | 2 | Jul 10 → Jul 18 | Pick per capstone idea — §7 multimodal, §5 ACL retrieval, §8 cascade are common fits |
| **Capstone (§1)** | 5 | Jul 24 → Aug 22 | W1 scope/metrics doc + assemble unguarded happy path · W2 guards + adversarial sets on the assembled system · W3 tune-or-justify + capstone harness/gate · W4 serve + canary, keep it live · W5 write-up + demo + metrics page. §2 design write-ups fold into W2/W4 evenings |
| Remaining frontier (any order) | 3 | Aug 28 → Sep 12 | §3 distillation with local `deepseek-r1` traces is the highest-signal pick on your hardware |
| Final oral exam | — | Sep 11–12 | Phase-5 `Interview-Questions.md` Parts 1–3, out loud, against the live capstone |

**Done ≈ 12 Sep 2027** — one year in: a live URL, green CI, a metrics page, and twelve projects'
worth of measured tables behind it.

## If you add one weekday evening (optional)

~1 hour midweek absorbs all reading, Q&A prep, and note-polish — effectively buying back the
phase-close weeks and compressing the total toward ~10–11 months. Don't spend it building;
tired builds produce sloppy tables.
