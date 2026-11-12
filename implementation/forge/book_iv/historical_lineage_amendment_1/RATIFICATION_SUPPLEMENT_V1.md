# RATIFICATION_SUPPLEMENT_V1

**BA-35 Rung 2 — Historical-Lineage Amendment 1.**
**Branch:** `forge` · **Starting HEAD:** `75f765f7547ebfeb89d9af75233a3b5820087bef` · **Mode:** institutional, evidence-first, append-only.
**Supplements:** BA-34 `RATIFICATION_SUPPLEMENT_V2.md` (F-06/F-07 PASS, F-07a/F-09 OPEN).

This document records the Rung 2 verdicts. It does not rewrite the original BA-35 audit.

## 1. Verdicts

| Item | Verdict | Basis |
|---|---|---|
| F-09 — IV.2 historical-intelligence routing repair | **PASS** | 28/28 drivers (R01–R28); H1–H3 reach governed answer path; zero `ERROR`; historical explanations answer, unsupported statistics refuse `INSUFFICIENT_EVIDENCE` |
| F-09b — IV.6 refusal-composition repair | **PASS** | No `None` reaches `validate_answer`; governed admission failures preserved as `GOVERNED_REFUSAL`; no unexpected exception mislabeled as refusal |
| F-10 — unmapped-intent harness behaviour | **PASS (negative control)** | `INDICATOR_NAVIGATION` yields governed `ROUTE_UNSUPPORTED`, matching product; no new IV.4 task implemented |
| F-07a — semantic contract (Option C) | **PASS** | 14/14 verification drivers (A01–A15); zero payload change; `REFUSAL_CONSUMER_CONTRACT_V1.md` ratified |
| Security non-regression (AM1-R01–R27, EC-01–EC-30) | **PASS** | Original 27 security-amendment drivers + 30 coverage drivers green; no new provider or authorization privileges |

## 2. Authorized source diff

| File | Change | Nature |
|---|---|---|
| `app/forge/ask_cerebus/retrieval/service.py` | Intelligence trigger narrowed to `requires_live_intelligence OR time_scope in {CURRENT, AS_OF}` (`HISTORICAL_RESEARCH` removed) | Behavioural amendment; one condition |
| `app/forge/ask_cerebus/evaluation/harness.py` | `_chain_gateway` returns `AdmissionFailure` instead of `None`; `_run_chain` routes it via `validate_answer` → `GovernedAnswerRefusal` | Evaluation-infrastructure composition fix |

No other source files modified. Book I, Book II, IV.1, IV.3, IV.4, IV.5, original IV.6 oracle, migrations, routes, `.gitattributes` untouched.

## 3. Hash-pin conflict (Section 12)

The IV.2 change alters `app/forge/ask_cerebus/retrieval/service.py`, which is pinned by BA-33 hash guards and upstream pins (x006, x010, AM1-R27). The following checks report the changed file as a conflict — this is the **documented, authorized** signal, not a regression:

- `test_x006_frozen_upstream_hashes_are_unchanged` — `retrieval/service.py` blob id changed
- `test_am1_r27_hash_guards_are_checkout_encoding_invariant` — `retrieval/service.py`
- `test_c88_frozen_iv2_bundle_refs_trace_unchanged` — `retrieval/service.py`
- `test_only_authorized_frozen_files_changed` — `retrieval/service.py`

Per Section 12 these are **not silently rebaselined**. A separately governed hash-pin amendment is required to update the pins for `retrieval/service.py`. All four checks fail solely on that file; every behavioural test passes.

## 4. Full regression

Baseline (starting HEAD): **2,654 passed / 0 failed / 29 skipped.**
Rung 2 head: **2,692 passed / 4 failed / 29 skipped.**

The 4 failures are exactly the hash-pin conflicts in §3 (all on `retrieval/service.py`). 42 new drivers were added (28 F-09 + 14 F-07a), all passing. No behavioural regression.

## 5. BG-A / BG-B / BG-C

| Gate | Verdict | Basis |
|---|---|---|
| BG-A deterministic completeness | **PASS** | unchanged; deterministic fixture execution, no stage errors |
| BG-B end-to-end evidence integrity | **PASS** | unchanged; 0 S1 findings, correct refusal rates preserved |
| BG-C operational readiness | **BLOCKED** | unchanged; no provider, market, entitlement or retention work (not authorized this rung) |

BG-A/BG-B are deterministic-fixture results, not production readiness; BG-C cannot pass in this rung and is not inferred from BG-A/BG-B.

## 6. EV-GATE-01–13

**OPEN** (unchanged). `EV-GATE-12` human review not discharged. No closure claimed by this rung.

## 7. Deliverables created

- `tests/test_forge_ask_cerebus_historical_lineage.py` — F-09 drivers R01–R28
- `tests/test_forge_ask_cerebus_f07a.py` — F-07a verification A01–A15
- `implementation/forge/book_iv/bloc_iv_6/fixtures_v3/` — EV-155–EV-178 corpus (digest `ee9cbf30…22657`)
- `implementation/forge/book_iv/historical_lineage_amendment_1/REFUSAL_CONSUMER_CONTRACT_V1.md` — F-07a Option C contract
- `IMPLEMENTATION_EVIDENCE.md`, `SUPPLEMENTAL_EVALUATION.md`, `RATIFICATION_SUPPLEMENT_V1.md` (this document)

## 8. Not done (out of scope for this rung)

- Book V implementation (deferred).
- `ASK_ANSWER_CONTRACT_V2` / Option B `refusal_limitations` (deferred).
- Production deployment (not authorized).
- Live market-data provider or real historical-data infrastructure (not authorized).
- Rebaselining the `retrieval/service.py` hash pins (requires separate governed amendment).
