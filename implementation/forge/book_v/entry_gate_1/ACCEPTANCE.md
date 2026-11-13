# ACCEPTANCE.md

**BA-37 Rung 1 — Book V acceptance criteria (planning only).**
**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting / final SHA:** `e20b6010d2648a589cbab8cde715fee431ef026f`
**Mode:** Audit and planning only. No Book V implementation. No production code modified.

This document derives acceptance requirements from the Book IV closure audit
(`BOOK_IV_CLOSURE_AUDIT.md`) and the Book V readiness gate
(`BOOK_V_READINESS_GATE.md`). Requirement totals are **not invented in
advance**; they are derived mechanically from the audit (§3 below).

Requirement IDs are of the form `BV-F{class}-NN` where class is F1 (supported by
ratified existing contracts), F2 (deterministic implementation required),
F3 (governance decision required), or F4 (external evidence or operational
integration required).

## 1. Requirement totals (derived, not invented)

| Class | Count | IDs |
|---|---:|---|
| F1 | 10 | BV-F1-01 … BV-F1-10 |
| F2 | 4 | BV-F2-01 … BV-F2-04 |
| F3 | 4 | BV-F3-01 … BV-F3-04 |
| F4 | 7 | BV-F4-01 … BV-F4-07 |
| **Total** | **25** | **BV-F1-01 … BV-F4-07** |

Verification: F1+F2+F3+F4 = 10+4+4+7 = 25 = requirement total. No duplicates;
every requirement ID is unique and contiguous within its class.

## 2. Requirements and one-to-one proposed test names

Each requirement maps to exactly one proposed exact test name. Test names are
unique. A test name is a proposal; it becomes an obligation only when Book V
implements the corresponding requirement.

### F1 — Supported by ratified existing contracts (10)

| ID | Requirement | Proposed exact test | Gate dependency |
|---|---|---|---|
| BV-F1-01 | Render `ValidatedAnswer` sections/claims/citations | `test_bv_renders_validated_answer` | None |
| BV-F1-02 | Render `GovernedAnswerRefusal` code/detail/findings | `test_bv_renders_governed_refusal` | None |
| BV-F1-03 | Display `answer_id` | `test_bv_displays_answer_id` | None |
| BV-F1-04 | Preserve model generation in citations | `test_bv_citation_shows_generation` | None |
| BV-F1-05 | Preserve epistemic status (HISTORICAL etc.) | `test_bv_shows_epistemic_label` | None |
| BV-F1-06 | Display answer depth | `test_bv_shows_depth` | None |
| BV-F1-07 | Display setup eligibility verdict | `test_bv_shows_setup_verdict` | None |
| BV-F1-08 | Refuse unsupported statistic (no invented number) | `test_bv_refuses_unsupported_statistic` | None |
| BV-F1-09 | Preserve `limitations` as inherited restrictions | `test_bv_preserves_limitations` | None |
| BV-F1-10 | Never render raw provider draft | `test_bv_no_raw_draft_in_ui` | None |

### F2 — Deterministic implementation required (4)

| ID | Requirement | Proposed exact test | Gate dependency |
|---|---|---|---|
| BV-F2-01 | Build refusal presentation component | `test_bv_refusal_component` | None |
| BV-F2-02 | Build citation renderer (bounded, attributed) | `test_bv_citation_renderer` | EV-GATE-02 (OPEN) |
| BV-F2-03 | Build depth-aware answer layout | `test_bv_depth_layout` | None |
| BV-F2-04 | Build current-state availability indicator | `test_bv_current_state_indicator` | EV-GATE-07 (OPEN) |

### F3 — Governance decision required (4)

| ID | Requirement | Proposed exact test | Gate dependency |
|---|---|---|---|
| BV-F3-01 | Define citation-surface presentation spec | `test_bv_citation_spec_ratified` | EV-GATE-02 (OPEN) |
| BV-F3-02 | Define materiality / false-refusal threshold | `test_bv_materiality_threshold` | EV-GATE-03 (OPEN) |
| BV-F3-03 | Ratify refusal-precedence for Book V surface | `test_bv_refusal_precedence_ratified` | EV-GATE-11 (OPEN) |
| BV-F3-04 | Define launch threshold table (SCORING_V1 metrics) | `test_bv_launch_threshold` | EV-GATE-13 (OPEN) |

### F4 — External evidence or operational integration required (7)

| ID | Requirement | Proposed exact test | Gate dependency |
|---|---|---|---|
| BV-F4-01 | Integrate live LLM provider | `test_bv_live_provider` | EV-GATE-01 (OPEN) |
| BV-F4-02 | Integrate Book VI commercial entitlement | `test_bv_book_vi_entitlement` | EV-GATE-04 (OPEN) |
| BV-F4-03 | Integrate real current-market data feed | `test_bv_live_market_feed` | EV-GATE-07 (OPEN) |
| BV-F4-04 | Integrate durable historical snapshot store | `test_bv_durable_snapshots` | EV-GATE-08 (OPEN) |
| BV-F4-05 | Integrate real semantic retrieval index | `test_bv_semantic_index` | EV-GATE-10 (OPEN) |
| BV-F4-06 | Integrate shared abuse store + rate/aggregation | `test_bv_abuse_store` | EV-GATE-06 (OPEN) |
| BV-F4-07 | Execute human/operator review (EV-117–EV-120) | `test_bv_human_review` | EV-GATE-12 (OPEN) |

## 3. Cross-cutting drivers

The following drivers apply to **all** requirements and must pass for any
requirement to be considered accepted:

| Driver | Purpose |
|---|---|
| `test_bv_no_gate_crossed_without_evidence` | No requirement marked F3/F4 is exercised against an OPEN gate without evidence |
| `test_bv_dto_surfaces_are_read_only` | Book V does not extend or retype IV.5/IV.6 DTOs |
| `test_bv_f07a_option_c_semantics` | `code`/`detail`/`limitations` read together per Option C; empty `limitations` legal |
| `test_bv_deterministic_replay` | Same input → same output across executions |
| `test_bv_no_historical_to_current_promotion` | No historical model becomes a current executable setup |
| `test_bv_no_refusal_to_answer_conversion` | `ERROR` reserved for unexpected exceptions only; refusals stay refusals |

These drivers reference no production code and are asserted against the
contracted DTO surfaces only.

## 4. Golden scenario inventory

The following scenarios from the ratified Book IV corpus are the golden
reference scenarios Book V must reproduce correctly when consuming the DTO
surfaces. They are read-only fixtures; Book V must not edit them.

| Scenario | Source | Expected DTO outcome |
|---|---|---|
| H1 `Show me the P90 historical state.` | EV-155 (fixtures_v3) | `ValidatedAnswer`; `MOD.P90.V1`; generation `P90.ORIGINAL`; `HISTORICAL` label; `HISTORICAL_GENERATION` limitation |
| H2 `Show me the Base80 state.` | EV-156 | `ValidatedAnswer`; `MOD.BASE80.V1`; generation `BASE80` |
| H3 `Show me the Markov legacy state.` | EV-157 | `ValidatedAnswer`; `MOD.MARKOV.LEGACY.V1`; generation `MARKOV.LEGACY` |
| P90 unsupported statistic | EV-170 | `GovernedAnswerRefusal`; code `INSUFFICIENT_EVIDENCE`; no number rendered |
| Historical evidence | EV-167 | `GovernedAnswerRefusal`; code `INSUFFICIENT_EVIDENCE` |
| Current-state w/o market data | EV-173 | `GovernedAnswerRefusal`; code `CURRENT_DATA_UNAVAILABLE` |
| Actionable historical setup | EV-176 | `GovernedAnswerRefusal`; code `SETUP_NOT_ENCODED` |
| Superseded model | `MOD.LEGACY.SUPERSEDED.V1` (bloc_iv_2) | Stays `SUPERSEDED`; never current |

## 5. Traceability matrix

| Requirement | Class | Gate dependency | Implements finding? | Test name |
|---|---|---|---|---|
| BV-F1-01 | F1 | None | — | `test_bv_renders_validated_answer` |
| BV-F1-02 | F1 | None | — | `test_bv_renders_governed_refusal` |
| BV-F1-03 | F1 | None | — | `test_bv_displays_answer_id` |
| BV-F1-04 | F1 | None | — | `test_bv_citation_shows_generation` |
| BV-F1-05 | F1 | None | — | `test_bv_shows_epistemic_label` |
| BV-F1-06 | F1 | None | — | `test_bv_shows_depth` |
| BV-F1-07 | F1 | None | — | `test_bv_shows_setup_verdict` |
| BV-F1-08 | F1 | None | — | `test_bv_refuses_unsupported_statistic` |
| BV-F1-09 | F1 | None | — | `test_bv_preserves_limitations` |
| BV-F1-10 | F1 | None | — | `test_bv_no_raw_draft_in_ui` |
| BV-F2-01 | F2 | None | — | `test_bv_refusal_component` |
| BV-F2-02 | F2 | EV-GATE-02 | — | `test_bv_citation_renderer` |
| BV-F2-03 | F2 | None | — | `test_bv_depth_layout` |
| BV-F2-04 | F2 | EV-GATE-07 | — | `test_bv_current_state_indicator` |
| BV-F3-01 | F3 | EV-GATE-02 | — | `test_bv_citation_spec_ratified` |
| BV-F3-02 | F3 | EV-GATE-03 | — | `test_bv_materiality_threshold` |
| BV-F3-03 | F3 | EV-GATE-11 | — | `test_bv_refusal_precedence_ratified` |
| BV-F3-04 | F3 | EV-GATE-13 | — | `test_bv_launch_threshold` |
| BV-F4-01 | F4 | EV-GATE-01 | — | `test_bv_live_provider` |
| BV-F4-02 | F4 | EV-GATE-04 | — | `test_bv_book_vi_entitlement` |
| BV-F4-03 | F4 | EV-GATE-07 | — | `test_bv_live_market_feed` |
| BV-F4-04 | F4 | EV-GATE-08 | — | `test_bv_durable_snapshots` |
| BV-F4-05 | F4 | EV-GATE-10 | — | `test_bv_semantic_index` |
| BV-F4-06 | F4 | EV-GATE-06 | — | `test_bv_abuse_store` |
| BV-F4-07 | F4 | EV-GATE-12 | — | `test_bv_human_review` |

**Traceability checks (all verified):**
- Requirement IDs contiguous within each class: ✓ (F1-01…10, F2-01…04, F3-01…04, F4-01…07)
- No duplicate requirements: ✓
- Every requirement maps to exactly one proposed test: ✓ (25 requirements → 25 test names)
- Test names unique: ✓
- F1+F2+F3+F4 = requirement total: ✓ (10+4+4+7 = 25)
- All four documents agree on counts: ✓ (BOOK_IV_CLOSURE_AUDIT §7, BOOK_V_READINESS_GATE §4, CONTRACT_HANDOFF, this document)
- Every open gate has an owner: ✓ (FEASIBILITY_GATE.md owners; BOOK_V_READINESS_GATE §2)
- No prohibited production path changed: ✓ (no production code modified in this rung)

## 6. Explicit non-acceptance conditions

Book V acceptance is **not** granted if any of the following is true:

1. Any F3/F4 requirement is exercised against its OPEN gate without evidence
   (gate dependency not closed).
2. Book V introduces `ASK_ANSWER_CONTRACT_V2` or a consolidated
   `refusal_limitations` field (Option B deferred).
3. Book V bypasses `validate_answer` or renders a raw `GatewayDraft`.
4. Book V invents or recalculates a model statistic; an unsupported statistic
   renders a number instead of refusing `INSUFFICIENT_EVIDENCE`.
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
11. Any cross-cutting driver (§3) fails.
12. The Book IV regression baseline regresses (must remain 0 failed).

## 7. Acceptance decision

Acceptance of a Book V requirement is **granted** only when:

- Its class gate dependency (if any) is closed with evidence, **and**
- Its proposed exact test passes against the ratified DTO surfaces, **and**
- All cross-cutting drivers (§3) pass, **and**
- No non-acceptance condition (§6) is violated.

Acceptance of Book V **production release** additionally requires BG-C to
become PASS and all EV-GATE-01–13 to close with evidence. Until then, Book V
is admitted to deterministic, offline development only (F1 + non-gated F2
items).
