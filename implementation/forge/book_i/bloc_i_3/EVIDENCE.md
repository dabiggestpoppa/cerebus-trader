# Book I / Bloc I.3 — Canonical Backfill — EVIDENCE

## Planning identity

- Branch `forge`, starting ratified head `ebda556694a14ee72e869d8f45d6dc819b187592`
  (II.4 CLOSED — PASS).
- PLAN + ACCEPTANCE: `314f815` — frozen A–X gates.
- Implementation package: `8066759` — mapping registry, card parser,
  canonicalizer, DRY_RUN/APPLY runner, memory-gateway batch-reference fidelity.
- This document records the **interrupted-build recovery**: state recovered from
  the local tree after the connection interruption (Phase 0), the two persistence
  gateway defects completed and tested, the lost test module reconstructed from
  its bytecode, and the real-corpus audit executed (Phases 1–6). No history was
  reset, amended, rebased, squashed, or force-pushed.

## Commit ladder (I.3, append-only)

| Rung | SHA | Content |
|------|-----|---------|
| start | `ebda556` | II.4 ratification (ratified head) |
| 1 | `314f815` | I.3 PLAN + ACCEPTANCE (frozen A–X gates) |
| 2 | `8066759` | I.3 backfill package (registry, parser, canonicalizer, runner) |
| 3 | `7c080eb` | I.3 repairs: batch unit validation, in-batch dup rejection, claim-identity SQL serializer, reference-set comparison, registry inventory (A1/I1) |
| 4 | `1ae9a46` | I.3 tests: focused suites (28 + 44), persistence regressions, PG integration incl. full-corpus apply |
| 5 | (this file) | I.3 evidence + audit/proof harnesses |
| 6 | (follows) | I.3 ratification — final head recorded there |

`git status` at evidence time: only forge-scope files modified
(`app/forge/backfill/*`, `app/forge/persistence/*`, `tests/test_forge_*`,
`implementation/forge/book_i/bloc_i_3/*`). No Signal Guard file, no policy file,
no corpus source file, no route file changed.

## Runtime environment

- Python 3.11.9, SQLAlchemy 2.0.49, psycopg2 2.9.12 (local Windows runner).
- PostgreSQL 16.15 local, role `forge`, database `forge_test` (mirrors CI's
  `postgres:16` service exactly, including `FORGE_TEST_DATABASE_URL` shape).
- CI: `.github/workflows/forge-tests.yml` — `test` job (`python -m pytest -q`)
  and `postgres` job (fresh `postgres:16` service per run).

## Commands executed and exact results

1. **Real-corpus DRY RUN** (read-only CLI):

   ```
   python -m app.forge.backfill.runner dry-run .
   ```

   Report counters (exact): `sources_inventoried=30, artifacts=29,
   provenance_edges=38, migrated=30 (models=7, evidence=10, setups=3,
   claims=10), ready=10, mapped=10, quarantined=9, missing_source=0,
   unresolved_reference=0, unsupported_numerical_claim=0, negative_evidence=1,
   visual_only_sources=4, conversation_derived_sources=1, conflicts=0,
   unchanged=0`; content hash
   `7b9f98041fabbc5f78d35cfdcaa5d1b986b192f7ab5a2258a16db729545f96e0`.

2. **Corpus audit harness**
   (`implementation/forge/book_i/bloc_i_3/tools/corpus_audit.py`, exit 0):

   ```
   PYTHONPATH=. python implementation/forge/book_i/bloc_i_3/tools/corpus_audit.py
   ```

   Inventory, BEFORE/AFTER parse compatibility, ID/status mapping tables,
   quarantine, provenance coverage, claim adequacy, frozen family distinctions,
   faithful representation — all PASS (details below).

3. **Persistence proof harness**
   (`implementation/forge/book_i/bloc_i_3/tools/persistence_proof.py`, exit 0):

   ```
   PYTHONPATH=. python implementation/forge/book_i/bloc_i_3/tools/persistence_proof.py
   ```

   Output: `ALL 7 PERSISTENCE PROOF STEPS PASSED` (details in Persistence proof).

4. **Focused regression gate** (each exit 0):

   | Gate | Command target | Result |
   |------|----------------|--------|
   | I.1 canonical + schemas | `tests/test_forge_canonical.py tests/test_forge_schemas.py` | 41 passed |
   | I.2 provenance | `tests/test_forge_provenance.py` | 41 passed |
   | II.2 persistence | `tests/test_forge_persistence.py` | 56 passed |
   | II.3 identity | `tests/test_forge_identity.py` | 66 passed |
   | II.4 policy | `tests/test_forge_policy.py` | 86 passed |
   | I.3 focused suite | `tests/test_forge_backfill.py tests/test_forge_backfill_more.py` | 72 passed (28 + 44) |
   | Signal Guard | `test_duplicate_signal.py + test_ghost_signal.py + test_forge_service_composition.py + test_vision_confirm.py + test_vision_mcp.py` | 64 passed |

5. **Full repository suite**: `python -m pytest -q`
   → **446 passed, 18 skipped, 0 failed, 0 errors** (464 collected, 7.7s).
   Baseline at `ebda556` was **369 passed, 14 skipped**; delta = +72 new I.3
   focused tests, +5 persistence regressions (2 mutual/dup batch + leak, 2 SQL
   claim-identity roundtrip), +4 new PG integration tests (the 4 added skips are
   exactly those PG tests when `FORGE_TEST_DATABASE_URL` is unset).

6. **PostgreSQL integration, real server** (fresh DB per run, CI semantics):

   ```
   FORGE_TEST_DATABASE_URL="postgresql+psycopg2://forge:...@localhost:5432/forge_test" \
     python -m pytest -q tests/test_forge_postgres_integration.py
   ```

   → **18 passed** on PostgreSQL 16.15, including the full-corpus APPLY and
   idempotent second apply through the SQL gateway. No PostgreSQL claim is made
   without this run.

## Corpus audit — exact counts (Phase 3)

### Inventory (deterministic frozen globs)

- Corpus files on disk: 96; in-scope loaded: **30**
  = 20 cards (7 model + 10 evidence + 3 setup) + 1 conversation-derived
  + 8 named artifacts (7 `.pine` + 1 research ledger, each with a frozen
  typed edge) + 1 claim registry.
- Every in-scope source appears exactly once in the report (A1).
- Claim registry classified `GOVERNANCE_CONTRACT` (inventoried, artifact- +
  edge-registered, never canonicalized into a domain object).

### BEFORE / AFTER parse compatibility

- BEFORE: `parse_card` on all 20 card files → 20/20 parsed, 0 exceptions
  (10 `EVIDENCE CARD`, 7 `MODEL CARD`, 3 `SETUP CARD`).
- The 9 non-card in-scope files are never misdetected as cards (0/9).
- AFTER: 30 outcomes = 10 `READY` + 10 `MAPPING_REQUIRED` + 9 `QUARANTINED`
  + 1 `GOVERNANCE_CONTRACT`. 0 card files quarantined.

### Legacy ID mappings (explicit registry, no fuzzy matching)

10 explicit entries, 20 passthrough (`EV.*`/`CL.*` after `CanonicalId.parse`),
0 canonical ids reachable from two legacy ids:

```
BTC.TRACKER.DWM.V1            -> MOD.BTC.TRACKER.DWM.V1
CROSSASSET.FIB.RANGE_BIRTH.V1 -> MOD.CROSSASSET.FIB.RANGE_BIRTH.V1
EUR.DAILY.NEWS_REKEY.V1       -> MOD.EUR.DAILY.NEWS_REKEY.V1
EUR.HIGHER_ORDER.V1           -> MOD.EUR.HIGHER_ORDER.V1
EUR.WEEKLY.V1_1               -> MOD.EUR.WEEKLY.V1_1
JPY.CARRY_GAME.L1_L3.V1       -> MOD.JPY.CARRY_GAME.L1_L3.V1
SETUP.FIB.REKEY.V1            -> SET.FIB.REKEY.V1
SETUP.JPY.CARRY_ROLE_GATE.V1  -> SET.JPY.CARRY_ROLE_GATE.V1
SETUP.XAU.QUARTER_ZONE.V1     -> SET.XAU.QUARTER_ZONE.V1
XAU.GAME.L1_L2_L3.V1          -> MOD.XAU.GAME.L1_L2_L3.V1
```

### Legacy status mappings (15 distinct raw strings, 0 ambiguous, 0 promotions)

```
ACTIVE_RESEARCH_IMPLEMENTED     -> RESEARCH_FLAG
CANDIDATE                       -> CANDIDATE
CANONICALIZATION_CANDIDATE      -> CANDIDATE
CANONICAL_FROZEN_FAMILY         -> DESCRIPTIVE        (demotion, frozen_family)
CORE_CANDIDATE                  -> CANDIDATE
FORWARD_OOS                     -> FORWARD_OOS
MODERN_RESEARCH_FRAMEWORK       -> RESEARCH_FLAG
NEGATIVE_EVIDENCE               -> FALSIFIED          (type stays NEGATIVE_EVIDENCE)
RESEARCH_FLAG_SMALL_N           -> RESEARCH_FLAG
RESEARCH_OPERATOR_CANDIDATE     -> RESEARCH_FLAG
SCIENTIFIC_CORE_CANDIDATE       -> CANDIDATE
VALIDATED                       -> VALIDATED
VALIDATED_RELATIONSHIP          -> VALIDATED          (+ relationship metadata)
VALIDATED_RESEARCH              -> VALIDATED          (+ research metadata)
VALIDATED_SMALL_N               -> VALIDATED          (+ small_n metadata)
```

Recorded status equals mapping result for every migrated record (0 mismatches).

### Quarantine (9, all non-card files — truthful, never hidden)

```
corpus/conversation-derived/CEREBUS_DATA_INTERPRETATION_DOCTRINE.md   (conversation-derived, never canonicalized)
corpus/indicators/btc/CEREBUS_BTC_Daily_Weekly_Monthly_Tracker_V1.pine
corpus/indicators/eur/CEREBUS_Daily_News_Rekey_Engine_V1_1_P90_MERGED_FIX1.pine
corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1.pine
corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1_2.pine
corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1_6_1_COMPILE_FIX.pine
corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1_6_4_STYLE_COLORS.pine
corpus/indicators/xau/CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine
corpus/research/eur/daily_range_tracker/PHASE_1_LEDGER.md
     all: "file does not match a known canonical card template"
```

**Correction of the interrupted session's earlier report**: it claimed
"30 migrated cards + 10 claims, zero quarantined". Actual truth: **20 card
files + 10 registry claims = 30 migrated objects; 9 quarantined sources** (all
non-card: 7 Pine indicators + 1 research ledger + 1 conversation-derived doc).
Zero *card-file* quarantines is the correct figure; "zero quarantined" overall
was false. The Pine sources are not lost: 3 carry `IMPLEMENTS` edges and 4
carry `VISUALIZES` edges to their models (visual ≠ empirical).

### Provenance coverage

- 29 artifacts registered, 29/29 have `sha256:` content identity + repo-relative
  locator, 29/29 carry ≥1 edge.
- 38 edges: `DEFINES` 30 (20 card files + 10 claim-registry→CLAIM), `SUPPORTS` 1
  (Phase1 ledger → `EV.EUR.DAILY.PHASE1_TIERS.V1`), `IMPLEMENTS` 3 (Pine →
  model), `VISUALIZES` 4 (EUR quarter/month trackers → `MOD.EUR.HIGHER_ORDER.V1`).
- **30/30 migrated objects have ≥1 provenance edge** (acceptance I1 — repaired,
  see Defects R5).

### Claim adequacy (all 10 registry claims)

Every claim: evidence reference resolves inside the plan, evidence carries the
`evidence_for` back-reference (**mutual CLAIM↔EVIDENCE**), model reference
resolves, `claim_identity` present, ≥1 provenance edge:

```
CL.EUR.HO.D3_DIRECTION      FORWARD_OOS   EV.EUR.HO.D3_DIRECTION.V1       MOD.EUR.HIGHER_ORDER.V1
CL.EUR.HO.UNFINISHED_M3     FORWARD_OOS   EV.EUR.HO.UNFINISHED_M3.V1      MOD.EUR.HIGHER_ORDER.V1
CL.EUR.HO.M1_RANGE_CORR     VALIDATED     EV.EUR.HO.M1_RANGE_CORR.V1      MOD.EUR.HIGHER_ORDER.V1
CL.EUR.DAILY.TIER_CALIBRATION VALIDATED   EV.EUR.DAILY.PHASE1_TIERS.V1    MOD.EUR.DAILY.NEWS_REKEY.V1
CL.EUR.DAILY.NEWS_INCREMENT CANDIDATE     EV.EUR.DAILY.NEWS_AUC.V1        MOD.EUR.DAILY.NEWS_REKEY.V1
CL.EUR.WEEKLY.TIER_RANGE    VALIDATED     EV.EUR.WEEKLY.TIER_RANGE.V1     MOD.EUR.WEEKLY.V1_1
CL.XAU.PROMOTION.68_80      VALIDATED     EV.XAU.PROMOTION.68_80.V1       MOD.XAU.GAME.L1_L2_L3.V1
CL.XAU.PROMOTION.120_132    RESEARCH_FLAG EV.XAU.PROMOTION.120_132.V1     MOD.XAU.GAME.L1_L2_L3.V1
CL.JPY.CARRY.ROLE_RELATION  VALIDATED     EV.JPY.CARRY.BASKET_RELATION.V1 MOD.JPY.CARRY_GAME.L1_L3.V1
CL.FIB.R11.GENERATOR_FAILURE FALSIFIED    EV.FIB.R11.ANCHOR_OVERGEN.V1    MOD.CROSSASSET.FIB.RANGE_BIRTH.V1
```

Anti-fabrication: `test_registry_claims_match_registry_file_table` re-parses
`CLAIM_REGISTRY_V1.md` and asserts the governed `REGISTRY_CLAIMS` table matches
the source table row-for-row (ids, model via explicit ID mapping, claim text,
evidence, status, layer). 0 issues. Numerical claims: 0 unsupported
(`unsupported_numerical_claim=0`); BTC Tracker family carries no fabricated
evidence (H2).

### Frozen model-family distinctions (9/9 PASS)

1. ST parity/separation doctrine preserved on the EUR daily card (P90 lineage +
   "implementation parity … must be separated from empirical evidence").
2. `MANUAL_OPERATOR` preserved on JPY + XAU setups; Fib rekey `RESEARCH_ONLY`
   (manual validity kept distinct from automation).
3. No `AUTOMATION_APPROVED` / autonomous execution anywhere in I.3 output.
4. P90 present as lineage, never a ST synonym; no invented performance numbers
   (`P90.WR` never appears as a canonical id).
5. BTC Tracker migrated independently; **BTC Game not fabricated** (no object).
6. EUR families separate: `MOD.EUR.DAILY.NEWS_REKEY.V1`,
   `MOD.EUR.HIGHER_ORDER.V1`, `MOD.EUR.WEEKLY.V1_1`.
7. XAU L1/L2/L3 distinct levels preserved.
8. JPY role asymmetry: model + gated setup + basket evidence triad exists.
9. Fib R11 negative evidence survives: claim FALSIFIED,
   `evidence_type=NEGATIVE_EVIDENCE`, `negative_evidence=1`.

### Faithful source representation

All 20 card objects: title matches source H1, canonical status equals the
explicit mapping of the source status (0 mismatches), full parsed payload in
`metadata["card"]` (no silent field loss). 0 issues.

## Persistence proof (Phase 4 — `persistence_proof.py`, all PASS)

| # | Step | Evidence |
|---|------|----------|
| 1 | DRY RUN zero writes | store: 0 objects, 0 artifacts, 0 edges after `DRY_RUN` |
| 2 | APPLY clean store | 30 objects / 29 artifacts / 38 edges committed, conflicts=0 |
| 3 | Second APPLY idempotent | `unchanged=30`, conflicts=0, store state byte-identical |
| 4 | Conflict rejection | mutated `MOD.BTC.TRACKER.DWM.V1` → `ConflictError`, content NOT overwritten |
| 5 | Duplicate ids in one batch | poisoned plan (same id twice) → `DuplicateCanonicalObject`, 0 objects / 0 artifacts persisted |
| 6 | Mutual references commit | real `CL.FIB.R11.GENERATOR_FAILURE` ↔ `EV.FIB.R11.ANCHOR_OVERGEN.V1`, all refs resolve post-commit |
| 7 | Invalid references roll back | `DanglingReference` → whole batch gone (0 objects) |

The same seven semantics are asserted as unit tests in
`tests/test_forge_persistence.py` (memory gateway) and — for mutual refs,
in-batch duplicates, rollback, and full-corpus apply/idempotency — on real
PostgreSQL in `tests/test_forge_postgres_integration.py` (18 passed).

## Defects discovered and repairs (recorded explicitly)

**R1 — mutual canonical references (defect A).** The in-memory gateway
validated each record against *committed* state only, so a valid transaction
containing mutually referencing CLAIM and EVIDENCE objects was rejected.
Repair: the whole pending batch is validated as a unit (batch-internal
resolution) at transaction exit; a batch whose ordinary references never
resolve still raises `DanglingReference` and rolls back atomically — post-commit
store never contains dangling truth.
Tests: `test_mutual_references_commit_as_one_unit` (memory),
`test_mutual_references_commit_in_one_transaction` (PostgreSQL).

**R2 — duplicate ids within one batch (defect B).** Two pending records with
the same canonical id (neither in committed state) silently overwrote each
other. Repair: `DuplicateCanonicalObject` raised on the second record; the
transaction rolls back — nothing partial persists. Existing committed-duplicate
and stale-write protections preserved.
Tests: `test_duplicate_canonical_id_within_one_batch_rejected` (memory),
`test_duplicate_canonical_id_within_batch_rejected` (PostgreSQL),
`test_failed_batch_rolls_back` (poisoned plan through the runner).

**R3 — SQL claim-identity serializer stored `{}` (found by the new PG
corpus-apply test).** `ClaimIdentity` has no `comparison_key_dict()` method,
so `hasattr(...)` fell back to `{}`; the read path then truthily parsed the
`"{}"` string and crashed with `KeyError: 'market'` — any CLAIM with identity
roundtripped through SQL was broken (latent since II.2; no prior test wrote a
CLAIM with identity through SQL). Repair: the write path persists all eight
identity dimensions explicitly; the read path treats an empty legacy dict as
*absent* identity (never fabricates dimension values, never crashes).
Tests: `test_claim_identity_survives_sql_roundtrip`,
`test_missing_identity_is_absent_not_crash` (SQLite contract),
`test_full_corpus_backfill_apply_on_postgres` (live PG).

**R4 — reference order treated as governed content.** The SQL gateway reads
references in sorted order (`ORDER BY target_id, relation`; the frozen schema
models references as an unordered set — PK `(canonical_id, target_id, relation)`,
and P3 forbids new migrations), while plan records keep authored order; the
runner's conflict comparison therefore reported a false `ConflictError` on the
second apply of any multi-reference object. Repair: the governed payload
compares reference *sets* (sorted by target/relation/allow). Authored order is
presentation, not truth; duplicate targets were already impossible.
Tests: `test_reference_order_is_not_governed_content`,
reference-set assertion in the PG corpus apply.

**R5 — acceptance gaps A1/I1 found by the Phase 3 audit.** The claim registry
(`corpus/canonical/CLAIM_REGISTRY_V1.md`) was not inventoried, and the 10
CLAIM objects had **zero** provenance edges (I1 violation). Repair: the registry
is loaded by the frozen inventory, classified `GOVERNANCE_CONTRACT` (new
`MigrationClass` member), registered as an artifact with `sha256:` identity,
and emits 10 `DEFINES` edges — one per registry CLAIM; a missing registry
classifies `MISSING_SOURCE` (I4) and is never fabricated.
Tests: `test_every_in_scope_source_appears_once` (30 with registry outcome),
`test_claim_registry_inventoried_with_claim_edges`,
`test_claim_registry_missing_classified_not_fabricated`,
`test_every_migrated_object_has_provenance_edge`.

**Recovery note.** The interrupted edit had left duplicated apply-loop code in
`runner.py`; removed in Phase 0/1 so `_apply_plan` executes exactly one
two-phase batch (stage → one `gateway.transaction()` commit).
`tests/test_forge_backfill_more.py` was destroyed by that interruption and
reconstructed 1:1 from its `.pyc` disassembly (44 tests, byte-for-byte
assertions and constants mirrored; reconstruction artifacts
`_pyc_dis.txt` / `_pyc_dump.txt` remain in the workspace root, untracked).

## Migrations

`discover_migrations()` == `[1, 2]` (001 + 002 only; asserted by
`tests/test_forge_policy.py::TestScopeGuards::test_no_new_migration` and
`tests/test_forge_identity.py`). I.3 added **no** migration, no table, no
column. 001 SHA pin unchanged (`test_001_and_002_unchanged`).

## Security implications

- No route added (V1): `/forge/v1/*` route set unchanged — health/ready/meta
  only; `test_no_new_public_corpus_route` enumerates the forbidden corpus
  surfaces.
- Report and logs contain no INTERNAL_METHOD/INTERNAL_CODE bodies (O1:
  `test_report_contains_no_internal_bodies`).
- Policy module untouched (O2/U1: `test_policy_engine_untouched_by_backfill`,
  `git diff` contains no `app/forge/policy.py`); no entitlement/plan/license/
  Whop object created; PUBLIC_TEACHING never assigned by default.
- No credentials in code or output; PG access only via `FORGE_TEST_DATABASE_URL`.
- Signal Guard files unchanged (`git diff --name-only` inventory) and green
  (64 passed).

## Unresolved provenance gaps / known limitations

1. **Governance contracts other than the claim registry** (ANSWER_CONTRACT,
   TAXONOMY, ONTOLOGY_CROSSWALK, PRODUCT_EXPOSURE_RULES, RETRIEVAL_OBJECT_SCHEMA,
   `schemas/*`) are read as rules but are not registered as artifacts. PLAN §1
   prose says governance contracts are "inventoried as governance-contract
   artifacts"; the frozen executable gate A1 enumerates only the claim registry
   among them. A1 is satisfied; the broader PLAN prose is recorded here as a
   deviation to be closed in a later bloc if desired.
2. **Domain `content_hash()` remains reference-order-sensitive** (I.1 frozen
   `deterministic_payload`), while persistence stores references as a set.
   For multi-reference objects read back from SQL, the *domain* hash may differ
   from the pre-persist hash by reference order alone. Governed comparisons in
   I.3 normalize order (R4). Retrieval (I.4) must not treat reference order as
   identity; if cross-store hash equality is required, I.4 should hash the
   normalized payload.
3. **PG integration suite grants fresh-database semantics per invocation**
   (fixture truncates data tables; schema and migration ledger untouched).
   CI's postgres job runs the module three times against one service
   container; without this the second run would see committed residue. Local
   reruns need no manual cleanup.
4. **Quarantined sources stay quarantined**: the 9 non-card files are
   inventory-only; no attempt was made to canonicalize Pine code or
   conversation-derived doctrine into empirical objects (K1/J1).
5. **CI result (observed).** Push-triggered workflow `forge-tests.yml`:
   first run `37799721801` exposed a hidden rerun-state dependency — the
   postgres job runs the PG module three times against one service container,
   which previously only passed because no test committed rows between
   invocations; the new committing tests surfaced duplicate-key residue.
   Repaired in rung `7aab0f1` (fixture truncates data tables per invocation,
   mirroring the fresh container; no assertion changed — locally reproduced
   all three CI steps: 464 / 18 / 7 passed). Verification run `37800246168`
   on `7aab0f1`: **both jobs green** (`test` 19s, `postgres` 58s).

## Acceptance-clause mapping (A–X)

| Clause | Proof |
|--------|-------|
| A1 inventory complete (7+10+3+1 registry) | audit INVENTORY; `test_every_in_scope_source_appears_once` (30) |
| A2 deterministic | `test_inventory_is_deterministic`, `test_reproducible_from_clean_state` |
| A3 content identity | audit "artifacts missing identity: 0"; `test_source_artifacts_registered_with_identity` |
| A4 sources unmodified | `test_sources_not_modified`; `git status` shows no `corpus/` change |
| A5 quarantine truthful | quarantine table (9 with reasons) above |
| B1–B3 explicit ID maps | 10-entry table above; `setup_id_maps_explicitly`, `all_migrated_ids_parse_with_expected_type` |
| B4 type-mismatch rejected | `object_type_mismatch_rejected` |
| B5 no fuzzy map | `invalid_legacy_id_does_not_fuzzy_map` |
| B6 no shared target | audit: 0 duplicate targets; `no_two_legacy_ids_share_canonical_target` |
| B7 legacy ids preserved | `legacy_ids_preserved_in_metadata` |
| C1–C2 explicit/unknown status | 15-row table; `status_mapping_explicit_table`, `unknown_status_quarantines` |
| C3 no promotion | audit: 0 record mismatches; `no_status_promotion` |
| C4 qualifiers survive | `research_qualifiers_survive_as_metadata`, `uncertainty_markers_not_fabricated_values` |
| C5 evidence-type table | `negative_evidence_status_and_type_preserved` + evidence-type tests |
| D1–D4 model cards | `all_model_cards_parse`, `no_silent_field_loss`, `every_in_scope_source_appears_once` |
| E1–E3 evidence cards | `all_evidence_cards_parse`, evidence path tests, `numerical_claims_have_evidence_path` |
| F1–F3 setup cards | `all_setup_cards_parse_with_typed_ids`, `manual_operator_preserved`, `research_only_preserved` |
| F4 no AUTOMATION_APPROVED | `no_automation_approved_created`, `no_autonomous_execution_approval_anywhere` |
| G1–G4 claims | `all_ten_registry_claims_exist`, `claim_identity_dimensions_preserved`, `parallel_populations_not_merged` |
| H1 numerical evidence path | `numerical_claims_have_evidence_path`, `claim_without_evidence_would_be_unsupported` |
| H2 BTC no fabricated evidence | `btc_game_not_fabricated`, `btc_tracker_migrated_independently` |
| I1 ≥1 edge per object | repaired (R5); `test_every_migrated_object_has_provenance_edge` (30/30) |
| I2 typed edges | `markdown_defines_edges`, `supports_edge_correct`, `implements_edges_correct`, `visualizes_edges_correct_and_non_empirical` |
| I3 no SUPPORTS for visual/conversation | `test_no_supports_edge_for_visual_or_conversation` |
| I4 missing source classified | `missing_named_source_classified_not_fabricated`, `test_claim_registry_missing_classified_not_fabricated` |
| J1 visual non-empirical | `visualizes_edges_correct_and_non_empirical` |
| K1 conversation-derived | `conversation_derived_inventoried_not_canonicalized` |
| L1–L2 negative evidence | `fib_r11_negative_evidence_survives`, audit family check |
| M1–M2 no fabrication / no silent drop | `no_silent_field_loss`, `uncertainty_markers_not_fabricated_values`, registry table match test |
| N1–N3 exposure | `all_migrated_objects_carry_valid_exposure`, `evidence_exposure_assignment_follows_frozen_rules`, `unknown_exposure_fails_closed`, `no_public_teaching_by_default` |
| O1 no internal bodies | `report_contains_no_internal_bodies` |
| O2 policy untouched | `policy_engine_untouched_by_backfill` |
| P1 writes via port | runner uses only `PersistenceGateway`; `apply_performs_writes_and_roundtrip` |
| P2 roundtrip semantics | PG corpus apply (status/identity/references/metadata asserted per object) |
| P3 no new migration | `discover_migrations() == [1, 2]` (command + `TestScopeGuards::test_no_new_migration`, `test_001_and_002_unchanged`) |
| Q1 idempotent | proof step 3; `second_identical_apply_is_idempotent`; PG `unchanged=30` |
| R1 conflict | proof step 4; `conflicting_content_rejected_no_silent_overwrite` |
| S1 dry-run zero writes | proof step 1; `dry_run_performs_zero_writes` |
| T1 atomic batch rollback | proof steps 5/7; `failed_batch_rolls_back`, PG leak test |
| U1 policy boundary | `policy_engine_untouched_by_backfill`, `no_entitlement_license_whop_created`, git diff inventory |
| V1 no public corpus route | `test_no_new_public_corpus_route` |
| W1 reproducibility | `reproducible_from_clean_state`, `persisted_hash_stable`, stable audit content hash |
| X1 regression | focused gates + Signal Guard 64 + full suite **446 passed / 18 skipped** + PG **18 passed**; no test weakened or removed (only assertions strengthened: inventory 29→30, new I1/I4/identity tests) |
