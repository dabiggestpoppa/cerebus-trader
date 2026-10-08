# Book I / Bloc I.3 — Canonical Backfill

## RATIFICATION

**Book I / Bloc I.3 — Canonical Backfill
CLOSED — PASS**

Ratified: 2026-10-08
Final local HEAD at ratification: `e42827f412cd43f6e376aa2cd5df6b1dda2097c2`
(ladder from `ebda556`, append-only: `314f815` → `8066759` → `7c080eb` →
`1ae9a46` → `e42827f`; the ratification commit follows this file)

## Explicit ratification statements

1. **Migration is representation change, never epistemic promotion.** All 15
   distinct legacy status strings map through the explicit frozen table with
   zero promotions (0 record mismatches): `CANONICAL_FROZEN_FAMILY` demotes to
   DESCRIPTIVE, `NEGATIVE_EVIDENCE` maps to FALSIFIED with
   `evidence_type=NEGATIVE_EVIDENCE` preserved, small-N/research/relationship
   qualifiers survive as metadata. No unknown value was nearest-enum coerced;
   unknown values quarantine.

2. **The two discovered gateway defects are repaired and proven on both
   gateways.** (A) Mutually referencing CLAIM ↔ EVIDENCE objects now commit as
   one unit via whole-batch validation, while a batch whose ordinary references
   never resolve still rolls back — the post-commit store never contains
   dangling truth. (B) Two pending records with the same canonical id raise
   `DuplicateCanonicalObject` and roll back atomically; the second record can
   never silently replace the first. Committed-duplicate and stale-write
   protections are preserved. Proven in memory AND on real PostgreSQL 16.15
   (constraint-level), plus the poisoned-plan rollback through the runner.

3. **Two further defects found during recovery are repaired.** (R3) The SQL
   claim-identity serializer silently stored `{}` (missing
   `comparison_key_dict()`) and the read path crashed with `KeyError: 'market'`
   — exposed by the new full-corpus PG apply; all eight identity dimensions are
   now persisted, and an empty legacy dict reads as *absent* identity, never
   fabricated. (R4) The governed-content comparison now compares reference
   *sets* (the frozen schema's PK is `canonical_id + target_id + relation`; no
   migration may be added), so authored reference order is no longer false
   conflict material.

4. **Acceptance gaps A1/I1 found by the Phase 3 audit are repaired.** The
   claim registry is inventoried as a `GOVERNANCE_CONTRACT` source artifact
   with a `sha256:` identity and emits 10 `DEFINES` edges — every one of the 30
   migrated objects now carries ≥1 provenance edge; a missing registry
   classifies `MISSING_SOURCE` and is never fabricated.

5. **The interrupted session's earlier report was wrong and is corrected on
   the record.** Actual truth: 20 card files + 10 registry claims = 30 migrated
   objects; **9 quarantined sources** (7 Pine indicators + 1 research ledger +
   1 conversation-derived document), all non-card and all listed with reasons;
   zero *card-file* quarantines. Zero overall quarantine was false. The
   conversation-derived doctrine is never canonicalized; visual sources carry
   only `VISUALIZES` edges and never establish empirical support.

6. **Numerical claims keep their evidence paths.** All 10 registry claims
   resolve CLAIM → EVIDENCE → source artifact with mutual back-references and
   `claim_identity`; 0 unsupported numerical claims; the governed
   `REGISTRY_CLAIMS` table is asserted row-for-row against
   `CLAIM_REGISTRY_V1.md`. BTC Game is not fabricated and the BTC Tracker
   family carries no invented evidence or statistics.

7. **Frozen family distinctions hold.** ST parity/separation doctrine preserved
   on the EUR daily card; P90 present as lineage, never conflated with ST and
   never as a performance statistic; BTC Tracker ≠ BTC Game; EUR families
   separate; XAU L1/L2/L3 distinct; JPY role asymmetry intact (model + gated
   setup + basket evidence); Fib R11 negative evidence survives as FALSIFIED.

8. **Boundary integrity.** No migration added (`discover_migrations() == [1,
   2]`, 001 SHA pin unchanged); no route added; `app/forge/policy.py` untouched;
   no entitlement/plan/license/Whop object; PUBLIC_TEACHING never assigned by
   default; no INTERNAL body in any report or log; no Signal Guard file changed;
   the corpus tree is unmodified.

## Acceptance verification

All ACCEPTANCE.md clauses A–X are satisfied and executable-proven (EVIDENCE.md
clause-mapping table). Exact results at the head above:

- I.3 focused suite: **72 passed** (28 + 44).
- Focused regression gate: I.1 41, I.2 41, II.2 56, II.3 66, II.4 86.
- Signal Guard: **64 passed**, files unchanged.
- Full repository suite: **446 passed, 18 skipped, 0 failed** (baseline at
  `ebda556` was 369/14; the 4 new skips are the new PG tests without
  `FORGE_TEST_DATABASE_URL`).
- PostgreSQL integration on a real server: **18 passed** (fresh database,
  CI semantics) including the full-corpus APPLY with per-object roundtrip
  assertions and an idempotent second apply (`unchanged=30`, 0 conflicts).
- Persistence proof harness: **ALL 7 STEPS PASSED**; corpus audit harness exit
  0 with stable content hash
  `7b9f98041fabbc5f78d35cfdcaa5d1b986b192f7ab5a2258a16db729545f96e0`.
- Corpus: 30 inventoried / 29 artifacts / 38 edges / 30 migrated (7 models,
  10 evidence, 3 setups, 10 claims) / 9 truthful quarantines / 0 missing
  sources / 0 unresolved references / 0 unsupported numerical claims.

Known limitations carried forward are recorded in EVIDENCE.md: (i) governance
contracts other than the claim registry are rules-read but not
artifact-registered (A1 satisfied; PLAN prose deviation disclosed); (ii) the
frozen I.1 domain `content_hash()` remains reference-order-sensitive while
persistence stores references as a set — I.4 must not treat reference order as
identity; (iii) the PG integration suite requires a fresh database per run (CI
provides one); (iv) push-triggered CI (`forge-tests.yml`) runs after this
ratification — local equivalents (full suite + PG job shape) executed green.

## Handoffs

- **I.4 Retrieval Index:** authorized to proceed. Retrieval reads must go
  through the enforcement boundary (policy before load), treat provenance edges
  and reference sets as governed truth, compare multi-reference objects via
  normalized payload rather than raw reference order, and never re-derive
  epistemic status from status-qualifier metadata.
- **Book II / II.3 authentication and Book VI entitlement** remain exactly
  where they are; I.3 created no identity, session, route, or commercial
  object.
