# Book I / Bloc I.2 — Source & Provenance Fabric Implementation Plan

Status: ACTIVE
Planning freeze: 60e067547b9d9165d94e4f074e0db0ba58e59e24
Dependency head: Bloc I.1 ratified PASS at aca9438

## Scope

Implement the in-memory source & provenance fabric for FORGE:

1. Artifact registry (extensible source/artifact classes).
2. Deterministic content identity for artifacts.
3. Typed provenance edges from artifacts to canonical objects.
4. Visual semantics guard (visual != independent statistical proof).
5. Explicit incomplete source states (LOCATED/READ/VERIFIED/MATERIALIZED/MISSING/PARTIAL/CONVERSATION_DERIVED).
6. Deterministic provenance audit reporting.

The existing Signal Guard application remains untouched; all new runtime code is
isolated under the existing `app/forge` package.

## Reuse

- `app/forge/canonical.py` — `CanonicalId`, `ObjectType.ARTIFACT`, `CanonicalObject`,
  `CanonicalRegistry`, `EvidenceStatus`, `ProductExposure`, `Layer`.
- Source contracts:
  - corpus/canonical/CEREBUS_CANONICAL_TAXONOMY_V1.md §16 ARTIFACT (PDF, MD, Pine, CSV,
    workbook, infographic, notebook, conversation-derived memo)
  - planning/forge/books/BOOK_I_CORPUS_CANONICAL_PLAN_V1.md — BLOC I.2 chapters I.2.1-I.2.6
  - corpus/canonical/CLAIM_REGISTRY_V1.md — retrieval rule (query -> model -> claim -> evidence)

Runtime baseline: Python 3.11, Pydantic >=2 already in requirements. No new dependency.

## Deliverables

1. `app/forge/provenance.py`
2. `tests/test_forge_provenance.py`
3. Evidence and ratification artifacts in this folder.

## Fabric contract

### I.2.1 Artifact registry
- Frozen default classes: PDF, MARKDOWN, TXT, PINE, CSV, XLSX, VISUAL (infographic),
  NOTEBOOK, SCRIPT, CONVERSATION_DERIVED, EXTERNAL_REFERENCE.
- Extensible: additional class names can be registered; registered names cannot be
  removed and frozen defaults cannot be overwritten or deleted.
- Registering an artifact NEVER creates, mutates or implies an Evidence (or any)
  canonical object. Artifact != Evidence.

### I.2.2 Content identity
- Typed `ART.*` canonical artifact IDs (I.1 prefix validation reused).
- `content_identity` = `sha256:<hex>` of the exact bytes — deterministic where the
  underlying content is deterministic.
- Derived artifact ID: `ART.<CLASS>.<HASH24>` — identical bytes + class always
  produce the same ID; different bytes produce different identities.
- Also represents: source generation, version, repository/library locator,
  created/observed metadata (caller-supplied strings, no clock dependency),
  materialization state (derived), source state (explicit state machine).

### I.2.3 Object provenance edges
- Typed edges `artifact -> canonical object` with relation:
  SUPPORTS, DEFINES, IMPLEMENTS, VISUALIZES, DERIVED_FROM, SUPERSEDES.
- Endpoints must exist; duplicates rejected; direction/type enforced by typed IDs.
- Edges NEVER mutate canonical objects or their status.
- Concept/model lineage (object -> object, I.1 `CanonicalReference` / LINEAGE) stays
  distinct from physical artifact provenance (artifact -> object). No crossover.

### I.2.4 Visual semantics
- VISUAL artifacts preserve historical semantics, relationships, operator teaching,
  terminology and constants as provenance/teaching support.
- Visual support can never classify as independent empirical support, regardless of
  source state. VISUAL != independent statistical proof; a number in an infographic
  does not become a verified numerical claim.

### I.2.5 Incomplete source states
- States: LOCATED, READ, VERIFIED, MATERIALIZED, MISSING, PARTIAL, CONVERSATION_DERIVED.
- Explicit transition map; same-state transitions are no-ops.
- MISSING is recoverable (MISSING -> LOCATED/PARTIAL) and never proof that a source
  never existed. MISSING sources carry no content identity (never fabricated).
- CONVERSATION_DERIVED can never transition directly to VERIFIED.

### I.2.6 Provenance audit
Deterministic report (sorted, no timestamps, stable JSON) covering:
- source coverage counts (any source / empirical source / no source);
- orphan canonical objects (zero provenance edges);
- evidence lacking source provenance;
- launch numerical claims lacking a source chain (GAP);
- numerical claims whose chain exists but is non-empirical (visual-only,
  conversation-derived-only, mixed non-empirical, not-yet-read) — GAP;
- unresolved sources (MISSING/PARTIAL/CONVERSATION_DERIVED) listed explicitly;
- historical objects with explicitly unresolved references (I.1 partial mechanism);
- visual-only support and conversation-derived support;
- deterministic serialization + content hash.

Numerical-claim detection (frozen for this bloc): a CLAIM object whose `metadata`
carries `numerical: true` or a non-empty `result`/`statistic` value. Bloc I.3 stamps
launch claims accordingly; I.2 only makes the chain representable and auditable.

Desired chain: QUERY -> MODEL -> CLAIM -> EVIDENCE -> SOURCE/ARTIFACT.
I.2 does NOT perform retrieval; it makes the chain representable and auditable.

## Invariants

- Artifact != Evidence.
- Visual != statistical proof.
- Conversation-derived != verified empirical evidence.
- Missing/partial provenance is explicit; never silently invent a source.
- A launch numerical claim must ultimately route Claim -> Evidence -> Source/Artifact.
- Provenance alone never changes canonical status.
- No persistence (Book II owns it), no retrieval, no LLM, no UI, no providers.
- No broad recovery restart; gaps are represented honestly.

## Non-goals

Persistence, database, FastAPI routes, embeddings/retrieval, corpus backfill (I.3),
live market data, LLM, Whop/OpenRouter, UI, trading execution, ID/status remapping of
hand-authored Markdown cards.

## Implementation sequence

1. Freeze ACCEPTANCE.md.
2. Artifact classes + extensible class registry + artifact model/registry.
3. Content identity + deterministic derived IDs + duplicate rejection.
4. Source-state machine + materialization state.
5. Typed provenance edges + edge registry validation.
6. Support classification (empirical / visual-only / conversation-derived / ...).
7. Deterministic provenance audit.
8. Tests against current canonical IDs as fixtures.
9. Evidence, then ratification.

## Stop conditions

Stop and write a GAP/ADR if implementation requires changing the frozen taxonomy,
collapsing Artifact into Evidence, letting provenance promote canonical status,
inventing a missing source, or introducing persistence/retrieval into Book I.
