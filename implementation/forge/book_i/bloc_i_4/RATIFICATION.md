# Book I / Bloc I.4 — Retrieval Index

## RATIFICATION

**Book I / Bloc I.4 — Retrieval Index
CLOSED — PASS**

Ratified: 2026-10-08
Final local HEAD at ratification: `eaf0e5a`
(ladder from `05c74a1`, append-only: `6a5d648` → `081fe78` → `b940732` →
`2b5f0db` → `1738f04` → `eaf0e5a`; the ratification commit follows this file)

## Explicit ratification statements

1. **Retrieval relevance is not evidence authority.** The index is a finding
   surface over governed canonical truth: it reads exclusively through the
   II.2 persistence port, never writes to it, never creates or supersedes a
   canonical object, and never changes `status`, `exposure`, `claim_identity`
   or evidence class of any result. Ranking is exactly
   `(identity_tier, -structured_hits, -lexical_hits, canonical_id)` — total,
   deterministic, clock-free; a query equal to a canonical id outranks every
   lexical match, and an unrecognized filter matches nothing (fail closed).

2. **Policy before content is enforced literally.** The frozen sequence —
   principal → trusted authorization context → header metadata → II.4 decision
   → guarded body load → result — runs through the ratified
   `ForgePolicyEnforcementService`. An instrumented loader proves **0 calls on
   DENY and exactly 1 per ALLOWED record**, for both search and provenance
   navigation. Denials are content-free by structure: exactly
   `{object_id, exposure, reason_code}`; unauthorized text never reaches any
   response, snippet, ranking explanation, audit line or citation.

3. **Exact indexed state, reproducible.** 30 records (10 CLAIM, 10 EVIDENCE,
   7 MODEL, 3 SETUP), 29 artifacts, 38 provenance edges, 9 quarantined
   non-card sources, 0 card-file quarantines;
   `source_fingerprint=9675431033dd1fa667e3ef3d7ea65526c7bf5a545bf073875af11496236fa226`,
   `index_hash=e23cfeb4576a6a534a39d4a336bda09b4972baa8ef9097c158fdc4cf5225d173`,
   generation 1. Rebuild is `UNCHANGED` with identical hashes; two independent
   builds are byte-identical; no timestamp, hostname, randomness or
   dict-order enters identity or ordering. The committed 95-check evidence
   harness reproduces every number.

4. **Index-generation metadata never changes record identity.** Identity is
   the normalized (reference-set) payload hash with top-level `generation`
   excluded; a record recompiled into generation 2 keeps its exact
   `content_hash` — proven by the regression test added at `eaf0e5a`
   (focused suite 123 → 124; no existing test weakened or removed). The
   source generation in conflict metadata is retained as content (F3).

5. **Header/body separation keeps protected content unloaded.** Policy needs
   only the safe header; INTERNAL_METHOD/INTERNAL_CODE records are compiled
   identity-only (empty text, empty content facets, `max_quote_scope=NONE`)
   so no internal body exists in the index; unknown or missing exposure fails
   closed at compile (build failure) and at release (`UNKNOWN_EXPOSURE`).

6. **Claim populations never merge; evidence chains are navigable and
   honest.** All 10 registry claims resolve `Claim → Evidence → Source
   Artifact` under research context (**found 10/10, supported 10/10**, zero
   missing links); missing links are reported with reason codes, never
   reconstructed from similarity; FOUND never implies SUPPORTED.
   `EV.FIB.R11.ANCHOR_OVERGEN.V1` remains FALSIFIED +
   NEGATIVE_EVIDENCE, research-gated, never reworded as support.

7. **Exposure matrix holds in both directions for all six classes.**
   Real corpus: SUBSCRIBER_MODEL 24 / RESEARCH_LAB 4 / OPERATOR_ONLY 2;
   anonymous sees 0 results with 30 content-free denials; member reads only
   SUBSCRIBER; operator/research contexts admit their classes; research
   authorization never rewrites research status; `forge.internal` alone
   admits only the internal classes. PUBLIC_TEACHING is never assigned by
   default; the synthetic 12-row matrix exercises all six classes allow+deny.

8. **Quarantine is truthful, excluded, and gated.** The 9 quarantined
   sources are absent from the index by construction and asserted disjoint
   from record ids; ordinary search never surfaces them; explicit discovery
   requires an II.4 RESEARCH_LAB decision and returns safe metadata only
   (path, reason, flag); a record whose `DEFINES` locator is quarantined is
   excluded and reported.

9. **Governance coverage (I.3 limitation B) is respected structurally.**
   Only canonical object types compile — `ART.*` is refused, so the Claim
   Registry artifact can never become a record; governance contracts are
   rules-read (crosswalk rows as alias table data, exposure rules as policy
   input) and never indexed as evidence; alias expansion never rewrites
   status, identity, population or evidence class, and no statistic moves
   across an alias.

10. **Model truth preserved (Q1–Q7).** EUR Daily/Weekly/Higher-Order stay
    separate families; XAU L1/L2/L3 stay disjoint with the Game model
    uncollapsed; no BTC Game object exists and the BTC Tracker keeps its
    honest unsupported gap; JPY basket role asymmetry and
    `USDJPY,AUDJPY,EURJPY` identity intact; MANUAL_OPERATOR/RESEARCH_ONLY
    survive with no AUTOMATION_APPROVED created; P90 stays lineage
    vocabulary; Fib Range Birth is not reduced to coordinates.

11. **Boundary integrity.** No route added (`/forge/v1/*` remains
    `{health, ready, meta}`; corpus/retrieval/search endpoints 404); no
    new migration (`discover_migrations() == [1, 2]`, 001 SHA pin
    unchanged); no new dependency; no embedding/vector/provider surface;
    no OpenRouter/Whop/license/entitlement/plan object; no credential, DSN
    or token in code, tests, reports or logs; `app/forge/policy.py`
    byte-unchanged (pinned SHA-256
    `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`);
    Signal Guard files unchanged; no I.5 QA, Ask CEREBUS or public corpus
    API behavior exists.

## Acceptance verification

All ACCEPTANCE.md clauses A–W are satisfied and executable-proven
(EVIDENCE.md clause-mapping table, 87 cited test names verified present).
Exact results at the head above:

- I.4 focused suite: **124 passed** (123 at `1738f04` + the
  generation-identity law test added in the evidence rung).
- Prior FORGE regression gates: I.1 **41**, I.2 **41**, II.2 **56**,
  II.3 **66**, II.4 **86**, I.3 **72**, service composition **36** (batch:
  398 passed).
- Signal Guard: **64 passed**, files unchanged.
- Full repository suite: **570 passed, 19 skipped, 0 failed** (the 19 skips
  are exactly the PG integration tests without `FORGE_TEST_DATABASE_URL`).
- PostgreSQL integration on a real 16.15 server: **19 passed**, run three
  consecutive times CI-style → **19 / 19 / 19** (no rerun-state residue).
- CI-shaped full suite with live PostgreSQL: **589 passed, 0 skipped**.
- Evidence harness (`tools/index_evidence.py`): exit 0, **95/95 checks**.
- Cross-store: PG-built and memory-built indexes over identical governed
  state yield the same `index_hash`; staleness observed after a real PG
  status transition and cleared by rebuild (generation 2).

Known limitations carried forward and recorded in EVIDENCE.md: (i) the
Windows CRLF raw-byte SHA pin on `001_initial_schema.sql` fails on a fresh
`core.autocrlf=true` checkout until the file is LF-normalized — Linux CI
unaffected; the frozen migration contract was deliberately not changed;
(ii) governance contracts other than the claim registry remain rules-read,
not artifact-registered; (iii) lexical retrieval only — embeddings belong
to Book VII `VII.5`; (iv) the real corpus contains no PUBLIC_TEACHING or
INTERNAL_* rows, so those classes are exercised on synthetic fixtures;
(v) the 9 quarantined sources stay quarantined; (vi) frozen I.1 domain
`content_hash()` remains reference-order-sensitive outside the index.

## Handoffs

- **Book I / Bloc I.5 QA & Answer Contract:** authorized to proceed. I.5
  must consume retrieval only through `RetrievalService` (policy before
  load), treat index results as findings and never as authority, keep
  numerical answers anchored to claim/evidence chains rather than lexical
  hits, and preserve the exposure matrix and denial semantics unchanged.
- **Book II / II.3 authentication and Book VI entitlement** remain exactly
  where they are; I.4 created no identity, session, route, provider or
  commercial object.

## Post-ratification verification

_(recorded after push — CI results appended in the verification rung that
follows this file)_
