# PRESENTATION_AUDIT.md

**BA-39 Rung 1 — Book V Interface Contract Hardening — Presentation Audit**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `b7f595ea417954e94ac15409a626915cb50ef8dc`
**Mode:** Audit and planning only. No production UI. No gated F2/F3/F4
implementation. No Book IV production behavior changes.

## 1. Foundation verification (Phase 0)

| Check | Result |
|---|---|
| HEAD equals `origin/forge` | PASS (`b7f595e...`) |
| HEAD equals required SHA | PASS (`b7f595e...`) |
| Append-only ancestry | PASS (merge-base == HEAD) |
| Clean worktree | PASS |
| Full regression | 2,721 passed / 0 failed / 29 skipped |
| 17 canonical hash guards | PASS (test_a74) |
| 178 evaluation fixtures (EV-001–178) | PASS (IV.6 suite green) |
| Q1–Q5 frozen fixtures (IV.5) | PASS (46 scenarios green) |
| BA-37 closure documents | Verified (unchanged) |
| BA-38 implementation evidence | Verified (unchanged) |
| Routes unchanged | PASS |
| Migrations 001–004 unchanged | PASS |
| Book II provider boundary unchanged | PASS |

## 2. Adapter contract inventory

### 2.1 Modules

| Module | Purpose |
|---|---|
| `app/forge/book_v/presentation/adapter.py` | `PresentationAdapter` + `PresentationRejectionError` |
| `app/forge/book_v/presentation/model.py` | `BookVInterfaceResponse` + element dataclasses; deterministic `payload()` |
| `app/forge/book_v/presentation/versions.py` | Frozen contract versions |

### 2.2 Verified properties (Phase 1)

| # | Property | Status | Evidence |
|---|---|---|---|
| 1 | Accepts only ratified DTOs (`ValidatedAnswer`, `GovernedAnswerRefusal`) | PASS | `isinstance` checks; `PresentationRejectionError` otherwise |
| 2 | Validated answers cannot become refusals | PASS | `test_adversarial_outcome_never_flips` |
| 3 | Refusals cannot become successful answers | PASS | `test_adversarial_outcome_never_flips` |
| 4 | Answer IDs preserved exactly | PASS | `test_bv_displays_answer_id`, `test_bv_golden_*` |
| 5 | Depth preserved | PASS | `test_bv_shows_depth`, `test_bv_golden_*` |
| 6 | Section order preserved | PASS | `test_bv_depth_layout`, `test_bv_golden_*` |
| 7 | Citation provenance preserved | PASS | `test_bv_citation_shows_generation`, `test_bv_golden_*` |
| 8 | Model generations preserved | PASS | `test_bv_citation_shows_generation`, `test_bv_golden_*` |
| 9 | Epistemic labels preserved | PASS | `test_bv_shows_epistemic_label`, `test_adversarial_historical_labels_preserved` |
| 10 | Setup eligibility preserved | PASS | `test_bv_shows_setup_verdict`, `test_bv_golden_*` |
| 11 | Context limitations preserved | PASS | `test_bv_preserves_limitations`, `test_bv_golden_*` |
| 12 | Refusal reason preserved | PASS | `test_bv_six_code_refusal_preservation`, `test_bv_golden_*` |
| 13 | No internal evidence identifiers leak | PASS | `test_bv_dto_surfaces_are_read_only`, `_assert_no_unauthorized_info` |
| 14 | No raw gateway drafts accepted | PASS | `test_bv_no_raw_draft_in_ui`, `test_adversarial_raw_gateway_draft_rejected` |
| 15 | Serialization deterministic | PASS | `test_bv_deterministic_replay`, `test_adversarial_deterministic_serialization` |
| 16 | Malformed inputs fail safely | PASS | `test_bv_malformed_input_rejection`, `test_adversarial_non_dto_types_rejected` |

### 2.3 What the adapter does NOT do (security boundaries)

- Does not consume `GatewayDraft` or any IV.4/IV.3 internal surface.
- Does not bypass `validate_answer` (IV.5).
- Does not invent or recalculate statistics.
- Does not promote historical evidence to current.
- Does not clear a no-go (`NO_GO_ACTIVE` preserved).
- Does not widen entitlement (`ACCESS_NOT_ENTITLED` enforced).
- Does not convert refusals into answers.
- Does not introduce `ASK_ANSWER_CONTRACT_V2` or `refusal_limitations`.
- Does not project provider/model/latency/cost/prompt internals into `record`.
- Does not add fields not present in the source DTO (pure pass-through).

## 3. Golden scenario coverage (Phase 2)

19 golden scenarios (`BV-GOLDEN-01` through `BV-GOLDEN-19`) under
`implementation/forge/book_v/golden/scenarios.py`.

### Coverage classification

| Category | Scenarios | Count |
|---|---|---|
| Directly executed by tests | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 13, 14, 15, 19 | 14 |
| Declared but not directly executed | 11, 16, 17, 18 | 4 |
| Duplicate scenarios (same Q5 case) | 08≡13 (Q5-25), 04≡14 (Q5-43), 03≡15 (Q5-05) | 3 pairs |

### Scenarios not directly executed (gap closed by Phase 3)

| ID | Q5 case | Why not directly executed | Closed by |
|---|---|---|---|
| BV-GOLDEN-11 | Q5-34 | No named test used Q5-34 | `test_bv_golden_11` |
| BV-GOLDEN-16 | Q5-19 | No named test used Q5-19 | `test_bv_golden_16` |
| BV-GOLDEN-17 | synthetic | No named test constructed the synthetic DTO | `test_bv_golden_17` |
| BV-GOLDEN-18 | Q5-39 | No named test used Q5-39 | `test_bv_golden_18` |

### Digest verification

All 19 scenario input digests (SHA-256 of canonical DTO payload) were
recomputed and verified against the pinned values in `scenarios.py`. All
match. No stale or invalid digests.

### Expected outcome verification

All 19 expected outcomes match the actual `PresentationAdapter` output.
No incorrect expected outcomes found.

## 4. Adversarial test results (Phase 4)

14 adversarial tests (`test_adversarial_*`) under
`tests/test_forge_book_v_adversarial.py`. All pass.

| Test | Covered case | Result |
|---|---|---|
| `test_adversarial_raw_gateway_draft_rejected` | Raw GatewayDraft input | PASS |
| `test_adversarial_non_dto_types_rejected` | Non-DTO types (None, str, int, list, dict) | PASS |
| `test_adversarial_historical_labels_preserved` | Historical labels not upgraded | PASS |
| `test_adversarial_empty_limitations_preserved` | Empty limitations not synthesized | PASS |
| `test_adversarial_no_fields_added` | No fields added by adapter | PASS |
| `test_adversarial_outcome_never_flips` | Answer/refusal outcome integrity | PASS |
| `test_adversarial_deterministic_serialization` | Repeated serialization identical | PASS |
| `test_adversarial_no_internal_material_in_record` | No provider/model/latency/cost/prompt in record | PASS |
| `test_adversarial_no_go_cannot_be_cleared` | NO_GO_ACTIVE preserved | PASS |
| `test_adversarial_entitlement_not_widened` | No privileged citation leak | PASS |
| `test_adversarial_unsupported_number_not_rendered` | No numbers in refusals | PASS |
| `test_adversarial_no_v2_contract` | No V2 contract / refusal_limitations | PASS |
| `test_adversarial_frozen_dto_prevents_mutation` | Frozen dataclass prevents tampering | PASS |
| `test_adversarial_record_is_fresh_copy` | Fresh record dict per projection | PASS |

### Cases prevented upstream (no presentation-boundary check needed)

| Case | Prevention mechanism |
|---|---|
| Unexpected extra fields | Frozen dataclasses (no `__dict__`) |
| Malformed citation structure | `CitationRef` requires all fields |
| Missing answer identity | `answer_id` required on DTOs |
| Contradictory status labels | IV.5 validates epistemic labels match source |

## 5. F-07a refusal semantics (Phase 5)

All six ratified refusal codes preserved verbatim through the adapter:

| Code | Q5 case | Depth | Result |
|---|---|---|---|
| `ACCESS_NOT_ENTITLED` | Q5-43 | OPERATOR | Preserved |
| `AMBIGUOUS_SCOPE` | Q5-44 | BEGINNER | Preserved |
| `MODEL_VERSION_UNAVAILABLE` | Q5-42 | RESEARCHER | Preserved |
| `CURRENT_DATA_UNAVAILABLE` | Q5-41 | OPERATOR | Preserved |
| `SETUP_NOT_ENCODED` | Q5-25 | OPERATOR | Preserved |
| `INSUFFICIENT_EVIDENCE` | Q5-07 | OPERATOR | Preserved |

F-07a Option C rules verified:
- Empty `limitations` tuple preserved as empty (not synthesized) ✓
- Refusal reason (`code`) remains visible ✓
- Empty limitations never interpreted as successful outcome ✓
- No synthetic limitations introduced ✓
- No refusal reason discarded ✓
- No internal validation findings exposed as unrestricted raw data ✓
- `detail` and `limitations` read together, never contradict ✓

No `ASK_ANSWER_CONTRACT_V2` introduced. IV.5 records unmodified.

## 6. Findings and limitations

### Findings

1. Four golden scenarios (11, 16, 17, 18) were declared in the BA-38
   fixture but not directly executed by any BA-38 test. Phase 3 closed
   this gap with `test_bv_golden_11` through `test_bv_golden_18`.
2. Three golden scenario pairs are duplicates (same Q5 case, same expected
   outcome): 08/13, 04/14, 03/15. This is intentional — they map to
   different requirements (e.g., GOLDEN-08 covers BV-F1-07, GOLDEN-13
   covers BV-F1-09).
3. All adversarial cases are either prevented upstream (frozen dataclasses,
   IV.5 validation) or handled by presentation-boundary checks. No new
   presentation-layer defects found.

### Limitations

- The adapter is a pure pass-through projection. It does not validate the
  semantic correctness of IV.5 content (that is IV.5's responsibility).
- Citation rendering is bounded to ratified safe fields; EV-GATE-02
  (citation-surface presentation spec) remains OPEN.
- No UI components are implemented in this rung.

## 7. Regression results

| Suite | Result |
|---|---|
| Full repository regression | 2,721 passed / 0 failed / 29 skipped |
| BA-38 presentation drivers (24) | PASS |
| BA-39 golden drivers (19) | PASS |
| BA-39 adversarial drivers (14) | PASS |
| IV.5 suite | PASS |
| IV.6 suite | PASS |
| Security Amendment 1 tests | PASS |
| Historical Lineage Amendment 1 tests | PASS |
| 17 hash guards | PASS |
