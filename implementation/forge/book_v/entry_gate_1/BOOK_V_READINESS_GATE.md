# BOOK_V_READINESS_GATE.md

**BA-37 Rung 1 — Book IV → Book V admission gate (planning only).**
**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting / final SHA:** `e20b6010d2648a589cbab8cde715fee431ef026f`
**Mode:** Audit and planning only. No Book V implementation. No production code modified.

This document states the conditions under which Book V may be admitted to build
on top of Book IV. It derives every condition from the Book IV closure audit
(`BOOK_IV_CLOSURE_AUDIT.md`) and the ratified contracts. It makes no
governance decisions beyond classifying requirements F1–F4; the GO / CONDITIONAL
GO / NO-GO decision is stated explicitly with its rationale.

## 1. Book V admission conditions

Book V admission is **CONDITIONAL GO**, not unconditional GO. Book IV's
deterministic implementation is complete and green (2,697 passed / 0 failed /
29 skipped), but production readiness (BG-C) is BLOCKED and all 13 EV-GATEs are
OPEN. Book V may proceed with deterministic implementation against the ratified
IV.5/IV.6 DTO surfaces, but any Book V behavior that depends on an OPEN gate
or on BG-C is itself blocked until that gate closes with evidence.

Admission conditions (all must hold):

1. **Book V consumes only ratified IV.5/IV.6 DTO surfaces.** It may read
   `ValidatedAnswer`, `GovernedAnswerRefusal`, `answer_id`, citations,
   evidence status, model generation, answer depth, setup eligibility,
   current-state availability, refusal limitations (`limitations` field), safe
   provenance, and error states. It must not consume raw `GatewayDraft`
   provider output, raw package internals, or any IV.4/IV.3 surface not exposed
   through the IV.5 DTO.
2. **Book V must not bypass IV.5 validation.** Every answer or refusal presented
   to the operator must flow through `validate_answer(draft, package)` (or an
   equivalent IV.5-governed validation) and carry a terminal
   `AnswerOutcome` (VALIDATED_ANSWER or GOVERNED_REFUSAL). No answer may be
   synthesized from a provider draft without IV.5 adjudication.
3. **Book V must not invent or recalculate model statistics.** Numerical values
   must resolve to authorized package evidence (`numeric_ref_is_admissible`);
   unsupported statistics must refuse `INSUFFICIENT_EVIDENCE`, never render a
   number.
4. **Book V must not promote historical evidence to current.** `HISTORICAL` /
   `SUPERSEDED` / `PARKED` / `CANDIDATE` / `RESEARCH_FLAG` labels must be
   preserved; no historical model may become a current executable setup
   (F-09/F-09b control).
5. **Book V must not clear a no-go.** `NO_GO_ACTIVE` limitations must survive
   into the answer surface; injected or operator text cannot convert WATCH→
   ELIGIBLE or override BLOCKED (Security Amendment 1 AM1-R14…R17).
6. **Book V must not widen entitlement.** `ACCESS_NOT_ENTITLED` and package
   exposure boundaries must be enforced; no privileged citation or object id may
   leak (Security Amendment 1 AM1-R01…R13).
7. **Book V must not interpret missing market data as valid current data.**
   `CURRENT`/`AS_OF` requests without a configured provider must refuse
   `CURRENT_DATA_UNAVAILABLE` / `PROVIDER_NOT_CONFIGURED`, never fabricate a
   level (F-09 control; EV-GATE-07 OPEN).
8. **Book V must not convert a refusal into a successful answer.** Every
   governed refusal must survive composition as `GOVERNED_REFUSAL`; `ERROR` is
   reserved only for unexpected exceptions (F-09b control).
9. **Book V must honor F-07a Option C semantics.** `code` is the primary
   governed refusal reason; `findings` are supporting validation findings;
   `detail` is consumer-safe explanatory prose; `limitations` are inherited
   context limitations (not a restatement of `code`). An empty `limitations`
   tuple is legal and is not evidence that the refusal has no reason.
10. **Book V adds no V2 response schema without separate authorization.**
    `ASK_ANSWER_CONTRACT_V1` remains the contract; `refusal_limitations`
    (Option B) remains deferred.

## 2. Required upstream contracts (Book V permitted to consume)

| Contract | Source (Book IV bloc) | Status | Book V may use? |
|---|---|---|---|
| `ValidatedAnswer` DTO | IV.5 `answer/schema.py` | Ratified (V1) | Yes |
| `GovernedAnswerRefusal` DTO | IV.5 `answer/schema.py` | Ratified (V1) | Yes |
| `answer_id` | IV.5 `answer/record.py` | Ratified (V1) | Yes |
| Citation presentation (`CitationRef`) | IV.5 `answer/schema.py` | Ratified (V1) | Yes |
| Evidence status / epistemic label | IV.3 `context/enums.py` | Ratified (V1) | Yes |
| Model generation | IV.2 `retrieval/refs.py` (`CanonicalRef.generation`) | Ratified (V1) | Yes |
| Answer depth | IV.5 `answer/enums.py` (`AnswerDepth`) | Ratified (V1) | Yes |
| Setup eligibility | IV.5 `answer/enums.py` (`SetupVerdict`) | Ratified (V1) | Yes |
| Current-state availability | IV.2/IV.3 intelligence refusal + IV.5 freshness | Ratified (V1) | Yes, but EV-GATE-07 OPEN for live data |
| Refusal limitations (`limitations` field) | IV.5 `GovernedAnswerRefusal.limitations` | Ratified (V1, F-07a Option C) | Yes |
| Safe provenance | IV.3 `ContextItem` / IV.5 `CitationRef` | Ratified (V1) | Yes |
| Error states | IV.5 `AnswerOutcome.GOVERNED_REFUSAL` + IV.4 `GatewayRefusal` | Ratified (V1) | Yes |
| Entitlement context | IV.2 `ForgePolicyEnforcementService` / IV.3 `exposure_allowed` | Ratified (V1) | Yes, but EV-GATE-04 OPEN for commercial entitlement |

**Missing adapter / presentation contract:** Book V has **no** ratified
presentation contract for rendering `GovernedAnswerRefusal` or `ValidatedAnswer`
to an operator UI. The refusal surface (`code`/`detail`/`limitations`) is
defined (`REFUSAL_CONSUMER_CONTRACT_V1.md`, Option C) but there is no UI
component, no citation renderer, no depth-aware layout contract. This is a
missing adapter that Book V must define under its own governance (EV-GATE-02
citation surface is OPEN).

## 3. Operational blockers

| Blocker | Source | Status | Blocks Book V? | Blocks production? |
|---|---|---|---|---|
| BG-C operational readiness | Security Amendment 1 / RATIFICATION.md | BLOCKED | No (deterministic impl OK) | Yes |
| EV-GATE-01 provider/privacy | FEASIBILITY_GATE.md | OPEN | Yes (live provider) | Yes |
| EV-GATE-04 commercial entitlement | FEASIBILITY_GATE.md | OPEN | Yes (Book VI entitlement) | Yes |
| EV-GATE-07 real current-market data | FEASIBILITY_GATE.md | OPEN | Yes (current-state answers) | Yes |
| EV-GATE-12 human review | FEASIBILITY_GATE.md | OPEN | No (deterministic impl OK) | Yes |
| All other EV-GATE-02/03/05/06/08/09/10/11/13 | FEASIBILITY_GATE.md | OPEN | Mixed (see §5 table) | Yes |

Deterministic Book V implementation (offline, fixture-backed, no live provider)
is not blocked by any of the above. Production release is blocked until
BG-C and the F4 gates close with evidence.

## 4. F1/F2/F3/F4 feasibility classification

Each requirement below has a unique ID, owner, evidence source, acceptance
criterion, proposed exact test, and closure condition. Totals are verified
mechanically in §5.

| ID | Requirement (short) | Class | Owner | Evidence source | Acceptance criterion | Proposed exact test | Closure condition |
|---|---|---|---|---|---|---|---|
| BV-F1-01 | Render `ValidatedAnswer` sections/claims/citations | F1 | Book V | IV.5 `answer/schema.py` | Sections/claims/citations render from DTO | `test_bv_renders_validated_answer` | DTO unchanged; test green |
| BV-F1-02 | Render `GovernedAnswerRefusal` code/detail/findings | F1 | Book V | IV.5 `answer/schema.py` | Refusal DTO renders; `code` primary reason | `test_bv_renders_governed_refusal` | DTO unchanged; test green |
| BV-F1-03 | Display `answer_id` | F1 | Book V | IV.5 `answer/record.py` | `answer_id` rendered | `test_bv_displays_answer_id` | DTO unchanged; test green |
| BV-F1-04 | Preserve model generation in citations | F1 | Book V | IV.2 `CanonicalRef.generation` | Generation shown on cited refs | `test_bv_citation_shows_generation` | DTO unchanged; test green |
| BV-F1-05 | Preserve epistemic status (HISTORICAL etc.) | F1 | Book V | IV.3 `context/enums.py` | Label shown per claim | `test_bv_shows_epistemic_label` | DTO unchanged; test green |
| BV-F1-06 | Display answer depth | F1 | Book V | IV.5 `AnswerDepth` | Depth shown | `test_bv_shows_depth` | DTO unchanged; test green |
| BV-F1-07 | Display setup eligibility verdict | F1 | Book V | IV.5 `SetupVerdict` | Verdict shown | `test_bv_shows_setup_verdict` | DTO unchanged; test green |
| BV-F1-08 | Refuse unsupported statistic (no invented number) | F1 | Book V | IV.5 `INSUFFICIENT_EVIDENCE` | Number refuses; no value rendered | `test_bv_refuses_unsupported_statistic` | DTO unchanged; test green |
| BV-F1-09 | Preserve `limitations` as inherited restrictions | F1 | Book V | F-07a Option C | `limitations` shown alongside `code`/`detail` | `test_bv_preserves_limitations` | DTO unchanged; test green |
| BV-F1-10 | Never render raw provider draft | F1 | Book V | IV.4 `GatewayDraft` (internal) | Draft never reaches UI | `test_bv_no_raw_draft_in_ui` | IV.5 validation gate; test green |
| BV-F2-01 | Build refusal presentation component | F2 | Book V | `REFUSAL_CONSUMER_CONTRACT_V1.md` | Component renders `code`/`detail`/`limitations` | `test_bv_refusal_component` | Component reviewed; no gate crossed |
| BV-F2-02 | Build citation renderer (bounded, attributed) | F2 | Book V | EV-GATE-02 (OPEN) | Citation renders with source ref + quote scope | `test_bv_citation_renderer` | EV-GATE-02 must close for live citations |
| BV-F2-03 | Build depth-aware answer layout (Beginner/Operator/Researcher) | F2 | Book V | IV.5 depth section orders | Layout differs correctly by depth | `test_bv_depth_layout` | DTO unchanged; test green |
| BV-F2-04 | Build current-state availability indicator | F2 | Book V | IV.2/IV.3 freshness; EV-GATE-07 OPEN | Indicator shows as_of or refuses | `test_bv_current_state_indicator` | EV-GATE-07 for live data |
| BV-F3-01 | Define citation-surface presentation spec | F3 | Product/UX | EV-GATE-02 | Signed citation-surface spec | `test_bv_citation_spec_ratified` | Governance decision (EV-GATE-02) |
| BV-F3-02 | Define materiality / false-refusal threshold | F3 | Product owner | EV-GATE-03 | Written materiality policy + threshold | `test_bv_materiality_threshold` | Governance decision (EV-GATE-03) |
| BV-F3-03 | Ratify refusal-precedence for Book V surface | F3 | Product/Governance | EV-GATE-11 | Signed precedence ratification | `test_bv_refusal_precedence_ratified` | Governance decision (EV-GATE-11) |
| BV-F3-04 | Define launch threshold table (SCORING_V1 metrics) | F3 | Product owner | EV-GATE-13 | Signed threshold table | `test_bv_launch_threshold` | Governance decision (EV-GATE-13) |
| BV-F4-01 | Integrate live LLM provider | F4 | Gateway owner + operator | EV-GATE-01 | Provider wired behind `LLMProvider` port | `test_bv_live_provider` | EV-GATE-01 (provider/privacy approval + eval) |
| BV-F4-02 | Integrate Book VI commercial entitlement | F4 | Book VI | EV-GATE-04 | Entitlement behind `AuthorizationContext` | `test_bv_book_vi_entitlement` | EV-GATE-04 |
| BV-F4-03 | Integrate real current-market data feed | F4 | Data owner | EV-GATE-07 | Licensed feed + freshness contract | `test_bv_live_market_feed` | EV-GATE-07 |
| BV-F4-04 | Integrate durable historical snapshot store | F4 | Book VII | EV-GATE-08 | Snapshot store + replay evidence | `test_bv_durable_snapshots` | EV-GATE-08 |
| BV-F4-05 | Integrate real semantic retrieval index | F4 | Book VII | EV-GATE-10 | Production index; `SEMANTIC_UNAVAILABLE` gaps closed | `test_bv_semantic_index` | EV-GATE-10 |
| BV-F4-06 | Integrate shared abuse store + rate/aggregation | F4 | Book VIII | EV-GATE-06 | Abuse store; cross-session controls | `test_bv_abuse_store` | EV-GATE-06 |
| BV-F4-07 | Execute human/operator review (EV-117–EV-120) | F3/F4 | Operator reviewer | EV-GATE-12 | Completed `HumanReviewRecord` set | `test_bv_human_review` | EV-GATE-12 (governance + execution) |

**Totals (verified mechanically):**
- F1: 10 (BV-F1-01…BV-F1-10)
- F2: 4 (BV-F2-01…BV-F2-04)
- F3: 4 (BV-F3-01…BV-F3-04)
- F4: 7 (BV-F4-01…BV-F4-07)
- **F1+F2+F3+F4 = 25 = requirement total.** No duplicates; every requirement maps to exactly one proposed test; test names unique; scenario/ID uniqueness holds.

## 5. GO / CONDITIONAL GO / NO-GO decision

**Decision: CONDITIONAL GO.**

**Rationale:**
- Book IV's deterministic implementation is complete and green: all six blocs,
  Security Amendment 1, Historical Lineage Amendment 1, and BA-33/BA-34/BA-36
  supplements are internally consistent; all previously reported findings
  (F-01–F-10, F-07a, F-08 hash integrity) are closed with executable evidence;
  full regression is 2,697 passed / 0 failed / 29 skipped; BG-A PASS, BG-B PASS.
- Book V may proceed with **deterministic implementation** (F1 + F2 items that
  do not cross an OPEN gate) against the ratified IV.5/IV.6 DTO surfaces,
  honoring F-07a Option C and all F-01–F-10 controls.
- Book V must **not** proceed to production release or to any behavior
  depending on an OPEN EV-GATE or BG-C until those gates close with evidence.
  BG-A and BG-B do not imply BG-C; no gate is closed by fixture-only success.

**Conditions before production release:** BG-C must become PASS; EV-GATE-01–13
must close with evidence; Book V's F3/F4 items must be resolved by their
respective owners. Until then, Book V is admitted to deterministic, offline
development only.
