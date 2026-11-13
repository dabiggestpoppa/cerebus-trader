# ACCEPTANCE.md

**BA-39 Rung 1 — Book V Interface Contract Hardening — Next Implementation Requirement Inventory**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `b7f595ea417954e94ac15409a626915cb50ef8dc`
**Mode:** Audit and planning only. No production UI. No gated F2/F3/F4
implementation.

## 1. Requirement inventory (derived from frozen Book V chapters)

The 25 BA-37 requirements remain the authoritative total. 12 are implemented
(BA-38). The remaining 13 are deferred pending gate closure. No new
requirements are invented in this rung.

### Implemented (12) — BA-38

| ID | Class | Chapter | Gate | Test | Status |
|---|---|---|---|---|---|
| BV-F1-01 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_renders_validated_answer` | Implemented |
| BV-F1-02 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_renders_governed_refusal` | Implemented |
| BV-F1-03 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_displays_answer_id` | Implemented |
| BV-F1-04 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_citation_shows_generation` | Implemented |
| BV-F1-05 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_shows_epistemic_label` | Implemented |
| BV-F1-06 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_shows_depth` | Implemented |
| BV-F1-07 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_shows_setup_verdict` | Implemented |
| BV-F1-08 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_refuses_unsupported_statistic` | Implemented |
| BV-F1-09 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_preserves_limitations` | Implemented |
| BV-F1-10 | F1 | BOOK_V_READINESS_GATE §4 | None | `test_bv_no_raw_draft_in_ui` | Implemented |
| BV-F2-01 | F2 | BOOK_V_READINESS_GATE §4 | None | `test_bv_refusal_component` | Implemented |
| BV-F2-03 | F2 | BOOK_V_READINESS_GATE §4 | None | `test_bv_depth_layout` | Implemented |

### Deferred (13) — gated, not implemented

| ID | Class | Chapter | Gate dependency | Test | Status |
|---|---|---|---|---|---|
| BV-F2-02 | F2 | CONTRACT_HANDOFF §7.4 | EV-GATE-02 (OPEN) | `test_bv_citation_renderer` | Deferred |
| BV-F2-04 | F2 | CONTRACT_HANDOFF §7.5 | EV-GATE-07 (OPEN) | `test_bv_current_state_indicator` | Deferred |
| BV-F3-01 | F3 | CONTRACT_HANDOFF §7.6 | EV-GATE-02 (OPEN) | `test_bv_citation_spec_ratified` | Deferred |
| BV-F3-02 | F3 | CONTRACT_HANDOFF §7.6 | EV-GATE-03 (OPEN) | `test_bv_materiality_threshold` | Deferred |
| BV-F3-03 | F3 | CONTRACT_HANDOFF §7.6 | EV-GATE-11 (OPEN) | `test_bv_refusal_precedence_ratified` | Deferred |
| BV-F3-04 | F3 | CONTRACT_HANDOFF §7.6 | EV-GATE-13 (OPEN) | `test_bv_launch_threshold` | Deferred |
| BV-F4-01 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-01 (OPEN) | `test_bv_live_provider` | Deferred |
| BV-F4-02 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-04 (OPEN) | `test_bv_book_vi_entitlement` | Deferred |
| BV-F4-03 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-07 (OPEN) | `test_bv_live_market_feed` | Deferred |
| BV-F4-04 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-08 (OPEN) | `test_bv_durable_snapshots` | Deferred |
| BV-F4-05 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-10 (OPEN) | `test_bv_semantic_index` | Deferred |
| BV-F4-06 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-06 (OPEN) | `test_bv_abuse_store` | Deferred |
| BV-F4-07 | F4 | CONTRACT_HANDOFF §7.7 | EV-GATE-12 (OPEN) | `test_bv_human_review` | Deferred |

### Feasibility totals

| Class | Total | Implemented | Deferred |
|---|---:|---:|---:|
| F1 | 10 | 10 | 0 |
| F2 | 4 | 2 | 2 |
| F3 | 4 | 0 | 4 |
| F4 | 7 | 0 | 7 |
| **Total** | **25** | **12** | **13** |

Mechanical verification:
- Contiguous IDs within each class: ✓ (F1-01…10, F2-01…04, F3-01…04, F4-01…07)
- Unique test names: ✓ (25 unique names)
- Complete requirement mapping: ✓ (every requirement maps to exactly one test)
- Complete scenario mapping: ✓ (19 golden scenarios map to requirements)
- Matching totals across documents: ✓ (ACCEPTANCE.md, BOOK_V_READINESS_GATE.md, CONTRACT_HANDOFF.md all agree)

## 2. Golden scenario mapping

| Golden scenario | Q5 case | Expected outcome | Requirement IDs | Test |
|---|---|---|---|---|
| BV-GOLDEN-01 | Q5-01 | VALIDATED_ANSWER | BV-F1-01, BV-F1-03, BV-F1-04, BV-F1-05, BV-F1-06 | `test_bv_golden_01` |
| BV-GOLDEN-02 | Q5-03 | VALIDATED_ANSWER | BV-F1-01, BV-F1-03, BV-F1-04, BV-F1-05, BV-F1-06, BV-F1-07 | `test_bv_golden_02` |
| BV-GOLDEN-03 | Q5-05 | VALIDATED_ANSWER | BV-F1-01, BV-F1-04, BV-F1-05, BV-F1-06 | `test_bv_golden_03` |
| BV-GOLDEN-04 | Q5-43 | GOVERNED_REFUSAL | BV-F1-02, BV-F1-09, BV-F2-01 | `test_bv_golden_04` |
| BV-GOLDEN-05 | Q5-44 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_05` |
| BV-GOLDEN-06 | Q5-42 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_06` |
| BV-GOLDEN-07 | Q5-41 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_07` |
| BV-GOLDEN-08 | Q5-25 | GOVERNED_REFUSAL | BV-F1-02, BV-F1-07, BV-F1-09, BV-F2-01 | `test_bv_golden_08` |
| BV-GOLDEN-09 | Q5-07 | GOVERNED_REFUSAL | BV-F1-02, BV-F1-08, BV-F2-01 | `test_bv_golden_09` |
| BV-GOLDEN-10 | Q5-31 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_10` |
| BV-GOLDEN-11 | Q5-34 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_11` |
| BV-GOLDEN-12 | Q5-08 | GOVERNED_REFUSAL | BV-F1-02, BV-F1-08 | `test_bv_golden_12` |
| BV-GOLDEN-13 | Q5-25 | GOVERNED_REFUSAL | BV-F1-02, BV-F1-07, BV-F1-09 | `test_bv_golden_13` |
| BV-GOLDEN-14 | Q5-43 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_14` |
| BV-GOLDEN-15 | Q5-05 | VALIDATED_ANSWER | BV-F1-01, BV-F1-04 | `test_bv_golden_15` |
| BV-GOLDEN-16 | Q5-19 | GOVERNED_REFUSAL | BV-F1-02 | `test_bv_golden_16` |
| BV-GOLDEN-17 | synthetic | GOVERNED_REFUSAL | BV-F1-02 | `test_bv_golden_17` |
| BV-GOLDEN-18 | Q5-39 | GOVERNED_REFUSAL | BV-F1-02, BV-F2-01 | `test_bv_golden_18` |
| BV-GOLDEN-19 | n/a | PRESENTATION_REJECTED | BV-F1-10 | `test_bv_golden_19` |

## 3. Admission criteria (next implementation phase)

A Book V requirement is accepted only when:

1. Its class gate dependency (if any) is closed with evidence, **and**
2. Its proposed exact test passes against the ratified DTO surfaces, **and**
3. All cross-cutting drivers pass:
   - `test_bv_no_gate_crossed_without_evidence`
   - `test_bv_dto_surfaces_are_read_only`
   - `test_bv_f07a_option_c_semantics`
   - `test_bv_deterministic_replay`
   - `test_bv_no_historical_to_current_promotion`
   - `test_bv_no_refusal_to_answer_conversion`
4. No non-acceptance condition is violated (see §4).

## 4. Non-acceptance conditions

Book V acceptance is **not** granted if any of the following is true:

1. Any F3/F4 requirement is exercised against its OPEN gate without evidence.
2. Book V introduces `ASK_ANSWER_CONTRACT_V2` or a consolidated
   `refusal_limitations` field (Option B deferred).
3. Book V bypasses `validate_answer` or renders a raw `GatewayDraft`.
4. Book V invents or recalculates a model statistic; an unsupported
   statistic renders a number instead of refusing `INSUFFICIENT_EVIDENCE`.
5. Book V promotes a historical model (`HISTORICAL`/`SUPERSEDED`/etc.) to a
   current executable setup.
6. Book V clears a no-go (`NO_GO_ACTIVE` not preserved).
7. Book V widens entitlement or leaks a protected identifier
   (`context_items`, `object_id`, `manifest_digest`, `row_id`, `credential`,
   `system prompt`).
8. Book V interprets missing market data as valid current data
   (`CURRENT_DATA_UNAVAILABLE` / `PROVIDER_NOT_CONFIGURED` not honored).
9. Book V converts a governed refusal into a successful answer or an
   `ERROR` into a refusal without fixing the cause.
10. Book V assumes BG-C operational readiness or treats BG-A/BG-B as implying
    BG-C.
11. Any cross-cutting driver fails.
12. The Book IV regression baseline regresses (must remain 0 failed).

## 5. Production release precondition

Acceptance of Book V **production release** additionally requires BG-C to
become PASS and all EV-GATE-01–13 to close with evidence. Until then, Book V
is admitted to deterministic, offline development only.

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED
