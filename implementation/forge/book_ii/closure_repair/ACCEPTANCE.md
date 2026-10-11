# BOOK II — CLOSURE REPAIR ACCEPTANCE

Status: ACCEPTANCE — committed BEFORE implementation (ladder rung 1, with PLAN)
Start SHA: `eea25a35f15fea70df1b768d1e1a7c6db05d337f`
Every clause below is executable. “PASS” for this packet means: all clauses
green on their stated environment, governance records committed, no frozen
file modified. It is NOT Book II ratification.

## A. Migration & schema (G-D1, Persistence domains)

- **A1** `discover_migrations()` returns exactly `[1, 2, 3]` with identities
  `001_initial_schema`, `002_identity_session`, `003_vector_projection`.
- **A2** On empty Postgres+pgvector: applying migrations records `[1,2,3]`,
  `check_compatibility() == "OK"`, re-apply is `CURRENT`.
- **A3** `CREATE EXTENSION vector` succeeded; `retrieval_vectors` exists
  with PK/FKs, `CHECK (vector_dims(embedding) = embedding_dim)`, and the
  frozen Ch II.2.4 column set present.
- **A4** Migration SQL contains no statements touching 001/002 objects
  (forward-only, additive; no DROP/ALTER of existing tables).

## B. Storage contract & canonical cross-checks (Ch II.2.4)

- **B1** A well-formed `VectorProjectionRecord` round-trips through the
  gateway with every frozen field preserved (id/version, payload, semantic
  text, vector values, model/version, exposure, canonical hash, owner,
  generated-at stamped by the store).
- **B2** Validation rejects, with `InvalidRecord` and **nothing written**:
  dimension mismatch (`len != embedding_dim`), dim ≤ 0 or > 16000,
  non-finite vector values, empty model or version, non-64-hex canonical
  hash, exposure outside the frozen `ProductExposure` vocabulary.
- **B3** Canonical cross-check rejects when the referenced canonical row is
  absent (FK/lookup), or record `object_version` / `exposure_class` /
  `canonical_hash` differs from the canonical row’s `version` / `exposure` /
  `content_hash` — a projection cannot re-label canonical truth.
- **B4** Provider/model identity stability: writing a second projection for
  the same `object_id` with a different `embedding_model`/`embedding_version`
  replaces attributes, keeps the same PK identity, leaves row count == 1.

## C. Rebuild (G-D4, Acceptance II.2)

- **C1** `rebuild_vector_projection(source)` from authorized source records
  is deterministic: two consecutive rebuilds yield identical fingerprint
  sets (all fields except `generated_at`).
- **C2** Independence: deleting ALL projection rows leaves canonical rows,
  references, edges and audit content byte-identical; a subsequent rebuild
  fully restores the projection (counts + fingerprints equal).
- **C3** Stale removal: rows not present in the source set are removed by
  rebuild; rows present are upserted (replacement, not duplication).
- **C4** Corruption recovery: an overwritten/corrupted projection row is
  restored to the source fingerprint by rebuild; canonical truth unchanged.
- **C5** Audit survival: recorded audit-trail entries (II.6
  `BoundedAuditTrail`) are unchanged by projection wipe/rebuild operations.

## D. Isolation & leakage (G-P3 vector sub-clause, Phase 2 boundaries)

- **D1** Deny-before-content-load: with `allowed_exposures` not containing
  the row’s exposure, `get_vector_projection` returns `None` — identical to
  a nonexistent id (no existence oracle), and no payload/text/vector data is
  ever returned for the denied row.
- **D2** Tenant isolation: a row with `owner_user_id = A` is invisible to
  `tenant=B` and to unscoped/anonymous access; shared rows (`owner NULL`)
  are visible only when the exposure allow-set also passes.
- **D3** Empty `allowed_exposures` fails closed (None / empty tuple) without
  issuing a content query.
- **D4** `search_vectors` filters exposure and tenant **in the SQL WHERE
  clause**: rows failing either filter are absent from the result and their
  content columns are never selected; results are cosine-distance ordered
  and deterministic (ties broken by object_id).
- **D5** Zero cross-tenant / cross-exposure leakage: adversarial matrix over
  {exposed × tenant-owned × shared} × {allowed, denied} returns exactly the
  authorized rows — asserted as row-id sets on both gateways, re-proven on
  PostgreSQL.
- **D6** Similarity never grants authority: search output is candidate rows
  only; no entitlement/policy decision is made or bypassed inside the
  persistence layer (structural: persistence imports no policy decision
  symbols; asserted by import-scope check).

## E. Backup/restore smoke (G-D5)

- **E1** `pg_dump` (custom format) of the live test database succeeds;
  credentials never appear in argv, stdout, stderr or evidence text.
- **E2** `pg_restore` into a fresh empty database completes; verification
  runs **against the restored database only**.
- **E3** Restored DB: all tables present; per-table counts equal source
  pre-dump counts; canonical `content_hash` multiset equal; migration head
  == code head `[1,2,3]`; vector rows and dimensions preserved;
  canonical↔projection hash reconciliation holds.
- **E4** Re-applying migrations on the restored DB is a no-op (`CURRENT`);
  source DB counts unchanged after the round trip (dump did not mutate).
- **E5** The smoke executes where pgvector exists (CI postgres job);
  locally it skips with an explicit reason (no CREATEDB / no pgvector) —
  recorded as an infrastructure gap, never as a pass.

## F. Governance records (Phase 1)

- **G1** `GOVERNANCE.md` records the GAP_ADR_001 operator interpretation
  verbatim with its authorization consequence (Book II closure precedes
  Book III; frozen plans unchanged).
- **G2** `GOVERNANCE.md` records the GAP-05 ownership interpretation with a
  clause-by-clause verification against frozen contracts, and states the
  honest consequence: durable audit/event-ledger implementation remains
  absent (reclassified on the register, never silently closed).
- **G3** All 23 manifest-pinned frozen files remain content-identical
  (re-verified after every rung); no prior packet file is edited.

## G. Preservation & exclusions

- **G1x** Full existing suite passes unchanged except the five migration-pin
  tests extended `[1,2]` → `[1,2,3]` (authorized schema extension; pins stay
  exact — nothing weakened, no test removed, no skip added to existing
  tests).
- **G2x** No new HTTP routes; route-inventory tests unchanged and green.
- **G3x** No embedding generation/model-selection/reranking code anywhere
  (`grep`/AST evidence in EVIDENCE); tests use deterministic synthetic
  vectors only.
- **G4x** No Book III/IV/VI/VII surface, no policy/identity semantics
  changes, no credentials/private data in any evidence file.

## Environments

- Local (this machine): non-PG suites + contract/memory tests + governance
  checks. Local PostgreSQL 16.15 cannot apply `003` (no pgvector package) →
  recorded infra gap; not substituted by any non-pgvector proof.
- CI `postgres` job (`pgvector/pgvector:pg16`): A2–A3, B–D PostgreSQL
  re-proofs, E smoke, migration chain, full regression — the acceptance
  environment for G-D1/G-D4/G-D5/G-P3.
