# Book I / Bloc I.4 — Retrieval Index — ACCEPTANCE

> Status: FROZEN GATES
> Date: 2026-10-08
> These clauses are frozen before implementation. I.4 passes ONLY when every
> clause is executable-proven. Clause letters are stable; evidence maps 1:1.

## A. INDEX AUTHORITY

A1. Every retrieval record is compiled from validated canonical persistence
    read through the II.2 `PersistenceGateway` port — never from Markdown,
    never from raw corpus files.
A2. The index never writes to the persistence port and never creates,
    updates, or supersedes a canonical object (index != canonical truth).
A3. Each record preserves canonical ID, type, version, status, exposure,
    source artifact ids, provenance edges, model/setup relationships and its
    index generation.
A4. Only canonical object types are compiled (MODEL, CLAIM, EVIDENCE, SETUP,
    DOCTRINE, TERM, LINEAGE); `ARTIFACT` is refused.
A5. Safe header metadata and protected body are separate structures; policy
    evaluation requires only the header.

## B. FROZEN RETRIEVAL OBJECT CONTRACT

B1. Every record implements the frozen `RETRIEVAL_OBJECT_SCHEMA_V1` fields:
    object_id, object_type, canonical_version, title, market_scope, layer,
    status, exposure_class, parent_ids, source_artifact_ids, retrieval text,
    structured fields, routing metadata, leakage metadata, conflict metadata.
B2. Structured facets are populated ONLY from actual schema fields; an
    unstated facet stays empty/absent and is never fabricated.
B3. `sample_n`, `period`, `metrics`, `clocks`, `events`, `levels`, `states`
    and `implementation_ids` are preserved exactly where the source states
    them, and absent where it does not.
B4. `retrieval_text` is a concise generated statement from governed card
    fields only — no raw artifact body, no metadata dump.
B5. Record identity is deterministic: same canonical state ⇒ same
    `content_hash()` and payload, on every run and every store.

## C. STRUCTURED RETRIEVAL

C1. Exact lookup by canonical id returns exactly one record or reports it
    missing — never a fuzzy/nearest match.
C2. Filters by object type, market, model family, status, exposure, layer,
    source artifact and provenance relation return only exact matches.
C3. `model_family` is derived from the frozen canonical-id grammar, not an
    invented universal field.
C4. Structured lookup runs on header metadata before any body load.
C5. Exact structured identity outranks textual similarity (see E).

## D. CLAIM POPULATION SEPARATION

D1. A `claim_identity` query returns ONLY `compare_claim_identity ==
    SAME_POPULATION` results.
D2. Two claims with different populations and near-identical prose remain
    distinct records with distinct ids; they are never merged.
D3. `ClaimIdentity` (all eight dimensions) is carried verbatim on CLAIM
    records; result/statistic values never enter identity.

## E. TEXT RETRIEVAL AND DETERMINISTIC RANKING

E1. Lexical retrieval matches governed text (title, retrieval text, terms,
    aliases) with normalized whole-word tokens.
E2. Ranking order is exactly `(identity_tier, -structured_hits,
    -lexical_hits, canonical_id)`; a query equal to a canonical id ranks that
    record above every lexical match.
E3. The same query against the same generation returns byte-identical result
    order and result identities, independent of input ordering.
E4. No embedding, vector, or provider call exists anywhere in I.4.
E5. Ranking never changes `status`, `exposure`, `claim_identity`, or
    evidence class of any result (no authority promotion by relevance).

## F. ALIAS / GENERATION ROUTING

F1. Historical aliases map to canonical terms using the frozen Ontology
    Crosswalk rows; the alias table is verbatim equal to the crosswalk
    markdown rows (test-asserted).
F2. Query alias expansion adds canonical terms; it never rewrites status,
    identity, population, or evidence class.
F3. The object's source `generation` is retained in conflict metadata; it is
    never collapsed to a single default when the source states one.
F4. Statistics are never moved across an alias (crosswalk translation rule).

## G. EXPOSURE COMPILER

G1. Every record is stamped with a valid frozen `ProductExposure`.
G2. An unparseable/unknown exposure at compile time fails the build (no
    index publication) — never nearest-class coercion.
G3. INTERNAL_METHOD / INTERNAL_CODE records are indexed identity-only:
    empty `retrieval_text`, empty content facets — no internal body exists
    in the index.
G4. `max_quote_scope` is `NONE` for internal exposure or stripped content,
    otherwise `SYNTHESIS` (never contiguous raw artifact reproduction).

## H. POLICY BEFORE CONTENT

H1. Retrieval executes the frozen sequence: principal → trusted
    authorization context → resource metadata → policy decision → protected
    content load → result.
H2. On DENY the protected loader is never invoked (instrumented loader
    proves 0 calls); on ALLOW exactly once.
H3. A denied record contributes no text, snippet, facet, or ranking
    explanation to the response — only a content-free denial entry
    (object_id, exposure, reason code).
H4. Unauthorized source text never enters any context-building buffer.
H5. Unknown or missing exposure fails closed (`UNKNOWN_EXPOSURE` deny).

## I. EXPOSURE MATRIX

I1. PUBLIC_TEACHING readable by anonymous and every authenticated context.
I2. SUBSCRIBER_MODEL denied to anonymous/auth-no-cap, allowed by
    `corpus.read.member`.
I3. OPERATOR_ONLY requires an operator capability.
I4. RESEARCH_LAB requires a research capability; research content is still
    returned AS research (status unchanged).
I5. INTERNAL_METHOD and INTERNAL_CODE denied to every ordinary capability
    combination; allowed only by `forge.internal`.
I6. All six classes are exercised by tests in both allow and deny directions.

## J. EVIDENCE AND PROVENANCE

J1. Results distinguish `found` (present in index) from `supported` (chain
    reaches an independent-empirical source per ratified I.2
    `classify_support`).
J2. Claim → Evidence → Source Artifact navigation works where the canonical
    data supports it, returning artifact id, locator, content identity,
    source state and relation.
J3. Each navigation hop is policy-guarded before its record is loaded.
J4. Missing links are reported as missing with a reason code and are never
    reconstructed from similarity.
J5. A lexical match alone never marks an object supported or true.

## K. NEGATIVE EVIDENCE

K1. `EV.FIB.R11.ANCHOR_OVERGEN.V1` is retrievable as FALSIFIED with
    `NEGATIVE_EVIDENCE` type under authorized (research) context.
K2. Negative evidence is never hidden, upgraded, or reworded into positive
    support.

## L. QUARANTINE

L1. Persisted/indexable counts match I.3 truth: 30 objects, 29 artifacts,
    38 edges, 9 quarantined sources, 0 card-file quarantines.
L2. Quarantined sources never appear as ordinary search results.
L3. If a record's `DEFINES` source locator is in the quarantine catalog, the
    record is excluded from the build and reported (fail closed).
L4. Explicit quarantine discovery requires an II.4 decision (RESEARCH_LAB)
    and returns safe metadata only: path, reason, quarantine flag — no body,
    no snippet.

## M. INDEX BUILD AND REBUILD

M1. `run_index_build` is explicit (DRY_RUN / APPLY) and never executes on
    import, on ordinary application startup, or on a web request.
M2. Build reads only through the persistence port.
M3. DRY_RUN publishes nothing.
M4. APPLY publishes atomically: readers observe either the previous complete
    generation or the new complete generation, never a partial index.
M5. Rebuild is idempotent: unchanged source ⇒ same `index_hash`, generation
    not bumped, zero duplicate entries.
M6. Deterministic versioning: `generation` increments only on source change;
    `source_fingerprint` and `index_hash` are reproducible.

## N. FRESHNESS, CHANGES, CONFLICTS, FAILURE

N1. `is_stale(gateway)` is False after a build and True after any canonical
    change (e.g. status transition) until the next build.
N2. A changed canonical object produces a `changed` entry in the build
    report and a new generation; added/removed ids are reported too.
N3. A duplicate canonical id inside one build raises a conflict error and
    publishes nothing.
N4. A failure part-way through a build leaves the previous generation
    current and reports the failure — no partial index is ever readable.

## O. REFERENCE-ORDER NORMALIZATION (I.3 limitation A)

O1. Index identity uses a normalized (reference-set) payload hash; reference
    order is never treated as distinct canonical identity.
O2. Two records differing only in reference order produce the SAME
    normalized hash, same fingerprint contribution, and same `index_hash`.
O3. Frozen I.1 `content_hash()` semantics are unchanged (no edit to the
    I.1 kernel); no ontology or migration change is introduced, hence no
    GAP/ADR is required.
O4. Memory-built and PostgreSQL-built indexes over the same corpus produce
    the same `index_hash`.

## P. GOVERNANCE COVERAGE (I.3 limitation B)

P1. Governance contracts other than the Claim Registry are not indexed as
    canonical evidence.
P2. The Claim Registry artifact (`ART.*`) is never a retrieval record.
P3. Governance contracts are separately classified (rules-read) and may
    appear only as alias table data or policy input, never as evidence.

## Q. MODEL-TRUTH REGRESSIONS

Q1. EUR: Daily / Weekly / Higher Order remain three distinct families;
    no cross-family result bleed under family or market filters.
Q2. XAU: L1 / L2 / L3 remain distinct — layer filters return disjoint sets
    and the Game model is never collapsed into one layer.
Q3. BTC: no fabricated BTC Game object exists in the index; the BTC Tracker
    family keeps its honest no-evidence gap (`requires_evidence_card`
    false / unsupported).
Q4. JPY: role asymmetry preserved — the basket relation claim keeps
    `USDJPY,AUDJPY,EURJPY` identity and confirmation/veto wording is not
    rewritten into equal-weight language.
Q5. ST manual/automation distinction preserved: `MANUAL_OPERATOR` and
    `RESEARCH_ONLY` execution classes survive; no `AUTOMATION_APPROVED` is
    created; parity/manual-automation metadata is retained.
Q6. P90 remains lineage/activation vocabulary — never a performance
    statistic, never conflated with ST.
Q7. Fib Range Birth doctrine is not reduced to coordinates; R11 negative
    evidence survives (see K).

## R. INTERNAL MATERIAL

R1. No INTERNAL_METHOD/INTERNAL_CODE body appears in any record, response,
    snippet, ranking explanation, log line, report or diagnostic.
R2. The II.4 policy module is untouched by I.4; no bypass, no second policy
    authority, no scattered exposure `if` outside the kernel.

## S. BOUNDARY INTEGRITY

S1. No route is added: FORGE routes remain exactly
    `{/forge/v1/health, /forge/v1/ready, /forge/v1/meta}`; `/retrieval`,
    `/search`, `/objects`, `/corpus`, `/query` all 404.
S2. No OpenRouter, embedding provider, Whop, license, entitlement, plan, or
    commercial object is created; no provider seam is opened.
S3. No new third-party dependency and no new migration
    (`discover_migrations() == [1, 2]`, 001 SHA pin unchanged).
S4. No I.5 QA, Ask CEREBUS, or public corpus API behavior exists.

## T. REPRODUCIBILITY

T1. Two builds over the same state produce identical `source_fingerprint`,
    `index_hash`, record hashes and report counts.
T2. No timestamp, hostname, random value or dict-iteration artifact enters
    record identity or result ordering.

## U. POSTGRESQL / CI

U1. The index builds from a real PostgreSQL store and yields the same
    `index_hash` as the memory build over the same corpus.
U2. Staleness is observed after a real PostgreSQL status transition, and
    cleared by a rebuild.
U3. CI `test` and `postgres` jobs are green on the final head.

## V. SECURITY

V1. Deny-before-load is proven for search and navigation with an
    instrumented loader (zero loads on deny).
V2. No protected snippet appears in any denial path.
V3. Quarantine discovery and internal exposure both fail closed when
    unauthorized.
V4. No credential, DSN, token, or provider id appears in code, tests,
    reports or logs introduced by I.4.

## W. REGRESSION

W1. I.1, I.2, II.1, II.2, II.3, II.4, I.3 focused suites, persistence, policy
    and Signal Guard tests are green; no existing test is weakened or
    deleted.
W2. The full repository suite is green with no new failures.
