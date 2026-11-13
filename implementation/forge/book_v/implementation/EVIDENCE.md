# EVIDENCE.md

**BA-38 Rung 2 — Book V Deterministic Interface Foundation — Evidence Record**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `55fef69a18fe9da2db81c55a06af413e68b0c28c`
**Mode:** Deterministic implementation only. No production code. No Book IV
behavior changes. No routes, migrations, or provider credentials.

## 1. Admitted requirement IDs

Implemented (12 of 25 total requirements):

| ID | Class | Requirement | Gate dependency | Status |
|---|---|---|---|---|
| BV-F1-01 | F1 | Render `ValidatedAnswer` sections/claims/citations | None | Implemented |
| BV-F1-02 | F1 | Render `GovernedAnswerRefusal` code/detail/findings | None | Implemented |
| BV-F1-03 | F1 | Display `answer_id` | None | Implemented |
| BV-F1-04 | F1 | Preserve model generation in citations | None | Implemented |
| BV-F1-05 | F1 | Preserve epistemic status (HISTORICAL etc.) | None | Implemented |
| BV-F1-06 | F1 | Display answer depth | None | Implemented |
| BV-F1-07 | F1 | Display setup eligibility verdict | None | Implemented |
| BV-F1-08 | F1 | Refuse unsupported statistic (no invented number) | None | Implemented |
| BV-F1-09 | F1 | Preserve `limitations` as inherited restrictions | None | Implemented |
| BV-F1-10 | F1 | Never render raw provider draft | None | Implemented |
| BV-F2-01 | F2 | Build refusal presentation component | None | Implemented |
| BV-F2-03 | F2 | Build depth-aware answer layout | None | Implemented |

Deferred (gated, not implemented):

| ID | Class | Requirement | Gate dependency | Status |
|---|---|---|---|---|
| BV-F2-02 | F2 | Build citation renderer (bounded, attributed) | EV-GATE-02 (OPEN) | Deferred |
| BV-F2-04 | F2 | Build current-state availability indicator | EV-GATE-07 (OPEN) | Deferred |
| BV-F3-01 | F3 | Define citation-surface presentation spec | EV-GATE-02 (OPEN) | Deferred |
| BV-F3-02 | F3 | Define materiality / false-refusal threshold | EV-GATE-03 (OPEN) | Deferred |
| BV-F3-03 | F3 | Ratify refusal-precedence for Book V surface | EV-GATE-11 (OPEN) | Deferred |
| BV-F3-04 | F3 | Define launch threshold table (SCORING_V1 metrics) | EV-GATE-13 (OPEN) | Deferred |
| BV-F4-01 | F4 | Integrate live LLM provider | EV-GATE-01 (OPEN) | Deferred |
| BV-F4-02 | F4 | Integrate Book VI commercial entitlement | EV-GATE-04 (OPEN) | Deferred |
| BV-F4-03 | F4 | Integrate real current-market data feed | EV-GATE-07 (OPEN) | Deferred |
| BV-F4-04 | F4 | Integrate durable historical snapshot store | EV-GATE-08 (OPEN) | Deferred |
| BV-F4-05 | F4 | Integrate real semantic retrieval index | EV-GATE-10 (OPEN) | Deferred |
| BV-F4-06 | F4 | Integrate shared abuse store + rate/aggregation | EV-GATE-06 (OPEN) | Deferred |
| BV-F4-07 | F4 | Execute human/operator review (EV-117–EV-120) | EV-GATE-12 (OPEN) | Deferred |

## 2. Implemented modules

| Module | Purpose | Lines |
|---|---|---|
| `app/forge/book_v/__init__.py` | Book V package marker | ~6 |
| `app/forge/book_v/presentation/__init__.py` | Package exports | ~12 |
| `app/forge/book_v/presentation/versions.py` | Frozen presentation contract versions | ~8 |
| `app/forge/book_v/presentation/model.py` | `BookVInterfaceResponse` + element dataclasses; deterministic `payload()` serialization | ~110 |
| `app/forge/book_v/presentation/adapter.py` | `PresentationAdapter`: read-only projection of `ValidatedAnswer` / `GovernedAnswerRefusal`; `PresentationRejectionError` for non-DTO input | ~100 |
| `tests/test_forge_book_v_presentation.py` | 24 acceptance drivers (12 requirements + 6 cross-cutting + 6 phase-8 cross-cutting) | ~600 |

## 3. DTO mappings

Book V copies IV.5 DTO fields verbatim. No field is extended, retyped, or
supplemented.

### `ValidatedAnswer` → `BookVInterfaceResponse` (outcome = VALIDATED_ANSWER)

| IV.5 field | Presentation field | Preserved? |
|---|---|---|
| `answer_id` | `answer_id` | Yes (verbatim) |
| `depth` | `depth` | Yes (verbatim) |
| `sections[].section_id` | `sections[].section_id` | Yes (verbatim, depth order preserved) |
| `sections[].heading` | `sections[].heading` | Yes (verbatim) |
| `sections[].bullets` | `sections[].bullets` | Yes (verbatim) |
| `sections[].claim_ids` | `sections[].claim_ids` | Yes (verbatim) |
| `claims[].claim_id` | `claims[].claim_id` | Yes (verbatim) |
| `claims[].text` | `claims[].text` | Yes (verbatim) |
| `claims[].section_id` | `claims[].section_id` | Yes (verbatim) |
| `claims[].epistemic_label` | `claims[].epistemic_label` | Yes (verbatim) |
| `claims[].layer` | `claims[].layer` | Yes (verbatim) |
| `claims[].generation` | `claims[].generation` | Yes (verbatim) |
| `claims[].source_refs` | `claims[].source_refs` | Yes (verbatim) |
| `claims[].citation_ids` | `claims[].citation_ids` | Yes (verbatim) |
| `citations[].source_ref_id` | `citations[].source_ref_id` | Yes (verbatim, never internal row/object id) |
| `citations[].source_ref_type` | `citations[].source_ref_type` | Yes (verbatim) |
| `citations[].source_status` | `citations[].source_status` | Yes (verbatim) |
| `citations[].provenance_refs` | `citations[].provenance_refs` | Yes (verbatim) |
| `citations[].evidence_refs` | `citations[].evidence_refs` | Yes (verbatim) |
| `citations[].generation` | `citations[].generation` | Yes (verbatim) |
| `numbers[].value_text` | `numbers[].value_text` | Yes (verbatim) |
| `numbers[].unit` | `numbers[].unit` | Yes (verbatim) |
| `numbers[].source_ref_id` | `numbers[].source_ref_id` | Yes (verbatim) |
| `numbers[].normalized` | `numbers[].normalized` | Yes (verbatim) |
| `limitations` | `limitations` | Yes (verbatim, inherited restrictions) |
| `as_of` | `as_of` | Yes (verbatim) |
| `record` | `record` | Yes (safe identity subset only — no provider/model/latency/cost/prompt internals) |

### `GovernedAnswerRefusal` → `BookVInterfaceResponse` (outcome = GOVERNED_REFUSAL)

| IV.5 field | Presentation field | Preserved? | F-07a Option C role |
|---|---|---|---|
| `answer_id` | `answer_id` | Yes (verbatim) | — |
| `code` | `code` | Yes (verbatim) | Primary governed refusal reason |
| `detail` | `detail` | Yes (verbatim) | Consumer-safe explanatory prose |
| `depth` | `depth` | Yes (verbatim) | — |
| `findings` | `findings` | Yes (verbatim) | Supporting validation findings |
| `limitations` | `limitations` | Yes (verbatim) | Inherited context restrictions (may be empty) |
| `record` | `record` | Yes (safe identity subset) | — |

### Rejected inputs

| Input type | Result |
|---|---|
| `ValidatedAnswer` | Projected successfully |
| `GovernedAnswerRefusal` | Projected successfully |
| `GatewayDraft` | `PresentationRejectionError` (raw provider draft never reaches UI) |
| `None`, `str`, `int`, `list`, `dict`, any other | `PresentationRejectionError` |

## 4. Test inventory

### Admitted requirement tests (12)

| Test name | Requirement | Purpose |
|---|---|---|
| `test_bv_renders_validated_answer` | BV-F1-01 | ValidatedAnswer sections/claims/citations render |
| `test_bv_renders_governed_refusal` | BV-F1-02 | GovernedAnswerRefusal code/detail/findings render |
| `test_bv_displays_answer_id` | BV-F1-03 | answer_id preserved and displayed |
| `test_bv_citation_shows_generation` | BV-F1-04 | Model generation preserved on citations |
| `test_bv_shows_epistemic_label` | BV-F1-05 | Epistemic status preserved per claim |
| `test_bv_shows_depth` | BV-F1-06 | Answer depth preserved |
| `test_bv_shows_setup_verdict` | BV-F1-07 | Setup eligibility verdict preserved |
| `test_bv_refuses_unsupported_statistic` | BV-F1-08 | Unsupported statistic refuses; no number rendered |
| `test_bv_preserves_limitations` | BV-F1-09 | limitations preserved as inherited restrictions |
| `test_bv_no_raw_draft_in_ui` | BV-F1-10 | Raw GatewayDraft rejected; never reaches UI |
| `test_bv_refusal_component` | BV-F2-01 | Refusal presentation component renders code/detail/limitations per Option C |
| `test_bv_depth_layout` | BV-F2-03 | Depth-aware layout preserves IV.5 section order |

### Cross-cutting drivers (6)

| Test name | Purpose |
|---|---|
| `test_bv_no_gate_crossed_without_evidence` | No F3/F4 requirement exercised against OPEN gate |
| `test_bv_dto_surfaces_are_read_only` | Book V does not extend or retype IV.5/IV.6 DTOs |
| `test_bv_f07a_option_c_semantics` | code/detail/limitations read together per Option C; empty limitations legal |
| `test_bv_deterministic_replay` | Same input → same output across executions |
| `test_bv_no_historical_to_current_promotion` | No historical model promoted to current |
| `test_bv_no_refusal_to_answer_conversion` | Refusals stay refusals; ERROR reserved for unexpected exceptions |

### Phase 8 cross-cutting (6)

| Test name | Purpose |
|---|---|
| `test_bv_historical_generation_preserved` | Historical model generation preserved |
| `test_bv_no_go_preserved` | NO_GO_ACTIVE survives into answer surface |
| `test_bv_entitlement_preserved` | ACCESS_NOT_ENTITLED enforced; no privileged citation leak |
| `test_bv_no_fabricated_numerical_claims` | No invented statistics |
| `test_bv_malformed_input_rejection` | Malformed input rejected deterministically |
| `test_bv_six_code_refusal_preservation` | All six IV.5 refusal codes preserved verbatim |

**Total: 24 tests, 0 skipped, 0 xfail, 0 placeholders, 0 empty tests.** Every test contains a meaningful behavioral assertion.

## 5. Golden fixture inventory

19 golden scenarios under `implementation/forge/book_v/golden/scenarios.py`:

| ID | Q5 source | Expected outcome | Expected code | Depth | Requirement IDs |
|---|---|---|---|---|---|
| BV-GOLDEN-01 | Q5-01 | VALIDATED_ANSWER | — | BEGINNER | BV-F1-01, BV-F1-03, BV-F1-04, BV-F1-05, BV-F1-06 |
| BV-GOLDEN-02 | Q5-03 | VALIDATED_ANSWER | — | OPERATOR | BV-F1-01, BV-F1-03, BV-F1-04, BV-F1-05, BV-F1-06, BV-F1-07 |
| BV-GOLDEN-03 | Q5-05 | VALIDATED_ANSWER | — | RESEARCHER | BV-F1-01, BV-F1-04, BV-F1-05, BV-F1-06 |
| BV-GOLDEN-04 | Q5-43 | GOVERNED_REFUSAL | ACCESS_NOT_ENTITLED | OPERATOR | BV-F1-02, BV-F1-09, BV-F2-01 |
| BV-GOLDEN-05 | Q5-44 | GOVERNED_REFUSAL | AMBIGUOUS_SCOPE | BEGINNER | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-06 | Q5-42 | GOVERNED_REFUSAL | MODEL_VERSION_UNAVAILABLE | RESEARCHER | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-07 | Q5-41 | GOVERNED_REFUSAL | CURRENT_DATA_UNAVAILABLE | OPERATOR | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-08 | Q5-25 | GOVERNED_REFUSAL | SETUP_NOT_ENCODED | OPERATOR | BV-F1-02, BV-F1-07, BV-F1-09, BV-F2-01 |
| BV-GOLDEN-09 | Q5-07 | GOVERNED_REFUSAL | INSUFFICIENT_EVIDENCE | OPERATOR | BV-F1-02, BV-F1-08, BV-F2-01 |
| BV-GOLDEN-10 | Q5-31 | GOVERNED_REFUSAL | CURRENT_DATA_UNAVAILABLE | BEGINNER | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-11 | Q5-34 | GOVERNED_REFUSAL | CURRENT_DATA_UNAVAILABLE | OPERATOR | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-12 | Q5-08 | GOVERNED_REFUSAL | INSUFFICIENT_EVIDENCE | RESEARCHER | BV-F1-02, BV-F1-08 |
| BV-GOLDEN-13 | Q5-25 | GOVERNED_REFUSAL | SETUP_NOT_ENCODED | OPERATOR | BV-F1-02, BV-F1-07, BV-F1-09 |
| BV-GOLDEN-14 | Q5-43 | GOVERNED_REFUSAL | ACCESS_NOT_ENTITLED | OPERATOR | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-15 | Q5-05 | VALIDATED_ANSWER | — | RESEARCHER | BV-F1-01, BV-F1-04 |
| BV-GOLDEN-16 | Q5-19 | GOVERNED_REFUSAL | INSUFFICIENT_EVIDENCE | OPERATOR | BV-F1-02 |
| BV-GOLDEN-17 | synthetic | GOVERNED_REFUSAL | INSUFFICIENT_EVIDENCE | RESEARCHER | BV-F1-02 |
| BV-GOLDEN-18 | Q5-39 | GOVERNED_REFUSAL | ACCESS_NOT_ENTITLED | OPERATOR | BV-F1-02, BV-F2-01 |
| BV-GOLDEN-19 | n/a | PRESENTATION_REJECTED | — | — | BV-F1-10 |

Each scenario records a unique ID, pinned input digest (SHA-256 of the IV.5 DTO
payload), expected outcome, expected presentation fields, requirement mapping,
and test mapping. No EV-001–EV-178 or Q1–Q5 fixtures were mutated.

## 6. Security boundaries verified

- Read-only projection only: cannot clear a no-go, promote historical to
  current, substitute model generation, remove status labels, change setup
  eligibility, expand entitlement, produce trade sizing, issue execution
  instructions, invent statistics, render untrusted text as authority, or
  recover discarded proposed prose.
- Malformed or unauthorized inputs (including raw `GatewayDraft`) are rejected
  deterministically via `PresentationRejectionError`.
- No internal provider or retrieval material is projected: `provider`,
  `model`, `latency_ms`, `cost_usd`, `cost_basis`, `prompt_id`,
  `prompt_version` are excluded from the projected `record`.
- No protected identifiers (`context_items`, `object_id`, `manifest_digest`,
  `row_id`, `credential`, `system prompt`) appear in `code`, `detail`, or
  `limitations`.
- No citation `source_ref_id` is an internal row or object id.
- Citation surface is bounded to ratified safe fields only; EV-GATE-02
  citation-surface spec is deferred.

## 7. Regression results

| Suite | Result |
|---|---|
| Full repository regression | 2,721 passed / 0 failed / 29 skipped |
| Book V presentation tests | 24 passed / 0 failed / 0 skipped |
| IV.5 suite (`test_forge_ask_cerebus_answer.py`) | Unchanged (included in full regression) |
| IV.6 suite (`test_forge_ask_cerebus_evaluation.py`) | Unchanged (included in full regression) |
| Security Amendment 1 tests | Unchanged (included in full regression) |
| Historical Lineage Amendment 1 tests | Unchanged (included in full regression) |
| 17 hash guards | Unchanged (included in full regression) |
| Frozen upstream hashes (test_a74) | PASS — no Book IV production source changed |
| Routes | PASS — no route changes |
| Migrations | PASS — 001–004 unchanged |
| Credentials | PASS — no credential changes |
| Frozen fixtures | PASS — EV-001–EV-178 and Q1–Q5 unmutated |
| New API endpoints | PASS — no new endpoints added |
| Live provider invocation | PASS — no provider invoked |

## 8. Known limitations

- Book V does not implement a live citation renderer (BV-F2-02 deferred
  pending EV-GATE-02).
- Book V does not implement a current-state availability indicator
  (BV-F2-04 deferred pending EV-GATE-07).
- Book V does not implement F3 governance items (citation-surface spec,
  materiality threshold, refusal-precedence ratification, launch threshold
  table).
- Book V does not implement F4 external integrations (live provider, Book VI
  entitlement, market data feed, durable snapshots, semantic index, abuse
  store, human review).
- Book V is deterministic and offline-only; no production deployment is
  ratified by this rung.

## 9. Deferred requirements

All F3 and F4 requirements plus BV-F2-02 and BV-F2-04 remain deferred pending
their respective EV-GATE closures. See RATIFICATION.md section 5.

## 10. Open EV-GATE dependencies

| Gate | Status | Blocks |
|---|---|---|
| EV-GATE-01 | OPEN | BV-F4-01 (live provider) |
| EV-GATE-02 | OPEN | BV-F2-02, BV-F3-01 |
| EV-GATE-03 | OPEN | BV-F3-02 |
| EV-GATE-04 | OPEN | BV-F4-02 |
| EV-GATE-05 | OPEN | — |
| EV-GATE-06 | OPEN | BV-F4-06 |
| EV-GATE-07 | OPEN | BV-F2-04, BV-F4-03 |
| EV-GATE-08 | OPEN | BV-F4-04 |
| EV-GATE-09 | OPEN | — |
| EV-GATE-10 | OPEN | BV-F4-05 |
| EV-GATE-11 | OPEN | BV-F3-03 |
| EV-GATE-12 | OPEN | BV-F4-07 |
| EV-GATE-13 | OPEN | BV-F3-04 |

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED
