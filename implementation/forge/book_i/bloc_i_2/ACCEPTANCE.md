# Book I / Bloc I.2 — Acceptance

Bloc I.2 may be ratified only if all conditions pass.

## A. Artifact registry
- all frozen default artifact classes are valid and registrable: PDF, MARKDOWN, TXT,
  PINE, CSV, XLSX, VISUAL, NOTEBOOK, SCRIPT, CONVERSATION_DERIVED, EXTERNAL_REFERENCE
- the registry is extensible: a new syntactically valid class name can be registered
  after construction
- duplicate class registration is rejected; frozen defaults cannot be removed or
  overwritten
- artifact identity is a typed `ART.*` canonical ID (I.1 prefix/type validation reused)
- an unregistered artifact class name is rejected at registration

## B. Content identity
- identical content bytes produce identical content identity (`sha256:<hex>`)
- different content bytes produce different content identity
- derived artifact IDs are deterministic: same class + same bytes => same ID
- duplicate artifact identity is rejected (duplicate ID; duplicate content identity at
  the same locator)
- a MISSING source carries no content identity (content is never fabricated for a
  source that was not found)

## C. Provenance edges
- valid edges accepted for SUPPORTS, DEFINES, IMPLEMENTS, VISUALIZES, DERIVED_FROM,
  SUPERSEDES
- unknown relation values fail validation
- direction/type is enforced: edge source must be an `ART.*` artifact ID, edge target
  must be a canonical object ID
- unknown endpoints (artifact or canonical object not registered) are rejected
- duplicate edges are rejected
- adding an edge never mutates canonical object identity or status

## D. Visual semantics
- a visual/infographic artifact with provenance edges can never be classified as
  independent empirical support, regardless of source state
- a launch numerical claim whose support chain ends in visual-only artifacts is
  surfaced as a GAP, not as a resolved source chain
- registering a VISUAL artifact never creates an Evidence object

## E. Conversation-derived sources
- conversation-derived artifacts register normally but classify as non-empirical
- a claim chain ending only in conversation-derived sources is not counted as
  empirical source coverage and is surfaced explicitly
- conversation-derived state can never transition directly to VERIFIED

## F. Incomplete source states
- all seven states are valid: LOCATED, READ, VERIFIED, MATERIALIZED, MISSING, PARTIAL,
  CONVERSATION_DERIVED
- legal transitions pass (e.g. LOCATED -> READ, READ -> VERIFIED, VERIFIED ->
  MATERIALIZED, MISSING -> LOCATED, PARTIAL -> READ)
- illegal transitions fail (e.g. MISSING -> VERIFIED, CONVERSATION_DERIVED -> VERIFIED,
  MATERIALIZED -> LOCATED); same-state transitions are no-ops
- unknown state values fail validation
- MISSING and PARTIAL remain explicit unresolved states in audit output; a historical
  unresolved source is reported as unresolved rather than fabricated or dropped

## G. Provenance audit
- orphan canonical objects (zero provenance edges) are reported
- evidence lacking source provenance is reported
- a launch numerical claim with no provenance chain is surfaced as a GAP
- a launch numerical claim with a non-empirical chain (visual-only,
  conversation-derived-only, mixed non-empirical, not-yet-read) is surfaced as a GAP
- unresolved sources (MISSING/PARTIAL/CONVERSATION_DERIVED) are listed explicitly
- visual-only support is listed explicitly
- audit output is deterministic: the same content yields byte-identical JSON regardless
  of registry insertion order, with no timestamps

## H. Invariants
- registering artifacts never creates Evidence (or any) canonical objects
- a provenance edge can never promote canonical/evidence status
- no persistence, retrieval, UI or provider behavior inside the provenance module
  (stdlib + pydantic + existing app.forge.kernel only)

## I. Regression / non-interference
- existing I.1 focused suite remains green (41 tests)
- full repository suite remains green
- no existing test weakened or removed
- no existing Signal Guard file changed
- no new external dependency

## Evidence required

Exact pytest command/output, source/provenance coverage counts from fixtures,
changed-file inventory, migrations (NONE unless approved), security implications,
unresolved provenance gaps, known limitations, acceptance-clause mapping, ratification
decision.
