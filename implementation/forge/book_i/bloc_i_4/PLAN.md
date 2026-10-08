# Book I / Bloc I.4 — Retrieval Index — PLAN

> Status: ACTIVE
> Date: 2026-10-08
> Governing law: RETRIEVAL RELEVANCE IS NOT EVIDENCE AUTHORITY. An index record
> is a *finding surface* over governed canonical truth; it never becomes a
> competing source of truth, never changes epistemic status, and never releases
> a protected body before the II.4 policy decision.

## 0. Source inventory (Phase 0 truth)

Verified at `05c74a1204a8c2a33c53206710e9d2399bb5b87b` (I.3 ratified head;
remote `origin/forge` in sync; freeze `60e067547b9d9165d94e4f074e0db0ba58e59e24`
is an ancestor). Ratifications verified: I.1, I.2, II.1, II.2, II.3, II.4, I.3 —
all CLOSED — PASS. Baseline at this head: **446 passed, 18 skipped**.

Frozen contracts read (no design may contradict them):

| Contract | Path | Role in I.4 |
|---|---|---|
| Master build plan (Bloc I.4 chapters I.4.1–I.4.6) | `planning/forge/GLX_FORGE_MASTER_BUILD_PLAN_V1.md` | chapter scope |
| Book I plan (Ch I.4.1–I.4.7 + Acceptance I.4) | `planning/forge/books/BOOK_I_CORPUS_CANONICAL_PLAN_V1.md` | acceptance law |
| Retrieval Object Schema V1 | `corpus/canonical/RETRIEVAL_OBJECT_SCHEMA_V1.md` | record field contract |
| Product Exposure Rules V1 | `corpus/canonical/PRODUCT_EXPOSURE_RULES_V1.md` | entitlement-before-retrieval |
| Answer Contract V1 | `corpus/canonical/ANSWER_CONTRACT_V1.md` | depth routing, numerical safety |
| Claim Registry V1 | `corpus/canonical/CLAIM_REGISTRY_V1.md` | claim→model→evidence routing |
| Ontology Crosswalk V1 | `corpus/canonical/ONTOLOGY_CROSSWALK_V1.md` | alias/generation routing |
| Planning freeze manifest | `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` | frozen lineage |

Ratified substrate reused (never re-implemented): I.1 `canonical.py` domain
kernel, I.2 `provenance.py` fabric, I.3 `backfill/*` corpus migration, II.2
`PersistenceGateway` port + memory/SQL gateways, II.4 `policy.py` kernel and
`ForgePolicyEnforcementService` deny-before-load primitive.

Persisted state indexed by I.4 (verified by I.3 evidence): 30 canonical
objects (7 MODEL, 10 EVIDENCE, 3 SETUP, 10 CLAIM), 29 artifacts, 38 provenance
edges, 9 quarantined non-card sources, 0 card-file quarantines.

## 1. What I.4 is (and is not)

I.4 is the **Retrieval Object Compiler + governed retrieval index** — frozen
chapters:

- I.4.1 canonical object → normalized retrieval object (compiler)
- I.4.2 structured exact fields (numbers, tiers, levels, versions, N, status,
  relationships)
- I.4.3 safe semantic text (concise explanatory text stripped of
  INTERNAL_METHOD / INTERNAL_CODE)
- I.4.4 alias / generation routing (historical alias → canonical term)
- I.4.5 exposure compiler (stamp retrieval objects with entitlement metadata)
- I.4.6 incremental rebuild (changed canonical object invalidates/rebuilds
  dependent retrieval objects)
- I.4.7 determinism (same canonical version ⇒ same retrieval payload/hash)

Acceptance I.4 (frozen): *compiler produces stable launch retrieval corpus;
internal-only fields absent from subscriber-safe output.*

**Explicitly out of scope:** I.5 QA, Ask CEREBUS, OpenRouter, embedding
providers, vector/pgvector storage, Whop/licensing, any public corpus API or
read route, live market calculation, LLM context assembly.

### 1.1 Lexical, not semantic — frozen-plan reading

The frozen Book I plan for I.4 requires *safe semantic text* (Ch I.4.3 =
generated explanatory text) and *alias/generation routing* (I.4.4). It does
NOT require vector/embedding retrieval in I.4: embeddings are owned by Book VII
`VII.5 Retrieval Rebuild` ("incremental compile; embeddings; structured index"),
and the II.1 readiness contract already reports `pgvector: NOT_APPLICABLE —
belongs to a later retrieval bloc`. Therefore I.4 implements **lexical (token)
retrieval over governed text plus exact structured lookup**, adds no embedding
infrastructure, no provider, and no new dependency. A later bloc may add
vectors; the deterministic structured/lexical precedence defined here remains
binding so a semantic layer can never outrank exact identity.

## 2. Index authority (Phase 2)

Records are compiled from **validated canonical persistence through the II.2
port** (`list_object_ids` → `get_object` → `edges_for_object` →
`get_artifact`), never from Markdown, never from raw corpus files. The I.3
canonicalizer output is therefore *already-governed state* by the time I.4 sees
it.

Each retrieval record preserves or resolves:

| Requirement | Field |
|---|---|
| canonical ID and type | `object_id`, `object_type` |
| canonical version/status | `canonical_version`, `status` |
| evidence status | `status` (verbatim; never re-derived) |
| product exposure | `exposure_class` |
| source artifact + content identity | `source_artifact_ids` (ids in record); locator/`content_identity`/`source_state` exposed only through guarded provenance navigation |
| provenance edges | `provenance_edges` (artifact_id, relation) |
| claim population identity | `claim_identity` (8 dimensions) on CLAIM records |
| model/setup relationships | `parent_ids` + `related_ids` (typed links) |
| index generation/version | `generation` |

**No competing truth.** The index never writes to the persistence port, never
creates/updates a canonical object, and is rebuilt from persistence on demand.
A stale index can never override a canonical record: reads that need governed
truth (provenance navigation) load through the port under policy, and index
freshness is checked explicitly (`is_stale`).

### 2.1 Header / body split (the deny-before-load substrate)

Every record is split so that *resource metadata exists without loading
protected content* (II.4 `ResourcePolicyMetadata` law: "authorizing a resource
NEVER requires loading its protected body"):

- **`RetrievalHeader` (safe metadata):** `object_id`, `object_type`,
  `canonical_version`, `status`, `exposure`, `layer`, `market_scope`,
  `model_family`, `source_artifact_ids`. Used for candidate selection,
  freshness, audit and policy input.
- **`RetrievalObject` body:** everything else — `retrieval_text`,
  `structured.*`, `routing.*`, `leakage.*`, `conflict.*`,
  `provenance_edges`, `related_ids`, `claim_identity`.

The body is loaded ONLY through the II.4 `guard()` primitive after a policy
decision has allowed that exact resource.

## 3. Structured retrieval (Phase 3)

`RetrievalQuery` supports exact governed lookup by **actual schema fields**:

| Filter | Source field |
|---|---|
| `canonical_id` | `CanonicalObjectRecord.canonical_id` |
| `object_type` | `record.object_type` |
| `market` | `market_scope` (MODEL/SETUP card `market_scope`, EVIDENCE card `market`, CLAIM `ClaimIdentity.market`) |
| `model_family` | canonical-id family token (`MOD.EUR.…` → `EUR`) — derived from the frozen id grammar, not an invented field |
| `status` | `record.status` |
| `exposure` | `record.exposure` (a filter grants nothing; II.4 still decides) |
| `layer` | `record.layer` |
| `source_artifact` | `source_artifact_ids` |
| `provenance_relation` | `provenance_edges[].relation` |
| `claim_identity` | `ClaimIdentity` compared with `compare_claim_identity` ⇒ SAME_POPULATION only |
| `text` | lexical over governed text |

Facet population uses only fields that exist; an unstated facet stays EMPTY,
never fabricated:

| Frozen facet | Actual field | Absent ⇒ |
|---|---|---|
| `clocks` | `ClaimIdentity.clock_origin` / `EvidenceCard.clock_origin` | omitted when `NOT_SPECIFIED_IN_SOURCE` |
| `events` | `event_definition` | omitted |
| `states` | `ModelCard.state_space` | `()` |
| `levels` | `SetupOperatorCard.l3_destination/l2_path/l1_execution` | `()` |
| `metrics` | `EvidenceCard.metric` | `()` |
| `sample_n` | `EvidenceCard.sample_n` (>0) | `None` |
| `period` | `EvidenceCard.data_period` | omitted |
| `implementation_ids` | provenance edges with relation `IMPLEMENTS` | `()` |
| `terms` | title tokens + type vocabulary (`model_type`, `execution_class`, `evidence_type`) | `()` |
| `aliases` | Ontology Crosswalk rows matched against this object's own text | `()` |

**Exact structured identity outranks textual similarity.** Two claims with
different `ClaimIdentity` populations remain distinct records with distinct
ids even when prose is nearly identical; a `claim_identity` query returns only
SAME_POPULATION matches and never merges.

## 4. Text / lexical retrieval and ranking precedence (Phase 4)

Lexical search operates over `title + retrieval_text + terms + aliases`
(normalized tokens, whole-word, case-folded) after **query alias expansion**
(Ch I.4.4): a query token that is a historical crosswalk alias expands to its
modern canonical term; expansion adds tokens, it never rewrites status,
identity or evidence class.

Deterministic ranking key, applied in this order:

```
(identity_tier, -structured_hits, -lexical_hits, canonical_id)
```

1. **identity tier** — a query that *is* a canonical id (or `canonical_id`
   filter) ranks that object above every lexical match (exact structured
   identity outranks textual similarity).
2. **structured hits** — count of structured facet values exactly equal to a
   normalized query token (market, status, exposure, layer, family, metric,
   period, id segments).
3. **lexical hits** — distinct query tokens present in the governed text.
4. **canonical id** — final tie-break, so ordering is total and stable.

No randomness, no clock, no dict-order dependence: the same query over the
same generation returns byte-identical result order and result identities.

Embedding rule (frozen schema) is honored by construction: I.4 embeds nothing
and stores no vectors; the record keeps `retrieval_text` as the canonical
embeddable statement for the later authorized bloc.

## 5. Policy before content (Phase 5)

Required sequence, implemented literally in `RetrievalService.retrieve`:

```
principal (II.3 ForgePrincipal)
  -> trusted AuthorizationContext (capability atoms)
  -> resource metadata (RetrievalHeader — safe)
  -> policy decision (II.4 kernel via ForgePolicyEnforcementService)
  -> protected content loading (index body load / port read)   [only if allowed]
  -> retrieval result
```

- Every per-record decision goes through the ratified `guard()` primitive:
  DENY ⇒ the loader is never invoked (asserted with an instrumented loader);
  ALLOW ⇒ invoked exactly once.
- All six exposure classes are exercised: PUBLIC_TEACHING, SUBSCRIBER_MODEL,
  OPERATOR_ONLY, RESEARCH_LAB, INTERNAL_METHOD, INTERNAL_CODE.
- **Unknown or missing exposure fails closed** (`exposure is None` ⇒
  `UNKNOWN_EXPOSURE` deny; an unparseable exposure at compile time ⇒ build
  failure, no publication).
- INTERNAL_METHOD / INTERNAL_CODE bodies are **never indexed**: for internal
  exposures the compiler emits identity-only records with empty
  `retrieval_text` and empty content facets, so no internal body exists to
  release — belt-and-braces on top of the policy matrix.
- **No route is added.** `/forge/v1/*` remains `{health, ready, meta}`;
  `/corpus`, `/objects`, `/retrieval`, `/search` etc. stay 404. I.4 exposes an
  in-process service only.
- Unauthorized text never enters any buffer: denied records produce a
  content-free `DeniedResult` (`object_id`, `exposure`, `reason_code`), and
  snippets/ranking explanations/logs carry no protected body.

## 6. Evidence and provenance (Phase 6)

`RetrievalService.navigate()` answers **FOUND vs SUPPORTED**:

- `found` — the object exists in the current index generation.
- `supported` — the canonical chain resolves to at least one source artifact
  classified independent-empirical by the ratified I.2 `classify_support`
  (visual and conversation-derived sources never count).
- Chain navigation: **Claim → Evidence → Source Artifact** using actual
  reference relations (`supported_by`, `evidence_for`, `belongs_to`,
  `parent`) and actual provenance edges; each hop is policy-guarded before its
  record is loaded, and artifact exposure derives from the linked object's
  exposure.
- A missing link is reported as a `MissingLink` entry with reason
  (`NO_EVIDENCE_REFERENCE`, `NO_SOURCE_ARTIFACT`, `NOT_IN_INDEX`, ...) — never
  reconstructed from similarity, never approximated by a lexical hit.
- Negative evidence is preserved and visible under authorized context:
  `EV.FIB.R11.ANCHOR_OVERGEN.V1` stays FALSIFIED + NEGATIVE_EVIDENCE.
- `FOUND` never implies `SUPPORTED`, and neither implies an answer: results
  carry status/provenance facts only. No numerical claim is asserted by the
  index.

## 7. I.3 limitation handoff (Phase 7)

**A. Reference-order sensitivity.** Frozen I.1 `content_hash()` is
reference-order-sensitive while persistence stores references as an unordered
set (I.3 R4/EVIDENCE gap 2). I.4 therefore computes its own
`normalized_content_hash(record)` — the governed payload with references
sorted by `(target_id, relation, allow_unresolved_historical)` — and uses it
for source fingerprints, staleness and index identity. Frozen I.1 hashing
semantics are NOT changed (no edit to `canonical.py`), reference order is
never treated as proof of distinct identity, and no ontology/migration change
is required, so no GAP/ADR is raised. Cross-store equality (memory vs
PostgreSQL) is proven by test: same corpus ⇒ same `index_hash`.

**B. Governance artifact coverage.** Only the Claim Registry is
artifact-registered (I.3 A1). Every other governance contract
(`ANSWER_CONTRACT_V1.md`, `RETRIEVAL_OBJECT_SCHEMA_V1.md`,
`PRODUCT_EXPOSURE_RULES_V1.md`, `ONTOLOGY_CROSSWALK_V1.md`, taxonomy, card
schemas) is rules-read, not artifact-registered. I.4 therefore:

- compiles **canonical objects only** (object types MODEL/CLAIM/EVIDENCE/
  SETUP/DOCTRINE/TERM/LINEAGE; `ARTIFACT` is refused) — so the Claim Registry
  artifact, being an `ART.*` artifact and not a canonical object, can never
  become a retrieval record;
- never indexes a governance contract as canonical evidence;
- keeps governance contracts separately classified: they are read as rules
  (crosswalk rows become alias *table data*, exposure rules become the policy
  input) and are never presented as indexed canonical evidence.

## 8. Quarantine and source safety (Phase 8)

Counts verified against actual persisted/indexable state by test: 30 canonical
objects, 29 artifacts, 38 edges, 9 quarantined sources, 0 card-file
quarantines.

- Quarantined sources are never canonicalized by I.3, so they are **absent
  from persistence and absent from the index by construction**; the build
  additionally enforces a hard guard: if a record's `DEFINES` source locator
  appears in the quarantine catalog, the record is excluded from the index and
  reported (`quarantined_excluded`).
- Ordinary search NEVER returns quarantine entries. Only an explicit
  `include_quarantine=True` query may surface them, and only after an II.4
  policy decision on `ResourcePolicyMetadata(ARTIFACT, path,
  RESEARCH_LAB)` — research gaps are research material (Product Exposure
  Rules: Research Lab may expose experiments and gaps with explicit status).
  The notice carries **safe metadata only** (`source_path`, `reason`,
  `quarantined: true`) — no body, no snippet, no content identity.
- Leakage guards: `leakage.contains_internal_method` / `contains_code` are
  computed by a scan over the generated text; any offending segment is
  stripped and `max_quote_scope` drops to `NONE`. No INTERNAL_METHOD or
  INTERNAL_CODE body appears in snippets, ranking explanations, logs,
  diagnostics or reports (asserted by test).

## 9. Index build and rebuild (Phase 9)

`run_index_build(gateway, ..., mode)` is an **explicit, controlled operation**
mirroring the I.3 runner law: DRY_RUN compiles and reports with zero publish;
APPLY publishes atomically. Never run on import, on ordinary app startup, or
on a web request (tested). All reads go through the persistence port.

1. **Build from canonical persistence** (port only).
2. **No automatic corpus indexing** on import/startup/request.
3. **Deterministic identity:** `source_fingerprint` = sha256 over sorted
   normalized object hashes + provenance edges + artifact content identities;
   `index_hash` = sha256 over sorted retrieval payloads; `generation` =
   monotonically increasing integer, bumped only when the fingerprint changes.
4. **Idempotent rebuild:** unchanged source ⇒ `UNCHANGED`, existing generation
   kept, `index_hash` identical, zero duplicate entries (records are unique by
   construction and asserted).
5. **Stale detection:** `index.is_stale(gateway)` recomputes the fingerprint
   from the live port and compares; canonical changes (e.g. a status
   transition) make it `True` until the next successful build.
6. **Safe handling of changed objects:** the build report diffs against the
   current generation (`added` / `changed` / `removed` id lists).
7. **Conflict reporting:** duplicate canonical id within one build ⇒
   `IndexBuildError`, nothing published.
8. **Partial-build failure:** compilation/validation happens fully before
   publication; any error leaves the previous generation current (no partial
   index can ever masquerade as complete).
9. **Atomic publication:** the generation object is immutable and swapped in
   by a single reference assignment; readers always observe a whole
   generation.

## 10. Determinism and record identity (Ch I.4.7)

- `RetrievalObject.deterministic_payload()` / `content_hash()` — sorted-key
  JSON over the governed record, reference-order normalized.
- Same canonical version ⇒ same payload/hash, on memory AND PostgreSQL.
- All collections sorted before serialization; no timestamps in identity
  (build time is recorded only in the report, outside identity).
- Query results are stable: `result_id` = canonical id; ordering is total.

## 11. Testing strategy (Phase 10)

Focused suite `tests/test_forge_retrieval.py` maps 1:1 to ACCEPTANCE A–W;
`tests/test_forge_postgres_integration.py` gains an I.4 class proving index
build from a real PostgreSQL 16 store (cross-store `index_hash` equality,
staleness after a real status transition). Regressions: I.1, I.2, II.1–II.4,
I.3 focused suites, persistence, policy, Signal Guard, then the full suite.

## 12. Security review

Threats addressed: entitlement bypass via search, content leak through
snippets/rank/log, exposure confusion, stale-index authority, quarantine
discovery leakage, enumeration of internal objects, provider/credential creep,
route-based corpus dump. Mitigations: header/body split, guard-before-load,
identity-only internal records, quarantine behind RESEARCH_LAB, no routes, no
credentials, no provider imports, bounded audit records (content-free).
