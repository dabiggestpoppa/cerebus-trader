# BA-40 — Book V Deterministic UI Component Foundation — Evidence Record

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `717026a6b37e312185c0b5bf337981c6feb0af51`
**Mode:** Deterministic UI component implementation only. No production
endpoints. No provider integration. No entitlement implementation. No
migrations. No unauthorized routes. No live market data. No Book IV
production behavior changes.

## 1. Requirement admission (Phase 1)

The 25 BA-37 requirements remain the authoritative total. BA-38
implemented all 12 admitted requirements at the presentation adapter
layer (`PresentationAdapter` + `BookVInterfaceResponse` model). BA-40
adds deterministic UI *rendering components* that consume
`BookVInterfaceResponse` and produce HTML.

### Admitted (12) — implemented by BA-38 presentation layer, rendered by BA-40 UI components

| ID | Class | Requirement | BA-38 implementation | BA-40 UI component | Status |
|---|---|---|---|---|---|
| BV-F1-01 | F1 | Render `ValidatedAnswer` sections/claims/citations | `PresentationAdapter` | `render_validated_answer`, `render_answer_sections`, `render_claim`, `render_citations` | Implemented |
| BV-F1-02 | F1 | Render `GovernedAnswerRefusal` code/detail/findings | `PresentationAdapter` | `render_governed_refusal`, `render_refusal` | Implemented |
| BV-F1-03 | F1 | Display `answer_id` | `PresentationAdapter` | `render_validated_answer`, `render_governed_refusal` | Implemented |
| BV-F1-04 | F1 | Preserve model generation in citations | `PresentationAdapter` | `render_citation` | Implemented |
| BV-F1-05 | F1 | Preserve epistemic status (HISTORICAL etc.) | `PresentationAdapter` | `render_claim` | Implemented |
| BV-F1-06 | F1 | Display answer depth | `PresentationAdapter` | `render_depth_badge` | Implemented |
| BV-F1-07 | F1 | Display setup eligibility verdict | `PresentationAdapter` | `render_eligibility` | Implemented |
| BV-F1-08 | F1 | Refuse unsupported statistic (no invented number) | `PresentationAdapter` | `render_numbers` (empty for refusals) | Implemented |
| BV-F1-09 | F1 | Preserve `limitations` as inherited restrictions | `PresentationAdapter` | `render_limitations` | Implemented |
| BV-F1-10 | F1 | Never render raw provider draft | `PresentationAdapter` (rejection) | UI accepts only `BookVInterfaceResponse` | Implemented |
| BV-F2-01 | F2 | Build refusal presentation component | `PresentationAdapter` | `render_refusal`, `render_governed_refusal` | Implemented |
| BV-F2-03 | F2 | Build depth-aware answer layout | `PresentationAdapter` | `render_answer_sections`, `render_section` | Implemented |

### Deferred (13) — gated, not implemented

| ID | Class | Gate dependency | Status |
|---|---|---|---|
| BV-F2-02 | F2 | EV-GATE-02 (OPEN) | Deferred |
| BV-F2-04 | F2 | EV-GATE-07 (OPEN) | Deferred |
| BV-F3-01 | F3 | EV-GATE-02 (OPEN) | Deferred |
| BV-F3-02 | F3 | EV-GATE-03 (OPEN) | Deferred |
| BV-F3-03 | F3 | EV-GATE-11 (OPEN) | Deferred |
| BV-F3-04 | F3 | EV-GATE-13 (OPEN) | Deferred |
| BV-F4-01 | F4 | EV-GATE-01 (OPEN) | Deferred |
| BV-F4-02 | F4 | EV-GATE-04 (OPEN) | Deferred |
| BV-F4-03 | F4 | EV-GATE-07 (OPEN) | Deferred |
| BV-F4-04 | F4 | EV-GATE-08 (OPEN) | Deferred |
| BV-F4-05 | F4 | EV-GATE-10 (OPEN) | Deferred |
| BV-F4-06 | F4 | EV-GATE-06 (OPEN) | Deferred |
| BV-F4-07 | F4 | EV-GATE-12 (OPEN) | Deferred |

## 2. Implemented UI components

| Module | Purpose | Components |
|---|---|---|
| `app/forge/book_v/ui/__init__.py` | UI package exports | All component functions + contract versions |
| `app/forge/book_v/ui/versions.py` | Frozen UI contract versions | `BOOK_V_UI_CONTRACT_V1`, `BOOK_V_UI_SCHEMA_V1` |
| `app/forge/book_v/ui/components.py` | Deterministic HTML rendering components | 14 component functions |

### Component functions

| Function | Implements | Purpose |
|---|---|---|
| `render_depth_badge(depth)` | BV-F1-06 | Renders depth badge (BEGINNER/OPERATOR/RESEARCHER) with ARIA label |
| `render_citation(citation)` | BV-F1-04 | Renders single citation with safe provenance fields (no internal IDs) |
| `render_citations(citations)` | BV-F1-04 | Renders bounded, attributed citation list |
| `render_numbers(numbers)` | BV-F1-08 | Renders authorized numeric values only (none invented) |
| `render_claim(claim)` | BV-F1-01, BV-F1-05 | Renders claim with epistemic label, layer, generation |
| `render_section(section)` | BV-F1-01, BV-F2-03 | Renders section preserving ratified depth order |
| `render_answer_sections(sections)` | BV-F1-01, BV-F2-03 | Renders all sections in IV.5 SECTION_ORDER |
| `render_limitations(limitations)` | BV-F1-09 | Renders inherited context limitations; empty tuple is valid |
| `render_eligibility(verdict)` | BV-F1-07 | Renders setup eligibility verdict |
| `render_refusal(code, detail, findings, limitations)` | BV-F1-02, BV-F2-01 | Renders refusal per F-07a Option C |
| `render_validated_answer(response)` | BV-F1-01…BV-F1-10 | Renders complete validated answer HTML |
| `render_governed_refusal(response)` | BV-F1-02, BV-F2-01 | Renders complete governed refusal HTML |
| `render_interface_response(response)` | All admitted | Main dispatcher by outcome; rejects non-DTO input |

## 3. DTO mappings

Book V UI components consume `BookVInterfaceResponse` (produced by the
presentation adapter) as read-only input. No field is extended, retyped,
or supplemented.

| `BookVInterfaceResponse` field | UI rendering | Preserved? |
|---|---|---|
| `outcome` | `data-outcome` attribute; dispatch | Yes (verbatim) |
| `answer_id` | `data-answer-id` attribute | Yes (verbatim) |
| `depth` | `render_depth_badge` | Yes (verbatim) |
| `sections` | `render_answer_sections` → `<section>` elements | Yes (verbatim, depth order) |
| `claims` | `render_claim` → `<div class="claim">` | Yes (verbatim) |
| `citations` | `render_citations` → `<div class="citation">` | Yes (verbatim) |
| `numbers` | `render_numbers` → `<div class="number">` | Yes (verbatim) |
| `limitations` | `render_limitations` → `<div class="limitations">` | Yes (verbatim) |
| `as_of` | Not rendered (metadata only) | N/A |
| `code` | `render_refusal` → `data-refusal-code` | Yes (verbatim) |
| `detail` | `render_refusal` → `<div class="refusal-detail">` | Yes (verbatim) |
| `findings` | `render_refusal` → `<ul>` list | Yes (verbatim) |
| `record` | Not rendered (safe identity subset already filtered by adapter) | N/A |

## 4. UI state contract

The UI layer renders deterministic output from `BookVInterfaceResponse`.
No network request lifecycle is implemented (no authorized backend
exists). The UI state is derived solely from the `outcome` field:

| `outcome` | UI state | Rendered component |
|---|---|---|
| `VALIDATED_ANSWER` | Answer displayed | `render_validated_answer` |
| `GOVERNED_REFUSAL` | Refusal displayed (role="alert") | `render_governed_refusal` |

No `PROCESSING`, `ERROR`, or `UNAVAILABLE` states are implemented — these
would require backend interaction not authorized in this rung.

## 5. Accessibility behavior

| Requirement | Implementation |
|---|---|
| Semantic HTML | `<section>`, `<h3>`, `<ul>`, `<li>`, `<div>` with meaningful classes |
| ARIA labels | `aria-label` on depth badges, eligibility, claims, sections, citations |
| ARIA live region | `role="alert" aria-live="polite"` on refusals |
| No color-only status | Status conveyed via text labels (code, depth, verdict text) |
| Visible focus structure | Semantic heading/list structure supports keyboard navigation |
| Readable error messages | Refusal detail rendered as plain text |
| Material state changes | `aria-live="polite"` announces refusal state changes |

## 6. Acceptance drivers (33 tests)

All tests in `tests/test_forge_book_v_ui.py`. Every test contains a
meaningful behavioral assertion. No skips, no xfails, no placeholders,
no empty tests.

| Test group | Test names | Count |
|---|---|---|
| BV-F1-01 | `test_bv_ui_renders_validated_answer` | 1 |
| BV-F1-02 | `test_bv_ui_renders_governed_refusal` | 1 |
| BV-F1-03 | `test_bv_ui_displays_answer_id` | 1 |
| BV-F1-04 | `test_bv_ui_citation_shows_generation` | 1 |
| BV-F1-05 | `test_bv_ui_shows_epistemic_label` | 1 |
| BV-F1-06 | `test_bv_ui_shows_depth` | 1 |
| BV-F1-07 | `test_bv_ui_shows_setup_verdict` | 1 |
| BV-F1-08 | `test_bv_ui_refuses_unsupported_statistic` | 1 |
| BV-F1-09 | `test_bv_ui_preserves_limitations` | 1 |
| BV-F1-10 | `test_bv_ui_no_raw_draft_in_ui` | 1 |
| BV-F2-01 | `test_bv_ui_refusal_component` | 1 |
| BV-F2-03 | `test_bv_ui_depth_layout` | 1 |
| Three depths | `test_bv_ui_three_depths_render_correctly` | 1 |
| Six refusal codes | `test_bv_ui_six_refusal_codes` | 1 |
| Citation safety | `test_bv_ui_citation_safety` | 1 |
| Historical generation | `test_bv_ui_historical_generation_preserved` | 1 |
| No-go preservation | `test_bv_ui_no_go_preserved` | 1 |
| Entitlement preservation | `test_bv_ui_entitlement_preserved` | 1 |
| Empty limitations | `test_bv_ui_empty_limitations` | 1 |
| Malformed input | `test_bv_ui_malformed_input` | 1 |
| Deterministic rendering | `test_bv_ui_deterministic_rendering` | 1 |
| No internal leakage | `test_bv_ui_no_internal_data_leakage` | 1 |
| Accessible messages | `test_bv_ui_accessible_status_messages` | 1 |
| No color-only status | `test_bv_ui_no_color_only_status` | 1 |
| Component: depth badge | `test_bv_ui_component_depth_badge_validation` | 1 |
| Component: eligibility | `test_bv_ui_component_eligibility_validation` | 1 |
| Component: refusal Option C | `test_bv_ui_component_refusal_option_c` | 1 |
| Component: citation fields | `test_bv_ui_component_citation_safe_fields` | 1 |
| Component: numbers | `test_bv_ui_component_numbers` | 1 |
| Component: limitations | `test_bv_ui_component_limitations` | 1 |
| Component: dispatch | `test_bv_ui_component_dispatch` | 1 |
| Component: contract versions | `test_bv_ui_component_contract_versions` | 1 |
| Component: hash deterministic | `test_bv_ui_rendered_hash_deterministic` | 1 |
| **Total** | | **33** |

## 7. Golden scenario coverage

The 19 BA-38 golden scenarios (`BV-GOLDEN-01` through `BV-GOLDEN-19`)
are reused by the UI component tests through end-to-end rendering
(IV.5 → `PresentationAdapter` → UI components). No golden scenario
expectations were changed.

| Golden scenario | Q5 case | UI-rendered in test |
|---|---|---|
| BV-GOLDEN-01 | Q5-01 | `test_bv_ui_renders_validated_answer`, `test_bv_ui_shows_depth` |
| BV-GOLDEN-02 | Q5-03 | `test_bv_ui_shows_depth`, `test_bv_ui_depth_layout` |
| BV-GOLDEN-03 | Q5-05 | `test_bv_ui_renders_validated_answer`, `test_bv_ui_citation_shows_generation`, `test_bv_ui_depth_layout` |
| BV-GOLDEN-04 | Q5-43 | `test_bv_ui_renders_governed_refusal`, `test_bv_ui_refusal_component`, `test_bv_ui_entitlement_preserved` |
| BV-GOLDEN-05 | Q5-44 | `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-06 | Q5-42 | `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-07 | Q5-41 | `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-08 | Q5-25 | `test_bv_ui_preserves_limitations`, `test_bv_ui_no_go_preserved`, `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-09 | Q5-07 | `test_bv_ui_refuses_unsupported_statistic`, `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-10 | Q5-31 | `test_bv_ui_historical_generation_preserved`, `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-11 | Q5-34 | `test_bv_ui_refusal_component`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-12 | Q5-08 | `test_bv_ui_refuses_unsupported_statistic`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-13 | Q5-25 | `test_bv_ui_no_go_preserved`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-14 | Q5-43 | `test_bv_ui_entitlement_preserved`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-15 | Q5-05 | `test_bv_ui_citation_shows_generation` |
| BV-GOLDEN-16 | Q5-19 | `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-17 | synthetic | `test_bv_ui_empty_limitations` |
| BV-GOLDEN-18 | Q5-39 | `test_bv_ui_entitlement_preserved`, `test_bv_ui_six_refusal_codes` |
| BV-GOLDEN-19 | n/a | `test_bv_ui_no_raw_draft_in_ui` |

## 8. Security boundaries

| Boundary | Implementation |
|---|---|
| No raw GatewayDraft | UI accepts only `BookVInterfaceResponse`; `render_interface_response` rejects non-DTO input with `ValueError` |
| No internal evidence identifiers | All user-provided text HTML-escaped; `source_ref_id` is authorized package reference only; no PKG./MFD./row_id/object_id rendered |
| No provider internals | `record` field filtered by adapter (safe identity subset only); UI never renders provider/model/latency/cost/prompt |
| No statistics invention | Numbers rendered only when present in presentation model (IV.5-validated); no number recalculated |
| No historical-to-current promotion | Epistemic labels copied verbatim; never upgraded |
| No no-go clearing | `NO_GO_ACTIVE` limitations rendered verbatim |
| No entitlement widening | `ACCESS_NOT_ENTITLED` refusal rendered with no citations |
| No refusal-to-answer conversion | Refusals render as `role="alert"`; never render sections/claims/numbers |
| Empty limitations valid | Rendered as "(no inherited limitations)"; never suppresses refusal |
| Deterministic output | Same input → identical HTML; verified by SHA-256 hash comparison |

## 9. Regression results

| Suite | Result |
|---|---|
| Full repository regression | **2,787 passed / 0 failed / 29 skipped** |
| BA-38 presentation drivers (24) | PASS (included in full regression) |
| BA-39 golden drivers (19) | PASS (included in full regression) |
| BA-39 adversarial drivers (14) | PASS (included in full regression) |
| BA-40 UI component drivers (33) | PASS |
| IV.5 suite | PASS (included in full regression) |
| IV.6 suite | PASS (included in full regression) |
| Security Amendment 1 tests | PASS (included in full regression) |
| Historical Lineage Amendment 1 tests | PASS (included in full regression) |
| 17 hash guards | PASS (test_a74, included in full regression) |

## 10. Frozen integrity verification

| Item | Status |
|---|---|
| Book IV production source | Unchanged |
| Book II provider boundary | Unchanged |
| Routes | Unchanged |
| Migrations | 001–004 unchanged |
| Credentials | Unchanged |
| Frozen fixtures (EV-001–EV-178, Q1–Q5) | Unmutated |
| New API endpoints | None added |
| Live provider invocation | None |
| `ASK_ANSWER_CONTRACT_V2` | Not introduced |
| `refusal_limitations` field | Not introduced |

## 11. Known limitations

- No production endpoints or routes are implemented.
- No live provider integration (EV-GATE-01 OPEN).
- No Book VI commercial entitlement (EV-GATE-04 OPEN).
- No live market data (EV-GATE-07 OPEN).
- No citation renderer beyond safe-field display (EV-GATE-02 OPEN).
- No current-state availability indicator (EV-GATE-07 OPEN).
- No `PROCESSING`/`ERROR`/`UNAVAILABLE` UI states (require backend not authorized in this rung).
- UI components are deterministic HTML rendering functions; no client-side JavaScript framework is introduced.

## 12. Open EV-GATE dependencies

All 13 EV-GATEs (EV-GATE-01 through EV-GATE-13) remain OPEN. No gate is
closed by fixture-only success.

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED

## 13. Ratification

This rung ratifies only the deterministic Book V UI component foundation:
pure HTML rendering functions consuming `BookVInterfaceResponse`, covering
the 12 admitted requirements (BV-F1-01…BV-F1-10, BV-F2-01, BV-F2-03).
Production deployment is not ratified. No Book VI/VII/VIII work is begun.
