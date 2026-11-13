# RATIFICATION.md

**BA-38 Rung 2 — Book V Deterministic Interface Foundation — Ratification**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `55fef69a18fe9da2db81c55a06af413e68b0c28c`
**Ratified SHA:** `55fef69a18fe9da2db81c55a06af413e68b0c28c` (pre-implementation baseline)

## 1. Ratification decision

**Ratified: the deterministic Book V interface foundation.**

This rung ratifies the read-only presentation adapter that projects ratified
Book IV IV.5/IV.6 DTO surfaces (`ValidatedAnswer`, `GovernedAnswerRefusal`)
into the Book V interface model. The adapter is strictly read-only with
respect to Book IV's validated output and implements exactly the 12 admitted
requirements (BV-F1-01…BV-F1-10, BV-F2-01, BV-F2-03).

**Not ratified:** production deployment, live provider integration, Book VI/VII/VIII
dependencies, F3 governance items, F4 external integrations, or any behavior
depending on an OPEN EV-GATE or BG-C.

## 2. Implemented requirement IDs

| ID | Class | Test name | Status |
|---|---|---|---|
| BV-F1-01 | F1 | `test_bv_renders_validated_answer` | Ratified |
| BV-F1-02 | F1 | `test_bv_renders_governed_refusal` | Ratified |
| BV-F1-03 | F1 | `test_bv_displays_answer_id` | Ratified |
| BV-F1-04 | F1 | `test_bv_citation_shows_generation` | Ratified |
| BV-F1-05 | F1 | `test_bv_shows_epistemic_label` | Ratified |
| BV-F1-06 | F1 | `test_bv_shows_depth` | Ratified |
| BV-F1-07 | F1 | `test_bv_shows_setup_verdict` | Ratified |
| BV-F1-08 | F1 | `test_bv_refuses_unsupported_statistic` | Ratified |
| BV-F1-09 | F1 | `test_bv_preserves_limitations` | Ratified |
| BV-F1-10 | F1 | `test_bv_no_raw_draft_in_ui` | Ratified |
| BV-F2-01 | F2 | `test_bv_refusal_component` | Ratified |
| BV-F2-03 | F2 | `test_bv_depth_layout` | Ratified |

Plus 12 cross-cutting / phase-8 drivers, all passing.

## 3. Cross-cutting driver verification

| Driver | Test name | Result |
|---|---|---|
| No F3/F4 gate crossed without evidence | `test_bv_no_gate_crossed_without_evidence` | Pass |
| DTO surfaces are read-only | `test_bv_dto_surfaces_are_read_only` | Pass |
| F-07a Option C semantics | `test_bv_f07a_option_c_semantics` | Pass |
| Deterministic replay | `test_bv_deterministic_replay` | Pass |
| No historical-to-current promotion | `test_bv_no_historical_to_current_promotion` | Pass |
| No refusal-to-answer conversion | `test_bv_no_refusal_to_answer_conversion` | Pass |

## 4. F-07a Option C contract verification

The six ratified refusal codes are preserved verbatim through the presentation
adapter:

| Code | Test case | Depth | Result |
|---|---|---|---|
| `ACCESS_NOT_ENTITLED` | Q5-43 | OPERATOR | Preserved |
| `AMBIGUOUS_SCOPE` | Q5-44 | BEGINNER | Preserved |
| `MODEL_VERSION_UNAVAILABLE` | Q5-42 | RESEARCHER | Preserved |
| `CURRENT_DATA_UNAVAILABLE` | Q5-41 | OPERATOR | Preserved |
| `SETUP_NOT_ENCODED` | Q5-25 | OPERATOR | Preserved |
| `INSUFFICIENT_EVIDENCE` | Q5-07 | OPERATOR | Preserved |

For each refusal: correct user-visible status (GOVERNED_REFUSAL), correct
primary reason (`code`), safe detail (`detail`), relevant inherited
limitations (`limitations`), no internal identifier disclosure, no unsafe
execution guidance, no misleading success state. Empty `limitations` tuple is
preserved as empty and is not treated as evidence of no refusal reason.

## 5. Deferred requirements

| ID | Class | Gate dependency | Reason deferred |
|---|---|---|---|
| BV-F2-02 | F2 | EV-GATE-02 | Citation-surface presentation spec not ratified |
| BV-F2-04 | F2 | EV-GATE-07 | Live market data not configured |
| BV-F3-01 | F3 | EV-GATE-02 | Governance decision pending |
| BV-F3-02 | F3 | EV-GATE-03 | Materiality policy not ratified |
| BV-F3-03 | F3 | EV-GATE-11 | Refusal-precedence ratification pending |
| BV-F3-04 | F3 | EV-GATE-13 | Launch threshold table not defined |
| BV-F4-01 | F4 | EV-GATE-01 | Live LLM provider not authorized |
| BV-F4-02 | F4 | EV-GATE-04 | Book VI commercial entitlement open |
| BV-F4-03 | F4 | EV-GATE-07 | Real current-market data feed not licensed |
| BV-F4-04 | F4 | EV-GATE-08 | Durable historical snapshot store not built |
| BV-F4-05 | F4 | EV-GATE-10 | Real semantic retrieval index not available |
| BV-F4-06 | F4 | EV-GATE-06 | Shared abuse store not implemented |
| BV-F4-07 | F4 | EV-GATE-12 | Human/operator review execution open |

## 6. Open EV-GATE dependencies

All 13 EV-GATEs (EV-GATE-01 through EV-GATE-13) remain OPEN. No gate is
closed by fixture-only success. Production release is blocked until BG-C
becomes PASS and all EV-GATEs close with evidence.

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED

## 7. Non-ratification

This ratification does **not** cover:

- Production deployment of any Book V component.
- `ASK_ANSWER_CONTRACT_V2` or a consolidated `refusal_limitations` field
  (Option B deferred).
- Any bypass of `validate_answer` (IV.5).
- Any rendering of raw `GatewayDraft` provider output.
- Any invention or recalculation of model statistics.
- Any promotion of historical evidence to current.
- Any clearing of a no-go (`NO_GO_ACTIVE`).
- Any widening of entitlement or leakage of protected identifiers.
- Any interpretation of missing market data as valid current data.
- Any conversion of a governed refusal into a successful answer.
