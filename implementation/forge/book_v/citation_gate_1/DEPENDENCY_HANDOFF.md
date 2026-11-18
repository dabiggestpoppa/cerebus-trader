# DEPENDENCY_HANDOFF.md

**BA-41 Rung 1 — Book V Citation Surface Governance — Dependency Handoff**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `119b46cfce49bd57fab699e53cb63a171dd14efb`
**Mode:** Planning and contract ratification proposal only.

## 1. Ratified upstream DTO contracts (Book IV — read-only)

Book V citation presentation consumes the following Book IV DTO surfaces
as read-only inputs. It does not extend, retype, or add fields to them.

| Contract | Source (Book IV bloc) | Status | Book V may use? |
|---|---|---|---|
| `ValidatedAnswer` DTO | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| `GovernedAnswerRefusal` DTO | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| `CitationRef` | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| `AnswerClaim` (source_refs, citation_ids) | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| Evidence status / epistemic label | IV.3 `context/enums.py` | Ratified (V1) | Yes |
| Model generation | IV.2 `retrieval/refs.py` (`CanonicalRef.generation`) | Ratified (V1) | Yes |
| Answer depth | IV.5 `answer/enums.py` (`AnswerDepth`) | Ratified (V1) | Yes |
| Refusal limitations | IV.5 `GovernedAnswerRefusal.limitations` | Ratified (V1, F-07a Option C) | Yes |
| Safe provenance | IV.3 `ContextItem` / IV.5 `CitationRef` | Ratified (V1) | Yes |

`CitationRef` fields exposed to Book V: `source_ref_id`,
`source_ref_type`, `source_status`, `provenance_refs`,
`evidence_refs`, `generation`. `source_ref_id` is documented as "never an
internal row or object id."

Book V must not consume raw `GatewayDraft` provider output or any IV.4
surface not exposed through the IV.5 DTO.

## 2. UI trust boundaries (citation surface)

The citation presentation surface must consume only
`BookVInterfaceResponse.citations` (tuple of `BookVCitation`, each a
verbatim projection of IV.5 `CitationRef`). It must never:

- Consume `GatewayDraft` directly.
- Read raw `AuthorizedContextPackage` or `ContextItem.item_id`/`text`.
- Read private retrieval records (`CanonicalRef.object_id`,
  `ClaimRef.claim_id`, `EvidenceRef.evidence_id`, `LineageRef.object_id`,
  `SemanticPassage.text`, `NegativeRef.object_id`).
- Read provider credentials or prompts.
- Bypass IV.5 validation (`validate_answer`).
- Invent provenance, substitute evidence, change evidence generation,
  promote historical to current, or convert unresolved evidence to
  resolved.
- Weaken `is_internal_ref()` (blocks `PKG.`, `MFD.`, `CTX.`, `ROW.`,
  `ITEM.`, UUID prefixes, `object_id`, `item_id`, `row_id`, `table:`,
  `sql:`, `traceback`, `../`, `\`).
- Weaken `CITATION_OUTSIDE_PACKAGE` refusal (IV.4 `parse_draft()`).

Any citation displayed must remain a projection of previously authorized
evidence.

## 3. Book VI / VII / VIII dependencies

| Book | Dependency | Gate | Blocks citation surface? |
|---|---|---|---|
| Book VI | Commercial entitlement | EV-GATE-04 (OPEN) | Potential — detail-view entitlement gating (OPTION C only) |
| Book VII | Durable historical snapshots | EV-GATE-08 (OPEN) | No — historical labels already preserved |
| Book VII | Real semantic retrieval index | EV-GATE-10 (OPEN) | No — citation surface is fixture-backed |
| Book VIII | Shared abuse store + rate/aggregation | EV-GATE-06 (OPEN) | Potential — detail-view extraction surface (OPTION C) |

## 4. Gate dependencies (EV-GATE-01 through EV-GATE-13)

Relevant to citation surface:

| Requirement | Gate | Status | Blocks? |
|---|---|---|---|
| BV-F2-02 (citation renderer) | EV-GATE-02 | OPEN | Yes |
| BV-F3-01 (citation-surface spec) | EV-GATE-02 | OPEN | Yes |
| BV-F2-04 (current-state indicator) | EV-GATE-07 | OPEN | No (separate) |
| BV-F4-03 (market data feed) | EV-GATE-07 | OPEN | No |

All other gates (EV-GATE-01, 03–06, 08–13) are not citation-surface
blockers but remain OPEN for production release.

## 5. Rung 2 implementation sequence

The next rung may implement citation presentation only after EV-GATE-02
closes:

1. ✅ Book V presentation adapter (BA-38) — DONE; projects `CitationRef`
   verbatim, excludes provider internals.
2. ✅ Book V UI components (BA-40) — DONE; renders bounded safe-field
   citations (`source_ref_id`, `source_ref_type`, `source_status`,
   `generation`).
3. ⏸️ Ratify citation-surface spec (BV-F3-01) — blocked by EV-GATE-02;
   product-owner decision (GOVERNANCE_DECISION.md recommends OPTION B).
4. ⏸️ Re-baseline IV.6 citation metrics — blocked by EV-GATE-02; required
   closure evidence.
5. ⏸️ Implement citation renderer (BV-F2-02) — blocked by EV-GATE-02;
   deterministic once spec ratified.
6. ⏸️ Current-state availability indicator (BV-F2-04) — blocked by
   EV-GATE-07.

No rung may implement production deployment, live provider integration,
Book VI entitlement, Book VII market integration, Book VIII security
expansion, or any behavior depending on an OPEN gate or BG-C.

## 6. Stop conditions

- Do not close EV-GATE-02 automatically.
- Do not implement BV-F2-02 before EV-GATE-02 closes.
- Do not implement BV-F3-01 before product-owner ratification.
- Do not modify Book IV source, tests, or fixtures.
- Do not introduce new routes or migrations.
- Do not add provider credentials.
- Do not begin live provider or market integration.
- Do not claim production readiness.

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED
