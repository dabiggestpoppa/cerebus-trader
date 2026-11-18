# CITATION_CONTRACT_AUDIT.md

**BA-41 Rung 1 — Book V Citation Surface Governance — Citation Contract Audit**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `119b46cfce49bd57fab699e53cb63a171dd14efb`
**Mode:** Planning and contract ratification proposal only. No
implementation of gated citation functionality. No Book IV modification.

This document inventories every citation field available across Book IV
blocs IV.2–IV.6 and the Book V presentation/UI layers, classifies each by
trust and exposure authorization, and records the existing behavior and
security law that any citation-surface spec (EV-GATE-02) must respect.

## 1. Citation field inventory

### 1.1 IV.5 `CitationRef` (app/forge/ask_cerebus/answer/schema.py) — ratified V1

`CitationRef` is the user-facing provenance reference type that flows from
IV.5 validation into the Book V presentation model. It is explicitly
documented as "never an internal row or object id."

| Field | Type | Default | Source | Trust class |
|---|---|---|---|---|
| `source_ref_id` | str | required | IV.3 `ContextItem.source_ref_id`; IV.5 `CitationRef` | SAFE TO DISPLAY (authorized package reference only) |
| `source_ref_type` | str | required | IV.3 `ContextItem.source_ref_type` | SAFE TO DISPLAY (MODEL / CLAIM / EVIDENCE / LINEAGE / TERM / SETUP) |
| `source_status` | str | required | IV.3 `ContextItem.source_status` | SAFE TO DISPLAY |
| `provenance_refs` | tuple[str, ...] | () | IV.3 `ContextItem.provenance_refs` | SAFE TO DISPLAY |
| `evidence_refs` | tuple[str, ...] | () | IV.3 `ContextItem.evidence_refs` | SAFE TO DISPLAY |
| `generation` | str | "" | IV.2 `CanonicalRef.generation`; IV.5 `CitationRef.generation` | SAFE TO DISPLAY |

`CitationRef.payload()` exposes exactly these six fields, all safe. The
Book V `PresentationAdapter` projects them verbatim into
`BookVCitation`. The Book V UI `render_citation()` renders all six,
HTML-escaped.

### 1.2 IV.3 `ContextItem` (app/forge/ask_cerebus/context/schema.py) — ratified V1

`ContextItem` is the upstream source from which IV.5 `CitationRef` is
derived via `citations.render()` (IV.5 `app/forge/ask_cerebus/answer/citations.py`).

| Field | Type | Source | Trust class |
|---|---|---|---|
| `item_id` | str | IV.3 | INTERNAL ONLY (never exposed in `CitationRef`) |
| `source_ref_id` | str | IV.3 → IV.5 `CitationRef.source_ref_id` | SAFE TO DISPLAY |
| `source_ref_type` | str | IV.3 → IV.5 `CitationRef.source_ref_type` | SAFE TO DISPLAY |
| `source_status` | str | IV.3 → IV.5 `CitationRef.source_status` | SAFE TO DISPLAY |
| `epistemic_label` | EpistemicLabel | IV.3 | SAFE WITH TRANSFORMATION (depth-appropriate presentation) |
| `layer` | str | IV.3 | SAFE WITH TRANSFORMATION |
| `exposure` | str | IV.3 | INTERNAL ONLY (trust boundary, not rendered) |
| `generation` | str | IV.3 → IV.5 `CitationRef.generation` | SAFE TO DISPLAY |
| `trust_class` | TrustClass | IV.3 | INTERNAL ONLY (governs exposure, not rendered) |
| `facts` | tuple[ContextFact] | IV.3 | SAFE WITH TRANSFORMATION (quote-bounded) |
| `text` | str | IV.3 | INTERNAL ONLY (raw text never rendered as citation) |
| `quote_scope` | str | IV.3 | SAFE WITH TRANSFORMATION (bounded quote display) |
| `provenance_refs` | tuple[str, ...] | IV.3 → IV.5 `CitationRef.provenance_refs` | SAFE TO DISPLAY |
| `evidence_refs` | tuple[str, ...] | IV.3 → IV.5 `CitationRef.evidence_refs` | SAFE TO DISPLAY |
| `token_units` | int | IV.3 | INTERNAL ONLY (budget accounting) |
| `priority` | int | IV.3 | INTERNAL ONLY |
| `mandatory` | bool | IV.3 | INTERNAL ONLY |

`ContextItem.control_payload()` exposes trust-class and internal fields;
`ContextItem.payload()` additionally exposes `item_id`, `text`,
`text_sha256`, `token_units`. Neither is used by the Book V citation
surface. `citations.render()` explicitly rejects internal refs
(`is_internal_ref` matches `PKG.`, `MFD.`, `CTX.`, `ROW.`, `ITEM.`, UUID
prefixes, and tokens like `object_id`, `item_id`, `row_id`, `table:`,
`sql:`, `traceback`, `../`, `\`).

### 1.3 IV.2 `retrieval/refs.py` — ratified V1

IV.2 reference types are upstream of IV.3/IV.5. They carry governed
identity, status, and bounded excerpts. They never carry an answer, a
verdict, an entitlement, or a computed market number.

| Type | Field | Trust class | Notes |
|---|---|---|---|
| `CanonicalRef` | `object_id` | INTERNAL ONLY | never in `CitationRef` |
| `CanonicalRef` | `object_type` | SAFE WITH TRANSFORMATION | maps to `source_ref_type` |
| `CanonicalRef` | `version` | SAFE WITH TRANSFORMATION | |
| `CanonicalRef` | `status` | SAFE WITH TRANSFORMATION | maps to `source_status` |
| `CanonicalRef` | `layer` | SAFE WITH TRANSFORMATION | |
| `CanonicalRef` | `market_scope` | INTERNAL ONLY | |
| `CanonicalRef` | `exposure` | INTERNAL ONLY | |
| `CanonicalRef` | `support_classification` | SAFE WITH TRANSFORMATION | |
| `CanonicalRef` | `generation` | SAFE TO DISPLAY | maps to `CitationRef.generation` |
| `ClaimRef` | `claim_id` | INTERNAL ONLY | never in `CitationRef` |
| `ClaimRef` | `model_ids` / `model_versions` | SAFE WITH TRANSFORMATION | |
| `ClaimRef` | `identity_key` | INTERNAL ONLY | |
| `ClaimRef` | `status` | SAFE WITH TRANSFORMATION | |
| `ClaimRef` | `evidence_ids` | INTERNAL ONLY | |
| `ClaimRef` | `generation` | SAFE TO DISPLAY | |
| `ClaimRef` | `result_value` | INTERNAL ONLY | computed market number |
| `ClaimRef` | `join_status` | SAFE WITH TRANSFORMATION | `EvidenceJoinStatus` |
| `EvidenceRef` | `evidence_id` | INTERNAL ONLY | |
| `EvidenceRef` | `claim_ids` | INTERNAL ONLY | |
| `EvidenceRef` | `status` | SAFE WITH TRANSFORMATION | |
| `EvidenceRef` | `provenance_ids` | INTERNAL ONLY | |
| `EvidenceRef` | `support_classification` | SAFE WITH TRANSFORMATION | |
| `EvidenceRef` | `gaps` | SAFE WITH TRANSFORMATION | |
| `EvidenceRef` | `oos_status` | SAFE WITH TRANSFORMATION | |
| `IntelligenceRef` | all fields | INTERNAL ONLY | market/snapshot intelligence |
| `LineageRef` | `object_id` | INTERNAL ONLY | |
| `LineageRef` | `generation` | SAFE TO DISPLAY | |
| `LineageRef` | `relation` / `claim_ids` | INTERNAL ONLY | |
| `SemanticPassage` | `object_id` | INTERNAL ONLY | |
| `SemanticPassage` | `text` | INTERNAL ONLY | raw passage text |
| `SemanticPassage` | `status` / `quote_scope` / `support_classification` | SAFE WITH TRANSFORMATION | |
| `SemanticPassage` | `score` | INTERNAL ONLY | computed score |
| `NegativeRef` | `object_id` | INTERNAL ONLY | |
| `NegativeRef` | `status` / `generation` / `reason` | SAFE WITH TRANSFORMATION | |
| `Limitation` | `code` / `object_id` / `detail` | INTERNAL ONLY | surfaces as IV.5 `limitations`, not citation |

### 1.4 IV.4 gateway (app/forge/ask_cerebus/llm_gateway/draft.py) — ratified V1

`GatewayDraft.citations` is `tuple[str, ...]` — citation reference ids
validated against `admission.allowed_refs` during `parse_draft()`. Every
claim citation and numeric link must resolve inside the package
(`CITATION_OUTSIDE_PACKAGE` refused). `DRAFT_FORBIDDEN_FIELDS` blocks
authority fields. These are IV.4 internal gatekeeping fields; they are
not part of the Book V citation surface.

### 1.5 IV.6 evaluation schema (app/forge/ask_cerebus/evaluation/schema.py)

`EvaluationCase.expected_citations: tuple[str, ...]` declares the
citations a case expects. `ExpectedClaim.source_ref` names the source
ref a claim must resolve to. These are frozen fixture expectations,
not presentation fields. They drive the citation metric population
(IV.6 R87: two citation populations; `CITATION_RESOLUTION_ACCURACY` ≥
`CITATION_SUPPORT_ACCURACY`).

### 1.6 Book V presentation adapter (app/forge/book_v/presentation/adapter.py)

The adapter projects `ValidatedAnswer.citations` (tuple of IV.5
`CitationRef`) into `BookVCitation`, copying all six fields verbatim.
The projected `record` excludes provider/model/latency/cost/prompt
internals (`_SAFE_RECORD_KEYS`).

### 1.7 Book V UI components (app/forge/book_v/ui/components.py)

`render_citation()` renders `source_ref_id`, `source_ref_type`,
`source_status`, `generation` — all HTML-escaped. `provenance_refs` and
`evidence_refs` are projected by the adapter but not yet rendered by the
UI (bounded safe-field display; expanded rendering is EV-GATE-02).

## 2. Trust and exposure classification summary

| Classification | Fields | Disposition |
|---|---|---|
| SAFE TO DISPLAY | `CitationRef.source_ref_id`, `source_ref_type`, `source_status`, `provenance_refs`, `evidence_refs`, `generation` | Rendered verbatim, HTML-escaped |
| SAFE WITH TRANSFORMATION | `epistemic_label`, `layer`, `support_classification`, `oos_status`, `gaps`, `quote_scope`, `join_status` | May be depth-formatted; no semantic reinterpretation |
| INTERNAL ONLY | `object_id`, `claim_id`, `evidence_id`, `provenance_ids`, `identity_key`, `result_value`, `text`, `score`, `exposure`, `trust_class`, `token_units`, `priority`, `mandatory`, `item_id`, `text_sha256` | Never rendered; filtered before Book V |
| GOVERNANCE UNRESOLVED | citation-surface presentation format/specification; materiality thresholds; citation metrics re-baseline | EV-GATE-02 / EV-GATE-03 |

## 3. Existing behavior

- IV.5 `citations.render()` builds a `CitationRef` only when
  `source_ref_id` is non-internal; otherwise returns `None` and the ref
  is recorded as unresolved.
- `citations.collect()` resolves refs in first-seen order, de-duplicates
  by rendered identity, returns rendered citations + unresolved refs.
- IV.4 `parse_draft()` refuses `CITATION_OUTSIDE_PACKAGE` for any claim
  citation or numeric link outside `admission.allowed_refs`.
- IV.5 `validate_citations` refuses `CITATION_REQUIRED` /
  `CITATION_UNRESOLVED` when claim citations do not resolve.
- The Book V UI renders only `source_ref_id`, `source_ref_type`,
  `source_status`, `generation` per citation (bounded safe-field
  display). `provenance_refs` / `evidence_refs` are projected but not
  rendered — this is the gap EV-GATE-02 addresses.

## 4. Discrepancies / open items

1. **No ratified public citation-surface specification.** EV-GATE-02
   (class F3, owner Product/UX) requires a "ratified citation-surface
   spec; IV.6 citation metrics re-baselined on it." Currently OPEN.
2. **`provenance_refs` / `evidence_refs` projected but not rendered.**
   The adapter carries them; the UI omits them. Expanded rendering is
   gated on EV-GATE-02.
3. **`epistemic_label` / `support_classification` / `oos_status`**
   carried on `ContextItem` but only partially exposed through
   `CitationRef` (which has no epistemic_label field). Depth-appropriate
   presentation of historical/research-flag labels is not specified.
4. **IV.6 citation metrics** (`CITATION_RESOLUTION_ACCURACY`,
   `CITATION_SUPPORT_ACCURACY`) are not yet re-baselined on a ratified
   public citation surface — required for EV-GATE-02 closure evidence.

## 5. Security law (binding on any citation-surface spec)

A citation presentation may not:

- Expose hidden retrieval objects, internal row IDs, private artifact
  paths, provider prompts, system instructions, credentials, protected
  evidence, or unauthorized model records.
- Invent provenance, substitute evidence, change evidence generation,
  promote research to production, promote historical to current, claim
  support from an unrelated source, convert unresolved evidence to
  resolved, or bypass IV.5 validation.

The displayed citation must remain a projection of previously authorized
evidence only. `is_internal_ref()` and `CITATION_OUTSIDE_PACKAGE`
refusal enforce this at the IV.4/IV.5 boundary; the Book V UI must not
weaken it.

## 6. What EV-GATE-02 must close

Per FEASIBILITY_GATE.md §4.1:

> `EV-GATE-02` | IV.5 public citation presentation contract (R26 of IV.5) | F3 |
> Product/UX | ratified citation-surface spec; IV.6 citation metrics
> re-baselined on it | OPEN

Closure requires:

1. A ratified citation-surface presentation spec (governance decision,
   owner Product/UX).
2. IV.6 citation metrics re-baselined on the ratified spec.

Until then, BV-F2-02 (citation renderer) and BV-F3-01 (citation-surface
spec) remain deferred.
