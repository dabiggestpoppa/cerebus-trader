# GOVERNANCE_DECISION.md

**BA-41 Rung 1 — Book V Citation Surface Governance — Governance Decision Proposal**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `119b46cfce49bd57fab699e53cb63a171dd14efb`
**Mode:** Planning and contract ratification proposal only. No
implementation of gated citation functionality. EV-GATE-02 remains OPEN.

This document presents three bounded citation-presentation options
(OPTION A / B / C), evaluates each against the security law and depth
requirements, and recommends one option with explicit tradeoffs. The
recommendation is explicit; the governance decision itself belongs to
the product owner and is not made here.

## 1. EV-GATE-02 closure requirements

Per FEASIBILITY_GATE.md §4.1:

| Gate | Description | Class | Owner | Closure evidence | Status |
|---|---|---|---|---|---|
| EV-GATE-02 | IV.5 public citation presentation contract (R26 of IV.5) | F3 | Product/UX | ratified citation-surface spec; IV.6 citation metrics re-baselined on it | OPEN |

This rung is governed by the following stop conditions:

- Do not close EV-GATE-02 automatically.
- Do not implement BV-F2-02 (citation renderer).
- Do not implement BV-F3-01 (citation-surface spec ratification).
- Do not modify Book IV.
- Do not introduce new routes or migrations.
- Do not begin live provider or market integration.
- Do not claim production readiness.

## 2. Existing deterministic behavior (baseline)

The Book V presentation layer already renders a bounded, attributed
citation surface using only IV.5 safe fields:

| Field rendered | Source | Security status |
|---|---|---|
| `source_ref_id` | IV.5 `CitationRef` | SAFE TO DISPLAY |
| `source_ref_type` | IV.5 `CitationRef` | SAFE TO DISPLAY |
| `source_status` | IV.5 `CitationRef` | SAFE TO DISPLAY |
| `generation` | IV.5 `CitationRef` | SAFE TO DISPLAY |

Fields projected by the adapter but **not** rendered by the UI:
`provenance_refs`, `evidence_refs`.

All text is HTML-escaped. `is_internal_ref()` blocks internal refs at
the IV.4/IV.5 boundary. `CitationRef` is documented as "never an
internal row or object id."

Missing relative to a full citation-surface spec:

- No depth-aware citation presentation (BEGINNER / OPERATOR /
  RESEARCHER differ in detail level).
- No historical designation or research-only evidence labeling.
- No provenance/evidence-ref expansion.
- No `epistemic_label` / `support_classification` / `oos_status`
  presentation.
- No explicit missing-evidence or citation-resolution-failure UI.
- No provenance-completeness vs. comprehension tradeoff decision.

## 3. Citation presentation options

### OPTION A — Minimal attributed source reference

**Design.** Render only the four already-exposed safe fields per
citation: `source_ref_id`, `source_ref_type`, `source_status`,
`generation`. HTML-escaped, attributed, bounded. No provenance-ref
expansion, no depth variation, no historical/research labeling beyond
what `source_status` already carries.

| Criterion | Assessment |
|---|---|
| User comprehension | Low — `source_ref_id` is an authorized package reference, not a human-readable source name; users cannot tell what the citation points to without external context |
| Provenance completeness | Minimal — authorized reference and generation only; no provenance chain |
| Internal data exposure risk | None — all four fields are ratified safe fields |
| Complexity | Lowest — reuses existing UI render path unchanged |
| Existing contract compatibility | Full — no contract change |
| Accessibility | Simple — single `<div>` per citation with `data-ref-id` |
| Determinism | Fully deterministic — pure function of `CitationRef` |
| Book VI entitlement dependency | None |
| Book VII data dependency | None |
| Book VIII abuse considerations | None — no new surface to abuse |

### OPTION B — Expanded evidence card

**Design.** Render the four safe fields plus `provenance_refs` and
`evidence_refs` (already projected by the adapter, currently omitted by
the UI), presented as an attributed evidence card per citation. Add
depth-aware detail: BEGINNER shows `source_ref_id` + `generation`;
OPERATOR adds `source_ref_type`/`source_status`; RESEARCHER adds
`provenance_refs`/`evidence_refs`.

| Criterion | Assessment |
|---|---|
| User comprehension | Medium — reference IDs are still not human-readable names; evidence card adds provenance chain visibility |
| Provenance completeness | High — full provenance chain visible at RESEARCHER depth |
| Internal data exposure risk | Low — all fields are ratified safe fields; `provenance_refs`/`evidence_refs` are already projected by the adapter |
| Complexity | Medium — depth-aware rendering + new fields |
| Existing contract compatibility | Full — no contract change; uses already-projected fields |
| Accessibility | Moderate — expandable card; needs ARIA controls for depth toggles |
| Determinism | Fully deterministic — pure function of `CitationRef` |
| Book VI entitlement dependency | None |
| Book VII data dependency | None |
| Book VIII abuse considerations | Low — provenance/evidence refs are authorized package references, not enumerable internal objects |

### OPTION C — Layered disclosure with evidence-detail view

**Design.** Concise citation (OPTION A fields) by default, plus a
user-requested evidence-detail view that expands to show
`provenance_refs`/`evidence_refs`/`epistemic_label`/`support_classification`
/`oos_status`. Depth-aware: BEGINNER sees concise only; OPERATOR can
expand; RESEARCHER sees detail inline. Requires interaction state
(not currently modeled) and a detail-view contract.

| Criterion | Assessment |
|---|---|
| User comprehension | Medium-High — concise default avoids overload; detail available on demand |
| Provenance completeness | High — full chain available on request |
| Internal data exposure risk | Low-Medium — all fields are safe, but detail view increases surface area; must enforce depth gating and not expose internal IDs |
| Complexity | Highest — interaction state, detail-view contract, depth-gated expansion |
| Existing contract compatibility | Partial — requires UI state model not yet authorized; no contract change but new behavior |
| Accessibility | Moderate-High — expand/collapse needs ARIA `aria-expanded`, keyboard handling |
| Determinism | Deterministic per view state — but state introduces non-determinism across interactions unless serialized |
| Book VI entitlement dependency | Potential — detail view could be gated on entitlement (EV-GATE-04) |
| Book VII data dependency | Potential — `support_classification`/`oos_status` relate to research evidence (EV-GATE-09/10) |
| Book VIII abuse considerations | Medium — detail view is an additional extraction surface; rate/aggregation concerns (EV-GATE-06) |

## 4. Recommendation

**Recommended: OPTION B (Expanded evidence card).**

Rationale:

- **Highest provenance completeness among low-complexity options.** OPTION B
  exposes the full provenance chain (`provenance_refs`/`evidence_refs`) that
  the adapter already projects, without the interaction-state complexity of
  OPTION C.
- **No new contract or behavior surface.** OPTION B uses fields already
  projected by the `PresentationAdapter`; only the UI render layer changes.
- **Depth-aware without interaction state.** OPTION B's depth-aware detail
  can be implemented as a pure function of `BookVInterfaceResponse.depth`,
  preserving determinism. OPTION C's detail view requires interaction state
  (not yet authorized).
- **Lowest abuse risk.** OPTION C's detail view is an additional extraction
  surface relevant to EV-GATE-06 (cross-session corpus-extraction
  protection); OPTION B's bounded card is lower risk.
- **No Book VI/VII/VIII dependency.** OPTION B does not depend on
  commercial entitlement, research evidence, or abuse-store integration.

**Tradeoffs accepted:**

- User comprehension remains limited because `source_ref_id` is an
  authorized package reference, not a human-readable source name. A human
  name mapping is Book VI/VII territory and is out of scope.
- `epistemic_label` / `support_classification` / `oos_status` are not
  rendered in OPTION B; historical/research-flag labeling remains
  governance-unresolved pending EV-GATE-02 closure and possible
  EV-GATE-09/EV-GATE-10 input.

## 5. Explicit product-owner decision needed

The product owner (EV-GATE-02 owner: Product/UX) must:

1. **Ratify the citation-surface presentation spec** — select OPTION A,
   B, or C (or a hybrid), specifying exactly which fields render at each
   depth and whether `provenance_refs`/`evidence_refs` are included.
2. **Authorize IV.6 citation metrics re-baselining** — `CITATION_RESOLUTION_ACCURACY`
   and `CITATION_SUPPORT_ACCURACY` must be re-baselined on the ratified
   spec (required EV-GATE-02 closure evidence).
3. **Confirm depth-aware presentation rules** — if OPTION B or C, confirm
   which fields appear at BEGINNER / OPERATOR / RESEARCHER.
4. **Confirm security law acceptance** — the spec must not weaken
   `is_internal_ref()` / `CITATION_OUTSIDE_PACKAGE` enforcement or expose
   any INTERNAL-ONLY field.

Until the product owner ratifies the spec, EV-GATE-02 remains OPEN,
BV-F2-02 and BV-F3-01 remain deferred, and no citation renderer beyond
the existing bounded safe-field display may be implemented.

## 6. What this document does NOT do

- Does not close EV-GATE-02.
- Does not implement BV-F2-02 or BV-F3-01.
- Does not modify Book IV source, tests, or fixtures.
- Does not introduce routes, migrations, or credentials.
- Does not begin live provider or market integration.
- Does not claim production readiness.
