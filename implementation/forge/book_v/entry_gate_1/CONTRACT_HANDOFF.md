# CONTRACT_HANDOFF.md

**BA-37 Rung 1 — Book IV → Book V contract handoff (planning only).**
**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting / final SHA:** `e20b6010d2648a589cbab8cde715fee431ef026f`
**Mode:** Audit and planning only. No Book V implementation. No production code modified.

This document defines the exact allowable DTO surfaces, refusal presentation
semantics, citation and provenance requirements, entitlement boundaries,
versioning expectations, IV.5/IV.6 ownership boundaries, and the Book V
implementation sequence. It is the authoritative handoff contract; Book V may
implement only what is described here.

## 1. Exact allowable DTO surfaces (read-only for Book V)

Book V may consume the following Book IV DTOs **as read-only inputs**. It may
not extend, retype, or add fields to them without separate authorization
(Option B `refusal_limitations` / `ASK_ANSWER_CONTRACT_V2` remains deferred).

### 1.1 `ValidatedAnswer` (IV.5 `app/forge/ask_cerebus/answer/schema.py`)

Contract: `ASK_ANSWER_CONTRACT_V1`. Read-only fields:

| Field | Type | Notes |
|---|---|---|
| `answer_contract_version` | str | `ASK_ANSWER_CONTRACT_V1` |
| `answer_schema_version` | str | |
| `validator_set_version` | str | |
| `outcome` | `AnswerOutcome.VALIDATED_ANSWER` | |
| `answer_id` | str | Opaque; do not parse |
| `depth` | `AnswerDepth` (BEGINNER/OPERATOR/RESEARCHER) | |
| `sections` | tuple[`AnswerSection`] | section_id, heading, bullets, claim_ids |
| `claims` | tuple[`AnswerClaim`] | claim_id, text, section_id, epistemic_label, layer, generation, source_refs, citation_ids |
| `citations` | tuple[`CitationRef`] | source_ref_id, source_ref_type, source_status, provenance_refs, evidence_refs, generation |
| `numbers` | tuple[`AnswerNumber`] | value_text, unit, source_ref_id, normalized |
| `limitations` | tuple[str] | Inherited context restrictions (F-07a Option C) |
| `as_of` | str | Empty unless current-state |
| `record` | `FinalResponseRecord` | Metadata; `answer_refusal_code` empty for answers |

Book V may render `sections`, `claims`, `citations`, `numbers`, `limitations`,
`depth`, `as_of`. It must not treat `record` internals as content.

### 1.2 `GovernedAnswerRefusal` (IV.5 `app/forge/ask_cerebus/answer/schema.py`)

Contract: `ASK_ANSWER_CONTRACT_V1`. Read-only fields:

| Field | Type | F-07a Option C semantics |
|---|---|---|
| `answer_id` | str | Opaque; do not parse |
| `code` | `AnswerRefusalCode` | **Primary governed refusal reason** (one of six; precedence highest-first) |
| `detail` | str | Consumer-safe explanatory prose |
| `depth` | `AnswerDepth` | |
| `findings` | tuple[str] | Supporting validation findings (validation codes) |
| `limitations` | tuple[str] | **Inherited context restrictions**, not a restatement of `code`. May be empty. |
| `record` | `FinalResponseRecord` | `answer_refusal_code` set; metadata only |

Book V must read `code`, `detail`, and `limitations` together. `code` wins for
the refusal reason; `limitations` are shown alongside, never merged into the
reason. An empty `limitations` tuple is legal and is not evidence that the
refusal has no reason.

### 1.3 `AnswerRefusalCode` (six frozen codes, precedence highest-first)

1. `ACCESS_NOT_ENTITLED`
2. `AMBIGUOUS_SCOPE`
3. `MODEL_VERSION_UNAVAILABLE`
4. `CURRENT_DATA_UNAVAILABLE`
5. `SETUP_NOT_ENCODED`
6. `INSUFFICIENT_EVIDENCE`

### 1.4 `CitationRef`

| Field | Type | Notes |
|---|---|---|
| `source_ref_id` | str | Authorized package reference (never internal row/object id) |
| `source_ref_type` | str | MODEL / CLAIM / EVIDENCE / LINEAGE / TERM / SETUP |
| `source_status` | str | |
| `provenance_refs` | tuple[str] | |
| `evidence_refs` | tuple[str] | |
| `generation` | str | Model generation (e.g. `P90.ORIGINAL`, `BASE80`) |

## 2. Refusal presentation semantics (F-07a Option C)

Book V must implement the following consumer rules (ratified in
`REFUSAL_CONSUMER_CONTRACT_V1.md`, zero payload change):

| Rule | Requirement |
|---|---|
| R1 | `code` is the primary governed refusal reason; read first. |
| R2 | `findings` are supporting validation findings; every failing validator code stays visible. |
| R3 | `detail` is consumer-safe explanatory prose; no protected identifiers. |
| R4 | `limitations` are inherited context restrictions; shown alongside `code`/`detail`, never merged. |
| R5 | `code` wins for the refusal reason; `limitations` are not a restatement of `code`. |
| R6 | An empty `limitations` tuple is legal and is **not** evidence that the refusal has no reason. |
| R7 | `detail` and `limitations` must not contradict for the same refusal. |
| R8 | No limitation is fabricated for a case that has none. |
| R9 | No protected identifiers in `code`, `detail`, or `limitations`. |
| R10 | Serialization is deterministic: same input → same `answer_id`/`code`/`detail`/`findings`/`limitations`. |

Book V must not introduce a consolidated `refusal_limitations` field (Option B
deferred) and must not modify IV.5 response payloads or frozen answer IDs.

## 3. Citation and provenance requirements

| Requirement | Source | Enforcement |
|---|---|---|
| Citations resolve inside `admission.allowed_refs` | IV.4 `parse_draft` | `CITATION_OUTSIDE_PACKAGE` refused |
| Claim citations resolve inside package | IV.5 `validate_citations` | `CITATION_REQUIRED` / `CITATION_UNRESOLVED` |
| Numeric links resolve to admissible evidence | IV.4 `numeric_ref_is_admissible` | `NUMERIC_EVIDENCE_MISSING` refused |
| Citation `source_ref_id` never an internal row/object id | IV.5 `CitationRef` docstring | By contract |
| Provenance refs carried on citations | IV.5 `CitationRef.provenance_refs` | Read-only |
| Evidence `generation` carried on citations | IV.5 `CitationRef.generation` | Read-only |
| Bounded quote scope; no secret-like material | IV.3 `_semantic` / `contains_forbidden_words` | `EXPOSURE_EXCLUDED` refused |

Book V must not fabricate citations, must not cite references outside the
authorized package, and must not treat `source_ref_id` as an internal database
key.

## 4. Entitlement boundaries

| Boundary | Source | Book V behavior |
|---|---|---|
| Package exposure | IV.3 `exposure_allowed()` | Refuse `CONTEXT_EXPOSURE_VIOLATION` for forbidden exposure |
| Trust class separation | IV.3 `TrustClass` (TRUSTED_CONTROL vs UNTRUSTED_DATA) | Untrusted text quoted only, never asserted |
| Claim/evidence package membership | IV.4 `admission.allowed_refs` | Citations/numbers outside package refused |
| `ACCESS_NOT_ENTITLED` | IV.5 refusal code (highest precedence) | Enforced; never bypassed |
| `DRAFT_FORBIDDEN_FIELDS` | IV.4 (answer, recommendation, order_intent, position_size, win_rate, entitlement, entitlement_grant, canonical_verified, current_price, trade, execute) | Drafts containing these refused |
| Commercial entitlement | EV-GATE-04 (OPEN) | Book V must not assume Book VI entitlement; gate is OPEN |

Book V must not widen entitlement, leak protected identifiers
(`context_items`, `object_id`, `manifest_digest`, `row_id`, `credential`,
`system prompt`), or assume Book VI commercial entitlement is resolved.

## 5. Versioning expectations

| Contract | Version constant | Location | Book V expectation |
|---|---|---|---|
| Evaluation contract | `ASK_EVALUATION_CONTRACT_V1` | `evaluation/versions.py` | Read-only |
| Dataset | `ASK_EVALUATION_DATASET_V1` | `evaluation/versions.py` | Read-only (120 cases) |
| Case schema | `ASK_EVALUATION_CASE_SCHEMA_V1` | `evaluation/versions.py` | Read-only |
| Answer contract | `ASK_ANSWER_CONTRACT_V1` | `answer/versions.py` | Read-only (V1) |
| Context contract | `CONTEXT_CONTRACT_V1` / `CONTEXT_MANIFEST_V1` | `context/versions.py` | Read-only |
| Retrieval contract | `RETRIEVAL_CONTRACT_V1` | `retrieval/versions.py` | Read-only |
| Gateway contract | `ASK_GATEWAY_CONTRACT_V1` / `ASK_GATEWAY_DRAFT_SCHEMA_V1` | `llm_gateway/versions.py` | Read-only (internal) |
| Query contract | `ASK_QUERY_CONTRACT_V1` | `interpreter/versions.py` | Read-only (internal) |

Book V must not introduce `ASK_ANSWER_CONTRACT_V2` or a consolidated
`refusal_limitations` field without separate authorization. All contract
versions are frozen; digests are pinned (BA-33 / 17 hash guards).

## 6. IV.5 / IV.6 ownership boundaries

| Responsibility | Owner | Book V may? |
|---|---|---|
| Answer validation (`validate_answer`) | IV.5 | No — must not bypass |
| Refusal code selection / precedence | IV.5 | No — must not redefine |
| Refusal presentation (`code`/`detail`/`limitations`) | Book V (consumer) | Yes — per F-07a Option C rules §2 |
| Citation rendering | Book V | Yes — per §3, bounded and attributed |
| Depth-aware layout | Book V | Yes — per IV.5 depth section orders |
| Provider integration | IV.4 gateway (caller-supplied) | No — EV-GATE-01 OPEN; no default provider |
| Entitlement resolution | IV.2 `AuthorizationContext` | No — EV-GATE-04 OPEN; Book VI owns |
| Human review (`HumanReviewRecord`) | IV.6 `review.py` | No — EV-GATE-12 OPEN |
| Scoring / metrics | IV.6 `scoring.py` | No — read-only metrics |
| Dataset / case management | IV.6 `dataset.py` / `schema.py` | No — read-only; cases frozen |

## 7. Book V implementation sequence

Book V shall implement in this order, and must not proceed to a step whose
gate is OPEN:

1. **Read-only DTO consumption layer** (F1-01…F1-10): render
   `ValidatedAnswer` / `GovernedAnswerRefusal`, `answer_id`, citations,
   evidence status, model generation, depth, setup eligibility, refusal
   limitations. No gate crossed (F1).
2. **Refusal presentation component** (F2-01): render `code`/`detail`/
   `limitations` per §2. No gate crossed (F2).
3. **Depth-aware layout** (F2-03): Beginner / Operator / Researcher sections per
   IV.5 `SECTION_ORDER`. No gate crossed (F2).
4. **Citation renderer** (F2-02): bounded, attributed, source_ref_id only.
   **Blocked until EV-GATE-02 closes** (citation-surface spec).
5. **Current-state availability indicator** (F2-04): as_of or refuse.
   **Blocked until EV-GATE-07 closes** (live market data).
6. **Governance items** (F3-01…F3-04): citation spec, materiality threshold,
   refusal-precedence ratification, launch threshold table. **Blocked until
   product/governance decisions** (EV-GATE-02/03/11/13).
7. **External integrations** (F4-01…F4-07): live provider, Book VI entitlement,
   market feed, durable snapshots, semantic index, abuse store, human review.
   **Blocked until respective EV-GATEs close** (EV-GATE-01/04/06/07/08/10/12).

**Production release precondition:** BG-C must become PASS and all EV-GATE-01–
13 must close with evidence. Until then, Book V is admitted to deterministic,
offline development only (F1 + non-gated F2 items).

## 8. What Book V must NOT do (hard boundaries)

Book V must never:

- Consume raw `GatewayDraft` provider output or IV.4 internals.
- Bypass `validate_answer` (IV.5).
- Invent or recalculate model statistics; unsupported statistics must refuse
  `INSUFFICIENT_EVIDENCE`.
- Promote historical evidence (`HISTORICAL`/`SUPERSEDED`/`PARKED`/
  `CANDIDATE`/`RESEARCH_FLAG`) to current; no historical model becomes a
  current executable setup.
- Clear a no-go (`NO_GO_ACTIVE` must survive).
- Widen entitlement (`ACCESS_NOT_ENTITLED` enforced; no privileged citation
  leak).
- Interpret missing market data as valid current data (`CURRENT_DATA_UNAVAILABLE`
  / `PROVIDER_NOT_CONFIGURED` honored).
- Convert a refusal into a successful answer (`ERROR` reserved for unexpected
  exceptions only).
- Introduce `ASK_ANSWER_CONTRACT_V2` or `refusal_limitations` without separate
  authorization.
- Assume Book VI commercial entitlement or BG-C operational readiness.
