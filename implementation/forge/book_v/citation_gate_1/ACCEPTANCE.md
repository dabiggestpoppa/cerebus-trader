# ACCEPTANCE.md

**BA-41 Rung 1 — Book V Citation Surface Governance — Acceptance Inventory**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `119b46cfce49bd57fab699e53cb63a171dd14efb`
**Mode:** Planning and contract ratification proposal only. No
implementation of gated citation functionality.

This document derives the citation presentation requirement inventory from
the ratified Book V chapters (BOOK_V_READINESS_GATE.md,
CONTRACT_HANDOFF.md, ACCEPTANCE.md at `entry_gate_1/`) and the BA-41
CITATION_CONTRACT_AUDIT.md. It separates already-implemented, deterministic,
governance, and external-dependency requirements, and verifies totals
mechanically.

## 1. Requirement inventory

### Already implemented (BA-38/BA-39/BA-40) — not part of EV-GATE-02

These citation-related capabilities already exist and are not gated:

| ID | Class | Requirement | Status | Basis |
|---|---|---|---|---|
| BV-F1-01 | F1 | Render `ValidatedAnswer` sections/claims/citations | Implemented (BA-38/40) | `test_bv_ui_renders_validated_answer` |
| BV-F1-04 | F1 | Preserve model generation in citations | Implemented (BA-38/40) | `test_bv_ui_citation_shows_generation` |
| BV-F1-09 | F1 | Preserve `limitations` as inherited restrictions | Implemented (BA-38/40) | `test_bv_ui_preserves_limitations` |
| BV-F1-10 | F1 | Never render raw provider draft | Implemented (BA-38/40) | `test_bv_ui_no_raw_draft_in_ui` |
| BV-F2-01 | F2 | Build refusal presentation component | Implemented (BA-38/40) | `test_bv_ui_refusal_component` |

### Deterministic implementation (gated by EV-GATE-02)

Requirements that can be implemented deterministically once EV-GATE-02
closes (ratified citation-surface spec + IV.6 metrics re-baselined):

| ID | Class | Requirement | Gate dependency | Proposed exact test | Golden scenario |
|---|---|---|---|---|---|
| BV-F2-02 | F2 | Build citation renderer (bounded, attributed) | EV-GATE-02 (OPEN) | `test_bv_citation_renderer` | BV-CITE-01…BV-CITE-06 |
| BV-F2-04 | F2 | Build current-state availability indicator | EV-GATE-07 (OPEN) | `test_bv_current_state_indicator` | — |

### Governance decision (F3)

| ID | Class | Requirement | Gate dependency | Proposed exact test | Golden scenario |
|---|---|---|---|---|---|
| BV-F3-01 | F3 | Define citation-surface presentation spec | EV-GATE-02 (OPEN) | `test_bv_citation_spec_ratified` | — |

### External dependency (F4)

| ID | Class | Requirement | Gate dependency | Proposed exact test | Golden scenario |
|---|---|---|---|---|---|
| BV-F4-01 | F4 | Integrate live LLM provider | EV-GATE-01 (OPEN) | `test_bv_live_provider` | — |
| BV-F4-02 | F4 | Integrate Book VI commercial entitlement | EV-GATE-04 (OPEN) | `test_bv_book_vi_entitlement` | — |
| BV-F4-03 | F4 | Integrate real current-market data feed | EV-GATE-07 (OPEN) | `test_bv_live_market_feed` | — |
| BV-F4-04 | F4 | Integrate durable historical snapshot store | EV-GATE-08 (OPEN) | `test_bv_durable_snapshots` | — |
| BV-F4-05 | F4 | Integrate real semantic retrieval index | EV-GATE-10 (OPEN) | `test_bv_semantic_index` | — |
| BV-F4-06 | F4 | Integrate shared abuse store + rate/aggregation | EV-GATE-06 (OPEN) | `test_bv_abuse_store` | — |
| BV-F4-07 | F4 | Execute human/operator review (EV-117–EV-120) | EV-GATE-12 (OPEN) | `test_bv_human_review` | — |

### F-totals (re-stated from BA-37/BA-39)

| Class | Total | Already implemented | Deterministic (gated) | Governance | External |
|---|---:|---:|---:|---:|---:|
| F1 | 10 | 10 | 0 | 0 | 0 |
| F2 | 4 | 2 (F2-01, F2-03) | 2 (F2-02, F2-04) | 0 | 0 |
| F3 | 4 | 0 | 0 | 4 | 0 |
| F4 | 7 | 0 | 0 | 0 | 7 |
| **Total** | **25** | **12** | **2** | **4** | **7** |

Mechanical verification:
- Contiguous IDs within each class: ✓ (F1-01…10, F2-01…04, F3-01…04, F4-01…07)
- Unique test names: ✓ (25 unique names)
- Complete requirement mapping: ✓ (every requirement maps to exactly one test)
- Matching totals across documents: ✓ (BA-37 ACCEPTANCE.md, BA-39 interface_gate_2/ACCEPTANCE.md, this document all agree)

## 2. Cross-cutting drivers (apply to all requirements)

| Driver | Purpose |
|---|---|
| `test_bv_no_gate_crossed_without_evidence` | No F3/F4 requirement exercised against OPEN gate without evidence |
| `test_bv_dto_surfaces_are_read_only` | Book V does not extend or retype IV.5/IV.6 DTOs |
| `test_bv_f07a_option_c_semantics` | `code`/`detail`/`limitations` read together per Option C |
| `test_bv_deterministic_replay` | Same input → same output across executions |
| `test_bv_no_historical_to_current_promotion` | No historical model promoted to current |
| `test_bv_no_refusal_to_answer_conversion` | Refusals stay refusals |

## 3. Citation-specific golden scenarios

Derived from existing ratified fixtures. No IV.5/IV.6 fixture modified.

| ID | Q5 case | Scenario | Expected outcome | Requirement mapping | Test |
|---|---|---|---|---|---|
| BV-CITE-01 | Q5-05 | Valid single citation (RESEARCHER answer) | `ValidatedAnswer`; citation `CL.XAU.GAME.001` with generation `XAU.GAME` | BV-F1-01, BV-F1-04 | `test_bv_cite_valid_single` |
| BV-CITE-02 | Q5-05 | Valid multiple citations | Two citations rendered; both resolve inside package | BV-F1-01, BV-F1-04 | `test_bv_cite_valid_multiple` |
| BV-CITE-03 | Q5-05 | Historical source (generation preserved) | Citation generation `XAU.GAME` preserved; not upgraded | BV-F1-04, BV-F1-05 | `test_bv_cite_historical_source` |
| BV-CITE-04 | Q5-08 | Unsupported statistic → refusal | `GOVERNED_REFUSAL`; `INSUFFICIENT_EVIDENCE`; no number rendered | BV-F1-02, BV-F1-08 | `test_bv_cite_unsupported_statistic` |
| BV-CITE-05 | Q5-19 | Unresolvable citation rejection | `GOVERNED_REFUSAL`; `CITATION_UNRESOLVED` | BV-F1-02 | `test_bv_cite_unresolvable` |
| BV-CITE-06 | Q5-39 | Unauthorized source containment | `GOVERNED_REFUSAL`; `ACCESS_NOT_ENTITLED`; no citations rendered | BV-F1-02 | `test_bv_cite_unauthorized` |

### Negative controls (must NOT refuse legitimate attributed evidence)

| ID | Case | Purpose |
|---|---|---|
| BV-CITE-NC-01 | Q5-01 | Valid BEGINNER answer with citations renders (no false refusal) |
| BV-CITE-NC-02 | Q5-03 | Valid OPERATOR answer with citations renders |
| BV-CITE-NC-03 | Q5-05 | Valid RESEARCHER answer with citations renders |

## 4. Proposed exact tests (governance-gated)

These tests exist only as proposals; they become obligations only when
EV-GATE-02 closes and BV-F2-02/BV-F3-01 are admitted:

| Test name | Requirement | Purpose |
|---|---|---|
| `test_bv_citation_renderer` | BV-F2-02 | Citation renderer renders `code`/`detail`/provenance per ratified spec |
| `test_bv_citation_spec_ratified` | BV-F3-01 | Citation-surface presentation spec exists and is ratified |
| `test_bv_cite_valid_single` | BV-F1-01/BV-F1-04 | Single citation renders with generation |
| `test_bv_cite_valid_multiple` | BV-F1-01/BV-F1-04 | Multiple citations render, all inside package |
| `test_bv_cite_historical_source` | BV-F1-04/BV-F1-05 | Historical generation preserved, not upgraded |
| `test_bv_cite_unsupported_statistic` | BV-F1-02/BV-F1-08 | Unsupported statistic refuses; no number |
| `test_bv_cite_unresolvable` | BV-F1-02 | Unresolvable citation refuses whole answer |
| `test_bv_cite_unauthorized` | BV-F1-02 | Unauthorized source refuses; no citations |

## 5. Non-acceptance conditions

Citation-surface acceptance is **not** granted if any of the following:

1. BV-F2-02 or BV-F3-01 is implemented before EV-GATE-02 closes with
   evidence (ratified spec + IV.6 metrics re-baselined).
2. The citation surface exposes any INTERNAL-ONLY field
   (`object_id`, `claim_id`, `evidence_id`, `result_value`, `text`,
   `score`, `exposure`, `trust_class`, `item_id`, `text_sha256`).
3. The citation surface invents provenance, substitutes evidence,
   changes generation, promotes historical to current, or bypasses
   IV.5 validation.
4. `is_internal_ref()` or `CITATION_OUTSIDE_PACKAGE` enforcement is
   weakened.
5. Any non-acceptance condition from BA-39 ACCEPTANCE.md §4 is violated.
6. Book IV regression baseline regresses (must remain 0 failed).

## 6. Production release precondition

Citation-surface production release additionally requires BG-C to become
PASS and all EV-GATE-01–13 to close with evidence. Until then, citation
presentation is admitted to deterministic, offline development only
(after EV-GATE-02 closes for BV-F2-02/BV-F3-01).

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED
