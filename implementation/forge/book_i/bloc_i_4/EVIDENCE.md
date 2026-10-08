# Book I / Bloc I.4 — Retrieval Index — EVIDENCE

## Planning identity

- Branch `forge`, starting ratified head `05c74a1204a8c2a33c53206710e9d2399bb5b87b`
  (I.3 CLOSED — PASS, CI green on that SHA).
- PLAN + ACCEPTANCE: `6a5d648` — frozen A–W gates.
- Implementation ladder through `1738f04` (index contract, build/retrieval,
  policy integration, focused suite).
- This document records the **acceptance/evidence phase**: fresh execution of
  every frozen gate, the exact indexed corpus state, an executable evidence
  harness, and one added regression test closing the only law that had no
  executable proof (generation metadata never changes record identity).
  No history was reset, amended, rebased, squashed, or force-pushed.

## Commit ladder (I.4, append-only)

| Rung | SHA | Content |
|------|-----|---------|
| start | `05c74a1` | I.3 verification record (ratified head) |
| 1 | `6a5d648` | I.4 PLAN + ACCEPTANCE (frozen A–W gates) |
| 2 | `081fe78` | I.4 index contract: record/header split, alias table, compiler, facet law, normalized identity |
| 3 | `b940732` | I.4 build + retrieval: DRY_RUN/APPLY build, fingerprint/index-hash identity, idempotence, staleness, atomic publication, quarantine catalog, structured filters, deterministic ranking |
| 4 | `2b5f0db` | I.4 policy integration: retrieval service sequence, FOUND vs SUPPORTED navigation, policy-gated quarantine discovery |
| 5 | `1738f04` | I.4 tests: focused suite + PG cross-store index identity/staleness evidence |
| 6 | `eaf0e5a` | I.4 evidence: harness `tools/index_evidence.py`, generation-identity regression test, EVIDENCE.md |
| 7 | `017fc96` | I.4 ratification — CLOSED — PASS |
| 8 | (this file) | I.4 verification record: CI run `37861618933` green on `017fc96` (test + postgres) |

`git status` at evidence time: only `tests/test_forge_retrieval.py` modified
(one added test), the new `implementation/forge/book_i/bloc_i_4/tools/` folder,
and the two preserved untracked bytecode-recovery artifacts `_pyc_dis.txt` /
`_pyc_dump.txt` (never committed, per I.3 recovery note). No Signal Guard file,
no policy file, no corpus source, no route file, no requirements file changed.

## Runtime environment

- Python 3.11.9, SQLAlchemy 2.0.49, psycopg2 2.9.12 (local Windows runner).
- PostgreSQL 16.15 local (Windows service `postgresql-x64-16`), role `forge`,
  database `forge_test`, credentials identical to CI
  (`FORGE_TEST_DATABASE_URL` shape unchanged).
- CI: `.github/workflows/forge-tests.yml` — `test` job (`python -m pytest -q`)
  and `postgres` job (fresh `postgres:16` service; full suite against live PG,
  then the PG integration module, then the identity/session filter — the
  module therefore runs 3× against one container, which the per-invocation
  fresh-database fixture from I.3 `7aab0f1` supports).

## Commands executed and exact results (fresh execution)

All commands run from the repository root with `set -o pipefail`; every exit
status below is the test command's own status, not the pipeline's tail.

1. **I.4 focused suite** `python -m pytest tests/test_forge_retrieval.py -q`
   → **124 passed, 0 failed** (was 123 at rung `1738f04`; the +1 is the new
   `test_generation_metadata_never_changes_record_identity` added in this
   evidence phase — see "Coverage added").
   Classes (124): ExposureMatrix 12, StructuredLookup 10, FrozenRecordContract
   10, BuildLaws 11, ExposureCompiler 9, ModelTruth 8, Ranking 7,
   ProvenanceNavigation 7, Quarantine 6, PolicyBeforeContent 6, AliasRouting 6,
   IndexAuthority 5, Security 4, InternalMaterial 4, ClaimPopulationSeparation
   4, BoundaryIntegrity 4, ReferenceOrderNormalization 3, NegativeEvidence 3,
   GovernanceCoverage 3, Reproducibility 2.

2. **Prior FORGE regression gates** (batched, exit 0) → **398 passed**;
   per-file collection matches the I.3 gate numbers exactly:
   canonical 37 + schemas 4 = I.1 **41**, provenance **41** (I.2),
   identity **66** (II.3), policy **86** (II.4), persistence **56** (II.2),
   backfill 28 + backfill_more 44 = I.3 **72**, service composition **36**.

3. **Signal Guard** `test_duplicate_signal.py + test_ghost_signal.py +
   test_forge_service_composition.py + test_vision_confirm.py +
   test_vision_mcp.py` → **64 passed** (files unchanged by I.4).

4. **Full repository suite** `python -m pytest tests/ -q`
   → **570 passed, 19 skipped, 0 failed** (19 skips are exactly the PostgreSQL
   integration tests when `FORGE_TEST_DATABASE_URL` is unset; the count is 569
   + the 1 test added in this evidence phase).

5. **PostgreSQL integration, real server** (CI credentials, local PG 16.15):

   ```
   FORGE_TEST_DATABASE_URL="postgresql+psycopg2://forge:forge_ci_password@localhost:5432/forge_test" \
     python -m pytest -q tests/test_forge_postgres_integration.py
   ```

   → **19 passed**; executed **3 consecutive times** (CI postgres-job shape)
   → **19 / 19 / 19 passed**, exit 0 each run — no rerun-state residue.

6. **CI-shaped full suite with live PostgreSQL** (same env var, `tests/` all)
   → **589 passed, 0 skipped, 0 failed** (= 570 + 19 PG tests).

7. **Evidence harness** (committed in this rung):

   ```
   PYTHONPATH=. python implementation/forge/book_i/bloc_i_4/tools/index_evidence.py
   ```

   → exit 0, **95/95 checks PASS**, `ALL INDEX EVIDENCE CHECKS PASSED`.
   Read-only: in-memory gateway, no corpus or database writes.

## Indexed corpus — exact counts

Persisted state (I.3 APPLY through the port) and the index compiled from it:

| Quantity | Exact value |
|---|---|
| canonical objects (index records) | **30** — CLAIM 10, EVIDENCE 10, MODEL 7, SETUP 3 |
| artifacts referenced by edges | **29** |
| provenance edges | **38** |
| quarantined sources | **9** (7 Pine + 1 research ledger + 1 conversation-derived); card-file quarantines **0** |
| exposure split | SUBSCRIBER_MODEL **24**, RESEARCH_LAB **4**, OPERATOR_ONLY **2** (PUBLIC_TEACHING 0, INTERNAL_* 0 in the real corpus) |
| status split | VALIDATED 10, CANDIDATE 8, RESEARCH_FLAG 5, FORWARD_OOS 4, FALSIFIED 2, DESCRIPTIVE 1 |
| build outcome | `PUBLISHED`, generation **1**, records **30** |
| `source_fingerprint` | `9675431033dd1fa667e3ef3d7ea65526c7bf5a545bf073875af11496236fa226` |
| `index_hash` | `e23cfeb4576a6a534a39d4a336bda09b4972baa8ef9097c158fdc4cf5225d173` |
| staleness after build | `False`; rebuild → `UNCHANGED`, generation stays 1, fingerprint and hash identical; a second independent build is byte-identical |

Counts asserted by `test_counts_match_persisted_state`, `test_zero_card_file_quarantines`
and re-asserted by the harness (30/29/38/9/0).

## Query coverage (exact result counts, operator context)

Every filter dimension of `RetrievalQuery` executed against the real index
(harness rows, each `results, denied=0`):

| Dimension | Counts |
|---|---|
| unfiltered | 30 |
| object_type | CLAIM 10, EVIDENCE 10, MODEL 7, SETUP 3 (exact partition) |
| market | EURUSD 17, XAUUSD 8 (unrecognized value → 0, fail closed) |
| model_family | EUR 15, XAU 6, JPY 4, BTC 1 |
| status | VALIDATED 10, CANDIDATE 8, RESEARCH_FLAG 5, FORWARD_OOS 4, FALSIFIED 2, DESCRIPTIVE 1 |
| exposure | SUBSCRIBER_MODEL 24, RESEARCH_LAB 4, OPERATOR_ONLY 2 |
| layer | NONE 23, CROSS_LAYER 4, L1 1, L2 1, L3 1 (disjoint) |
| source_artifact | 1 per sampled artifact id |
| provenance_relation | DEFINES 30, IMPLEMENTS 3, VISUALIZES 1, SUPPORTS 1 (record matches) |
| canonical_id | exact → 1; unknown id → **0** (never fuzzy-matched) |
| text (lexical) | `anchor overgeneration` 3, `weekly engine` 4, `carry basket` 3, `quarter zone` 6, `news residual auc` 3, `p90` 11 |
| claim_identity | SAME_POPULATION only → 1 for the sampled claim |

Plus: alias expansion (verbatim crosswalk table), ranking key
`(identity_tier, -structured_hits, -lexical_hits, canonical_id)` asserted total
and stable under input reordering, zero-signal query returns nothing, ranking
never changes `status`/`exposure`/`claim_identity` (E1–E5, F1–F4).

## Provenance paths (10/10 chains, research context)

`Claim → Evidence → Source Artifact` navigation, every registry claim:

| Claim | Evidence | Artifacts | found / supported / missing |
|---|---|---|---|
| CL.EUR.DAILY.NEWS_INCREMENT | EV.EUR.DAILY.NEWS_AUC.V1 | 1 | ✓ / ✓ / none |
| CL.EUR.DAILY.TIER_CALIBRATION | EV.EUR.DAILY.PHASE1_TIERS.V1 | 2 | ✓ / ✓ / none |
| CL.EUR.HO.D3_DIRECTION | EV.EUR.HO.D3_DIRECTION.V1 | 1 | ✓ / ✓ / none |
| CL.EUR.HO.M1_RANGE_CORR | EV.EUR.HO.M1_RANGE_CORR.V1 | 1 | ✓ / ✓ / none |
| CL.EUR.HO.UNFINISHED_M3 | EV.EUR.HO.UNFINISHED_M3.V1 | 1 | ✓ / ✓ / none |
| CL.EUR.WEEKLY.TIER_RANGE | EV.EUR.WEEKLY.TIER_RANGE.V1 | 1 | ✓ / ✓ / none |
| CL.FIB.R11.GENERATOR_FAILURE | EV.FIB.R11.ANCHOR_OVERGEN.V1 | 1 | ✓ / ✓ / none |
| CL.JPY.CARRY.ROLE_RELATION | EV.JPY.CARRY.BASKET_RELATION.V1 | 1 | ✓ / ✓ / none |
| CL.XAU.PROMOTION.120_132 | EV.XAU.PROMOTION.120_132.V1 | 1 | ✓ / ✓ / none |
| CL.XAU.PROMOTION.68_80 | EV.XAU.PROMOTION.68_80.V1 | 1 | ✓ / ✓ / none |

- **found 10/10, supported 10/10** (support per ratified I.2 `classify_support`;
  visual/conversation sources never count).
- Unknown id → `found=False`, `missing=[NOT_IN_INDEX]` — reported, never
  invented, never approximated by lexical similarity.
- Negative evidence retrievable under research: `EV.FIB.R11.ANCHOR_OVERGEN.V1`
  = FALSIFIED + NEGATIVE_EVIDENCE; `CL.FIB.R11.GENERATOR_FAILURE` text keeps
  "overproduced" (never reworded as support).
- FOUND never implies SUPPORTED; neither implies an answer — result objects
  carry status/provenance facts only (J1–J5, K1–K2).

## Exposure matrix

Real corpus, retrievable count per context (harness, asserted row-by-row):

| exposure | anon | auth_nocap | member | operator | research | admin_research | internal |
|---|---|---|---|---|---|---|---|
| SUBSCRIBER_MODEL (24) | 0 | 0 | **24** | 24 | 24 | 0 | 0 |
| OPERATOR_ONLY (2) | 0 | 0 | 0 | **2** | 2 | 0 | 0 |
| RESEARCH_LAB (4) | 0 | 0 | 0 | 4 | **4** | 0 | 0 |

- Anonymous: **0 results, 30 denials**; every denial entry's fields are exactly
  `{object_id, exposure, reason_code}` — content-free by structure.
- `forge.internal` alone admits only the internal classes (fail closed for
  ordinary exposure); `admin_research` alone grants no ordinary corpus read —
  asserted by the 12-row synthetic `TestExposureMatrix::test_matrix`, which
  exercises **all six classes in both allow and deny directions**
  (PUBLIC_TEACHING, SUBSCRIBER_MODEL, OPERATOR_ONLY, RESEARCH_LAB,
  INTERNAL_METHOD, INTERNAL_CODE).
- Research authorization never rewrites research status (RESEARCH_FLAG stays
  RESEARCH_FLAG).
- INTERNAL_METHOD/INTERNAL_CODE real-corpus records do not exist; their
  identity-only compilation (empty `retrieval_text`, empty content facets,
  `max_quote_scope=NONE`), build-failure on unknown exposure, and
  internal-only release are proven on synthetic fixtures
  (`TestExposureCompiler`, `TestInternalMaterial`).

## Deny-before-load (adversarial evidence)

- Instrumented loader: **0 calls on DENY, exactly 1 per ALLOWED record**
  (`test_deny_before_load_zero_loads_on_deny`, `test_allow_loads_each_allowed_record_exactly_once`);
  denied hops stop provenance chains without loading the hop; a denied root
  loads nothing.
- A denied record contributes no text/snippet/facet/ranking explanation —
  the denial entry has no content field at all; marker-text tests prove
  unauthorized text never reaches the response, audit trail, or citations.
- Stripping: INTERNAL_METHOD and CODE segments are removed from generated
  text, `max_quote_scope` drops to `NONE`; no internal body appears in any
  record, response, snippet, ranking explanation, log line, report or
  diagnostic (`TestInternalMaterial`, `TestSecurity`).
- Unknown/missing exposure fails closed at release (`UNKNOWN_EXPOSURE`).
- The sequence runs through the ratified `ForgePolicyEnforcementService`
  (single policy authority; `app/forge/policy.py` byte-unchanged — pinned
  SHA-256 `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`
  asserted by `test_policy_module_is_untouched`).

## Quarantine treatment

- 9 quarantined sources, all non-card, all listed with reasons (harness
  reproduces the list); they are absent from persistence and absent from the
  index by construction (`index ids ∩ quarantine paths = ∅`).
- Ordinary search (any context) returns **0** quarantine notices and never a
  quarantine path among results.
- Explicit `include_quarantine=True` under a research-authorized II.4 decision
  returns **9** notices carrying safe metadata only (`source_path`, `reason`,
  `quarantined: true`) — no body, no snippet; anonymous explicit discovery
  fails closed (0 notices, 0 results).
- Hard guard: a record whose `DEFINES` source locator enters the quarantine
  catalog is excluded from the build and reported
  (`test_quarantined_source_excludes_a_defined_record`).

## Index build laws (freshly executed)

| Law | Proof |
|---|---|
| explicit DRY_RUN/APPLY, never on import/startup/request | `test_dry_run_publishes_nothing`, `test_index_never_executes_on_import_or_startup` |
| port-only reads, zero writes | `test_index_never_writes_to_the_port`, `test_records_come_from_persistence_not_markdown` |
| unpublished index fails closed | `test_unbuilt_index_fails_closed` |
| idempotent rebuild | `UNCHANGED`, generation 1 kept, identical hashes (harness + `test_rebuild_is_idempotent`) |
| staleness | False after build; True after a real status transition until rebuild; fresh index stale until first build; added object → `changed`/`added` report and generation 2 |
| duplicate id in one build | `IndexBuildError(DUPLICATE_CANONICAL_OBJECT)`, previous generation content-hash unchanged, nothing published |
| partial failure | poisoned exposure compile → previous generation remains current (same generation, same content hash) |
| atomic publication | generation immutable; readers observe a whole generation (`test_publication_is_atomic_from_a_readers_view`) |
| reproducibility | two independent builds byte-identical (fingerprint, index hash, per-record hashes); report JSON deterministic, no timestamps |

## Reference-order normalization and cross-store identity (O, U)

- Record identity = `deterministic_payload()` (sorted-key JSON, references and
  all collections normalized, **top-level `generation` excluded**);
  `content_hash()` = sha256 of that payload. Two records differing only in
  reference order produce the same hash (`test_index_hash_is_identical_across_reference_order`,
  `test_identity_independent_of_relationship_order`).
- Frozen I.1 `content_hash()` semantics untouched (`test_frozen_i1_hash_semantics_are_untouched`);
  no migration, no ontology change ⇒ no GAP/ADR required (O3).
- **Cross-store:** PG integration test builds the index from real PostgreSQL
  and from an identically-mirrored memory store over the same governed state
  and asserts equal `index_hash`, equal compiled count, staleness after a real
  PG status transition, rebuild → generation 2, and hash stability on rebuild
  (`test_index_builds_from_postgres_with_identical_hash_and_freshness`, part of
  the 19 passed).

## Coverage added in this evidence phase

The mission requires that **index-generation metadata never changes canonical
retrieval-record identity**. The implementation already excluded top-level
`generation` from `deterministic_payload()`, but no test proved the
cross-generation law (existing determinism tests only compared generation-1
builds). Added, append-only:

- `TestBuildLaws::test_generation_metadata_never_changes_record_identity` —
  builds gen 1, records a survivor's `content_hash`, adds an object so the
  rebuild publishes generation 2, then asserts the survivor's `content_hash`
  is unchanged while its `generation` field advances, and that the payload has
  no top-level `generation` key (the source `conflict.generation` string is
  content, F3, and is retained).
- `implementation/forge/book_i/bloc_i_4/tools/index_evidence.py` — the
  committed 95-check harness behind every exact number in this document.

Focused suite moved 123 → **124**; no existing test was weakened or removed.

## Boundary and security invariants

- **No route:** `/forge/v1/*` = `{health, ready, meta}`; `/retrieval`,
  `/search`, `/objects`, `/corpus`, `/query` all 404
  (`test_no_route_is_added`).
- **No new dependency, no new migration:** `discover_migrations() == [1, 2]`,
  001 SHA pin unchanged (`test_no_new_migration`); `requirements.txt`
  untouched; no provider/embedding/import surface anywhere in the package
  (`test_no_embedding_vector_or_provider_surface_exists`).
- **No commercial object:** no OpenRouter/Whop/license/entitlement/plan object,
  no provider seam (`test_no_commercial_or_provider_object_is_created`).
- **No credentials:** retrieval package, tests, reports and logs carry no
  credential/DSN/token/provider id (`test_retrieval_package_has_no_credential_material`,
  `test_no_credential_material_in_tests_or_sources`); PG access only via
  `FORGE_TEST_DATABASE_URL`.
- **No I.5 behavior:** no QA, Ask CEREBUS, or public corpus API exists.

## Known gaps and carried-forward limitations

1. **Windows CRLF migration-hash limitation (carried forward unchanged).**
   `test_001_and_002_unchanged` pins the raw bytes of `001_initial_schema.sql`
   by SHA-256. On a *fresh* Windows checkout with `core.autocrlf=true` the
   file arrives CRLF-normalized and the pin fails until the file is
   LF-normalized locally; Linux CI is unaffected. The frozen migration
   contract was **not** changed to accommodate this — recorded here as a
   checkout-environment limitation (also recorded in I.3 evidence).
2. **Governance contracts other than the Claim Registry remain rules-read,
   not artifact-registered** (I.3 limitation B). I.4 compiles canonical
   objects only — `ART.*` can never become a retrieval record (P1–P3) — and
   keeps governance contracts classified as alias-table data or policy input.
3. **Lexical, not semantic (frozen reading).** I.4 embeds nothing and stores
   no vectors; embeddings belong to Book VII (`VII.5 Retrieval Rebuild`).
   The structured-over-lexical precedence defined here binds any future
   semantic layer (E4).
4. **Real corpus contains no PUBLIC_TEACHING or INTERNAL_* records.** Those
   exposure classes are exercised through synthetic fixtures in the focused
   suite (both directions), not against live corpus rows.
5. **The 9 quarantined sources stay quarantined** — inventory-only; no attempt
   to canonicalize Pine code or conversation-derived doctrine (I.3 K1/J1).
6. **Quarantine discovery payload is metadata-only by design** — no snippet
   preview exists even for authorized research contexts (L4).
7. **Reference-order sensitivity of the frozen I.1 domain hash remains**
   outside the index (handled by the normalized payload; O-law satisfied —
   disclosed, not repaired, since the I.1 kernel is frozen).

## Acceptance-clause mapping (A–W)

| Clause | Proof |
|--------|-------|
| A1 records from persistence via port | `test_records_come_from_persistence_not_markdown`; harness builds through the port |
| A2 index never writes / never supersedes | `test_index_never_writes_to_the_port` |
| A3 preserves id/type/version/status/exposure/artifacts/edges/relationships/generation | `test_records_carry_their_index_generation`, `test_every_record_implements_the_frozen_fields` |
| A4 only canonical types, ARTIFACT refused | `test_artifacts_are_never_retrieval_records`, `test_artifact_type_is_refused` |
| A5 header/body split, policy needs header only | `test_header_is_safe_projection_without_body`, `test_header_filters_run_before_any_body_load` |
| B1 frozen fields | `test_every_record_implements_the_frozen_fields` |
| B2/B3 unstated facets empty, stated survive | `test_unstated_facets_stay_empty_and_stated_ones_survive`, `test_sample_n_present_only_where_source_states_it`, `test_period_and_implementation_ids_from_real_fields` |
| B4 generated text from governed fields | `test_retrieval_text_is_generated_from_governed_fields` |
| B5 deterministic identity every run/store | `test_deterministic_payload_and_hash`, `test_two_builds_are_byte_identical`, PG U1 |
| C1 exact id / no fuzz | `test_exact_id_lookup_returns_exactly_one`, `test_unknown_id_is_never_fuzzily_matched` (harness: 1 / 0) |
| C2 all filters exact | `test_type_filter_partitions_the_index`, `test_market_filter_is_exact_and_disjoint`, `test_model_family_filter_separates_families`, `test_status_and_exposure_filters`, `test_layer_filter_returns_disjoint_sets`, `test_source_artifact_and_provenance_relation_filters`, `test_unknown_filter_value_matches_nothing` |
| C3 family from id grammar | `test_model_family_filter_separates_families` |
| C4 header before body load | `test_header_filters_run_before_any_body_load` |
| C5 structured outranks lexical | `test_exact_identity_outranks_lexical_similarity` |
| D1 same-population only | `test_identity_filter_returns_only_same_population` |
| D2 distinct populations never merged | `test_near_identical_prose_different_population_stays_distinct`, `test_parallel_populations_are_not_contradictions` |
| D3 identity verbatim, values never enter | `test_claim_identity_carried_verbatim`, `test_result_values_never_enter_identity` |
| E1 lexical governed text | `test_lexical_match_never_implies_support`, harness text rows |
| E2/E3 ranking key + byte-identical | `test_ranking_is_total_and_stable_under_input_order`, `test_same_query_twice_returns_identical_results`, `test_zero_signal_query_returns_nothing` |
| E4 no embedding/provider | `test_no_embedding_vector_or_provider_surface_exists` |
| E5 no authority promotion | `test_ranking_never_changes_status_or_exposure` |
| F1 verbatim alias table | `test_alias_table_is_verbatim_the_frozen_crosswalk` |
| F2 expansion never rewrites | `test_alias_routing_never_rewrites_status`, `test_historical_query_expands_to_modern_tokens` |
| F3 source generation retained | `test_generation_is_retained_from_the_source` (+ new generation-identity test: `conflict.generation` survives) |
| F4 no statistics across alias | `test_alias_routing_never_rewrites_status` |
| G1 valid exposure stamped | `test_every_real_record_carries_a_valid_exposure` |
| G2 unknown exposure fails build | `test_unknown_exposure_fails_the_build` |
| G3 internals identity-only | `test_internal_method_record_is_identity_only`, `test_internal_code_record_is_identity_only` |
| G4 max_quote_scope | `test_max_quote_scope_is_synthesis_for_real_records`, stripping tests |
| H1 sequence | `test_sequence_uses_the_ratified_enforcement_service` |
| H2 deny never loads / allow once | `test_deny_before_load_zero_loads_on_deny`, `test_allow_loads_each_allowed_record_exactly_once` |
| H3/H4 content-free denials | `test_denial_entries_are_content_free`, `test_unauthorized_text_never_reaches_the_response`, `test_denial_never_produces_a_body` (harness: denial fields == 3 keys) |
| H5 unknown exposure fails closed | `test_unknown_exposure_fails_closed_at_release` |
| I1–I6 exposure matrix | `TestExposureMatrix` 12 rows (both directions, six classes) + real-corpus matrix in harness |
| J1 found vs supported | `test_found_is_distinct_from_supported` |
| J2 chain to artifact | `test_claim_to_evidence_to_source_artifact`, `test_every_launch_claim_resolves_a_chain` (harness 10/10) |
| J3 guarded hops | `test_denied_hop_stops_the_chain_without_loading_it`, `test_denied_root_loads_nothing` |
| J4 missing links reported | `test_missing_object_is_reported_not_invented`, `test_evidence_without_source_is_reported_as_missing` |
| J5 lexical never implies support | `test_lexical_match_never_implies_support` |
| K1/K2 negative evidence | `TestNegativeEvidence` 3 tests |
| L1 counts | `test_counts_match_persisted_state` (30/29/38/9), `test_zero_card_file_quarantines` |
| L2 never ordinary results | `test_ordinary_search_never_returns_quarantine` (harness 0 notices) |
| L3 quarantine excludes record | `test_quarantined_source_excludes_a_defined_record` |
| L4 discovery gated, metadata only | `test_quarantine_discovery_requires_research_authorization` (harness: 9 research / 0 anon) |
| M1 explicit build, never auto | `test_index_never_executes_on_import_or_startup`, `test_dry_run_publishes_nothing` |
| M2 port-only reads | `test_index_never_writes_to_the_port` |
| M3 DRY_RUN publishes nothing | `test_dry_run_publishes_nothing` |
| M4 atomic publication | `test_publication_is_atomic_from_a_readers_view` |
| M5 idempotent rebuild | `test_rebuild_is_idempotent` (harness UNCHANGED) |
| M6 deterministic versioning | `test_added_object_starts_a_new_generation`, harness rebuild checks |
| N1 staleness | `test_staleness_detected_and_cleared_by_rebuild`, `test_fresh_index_is_stale_until_built`, PG U2 |
| N2 changed/added/removed report | `test_added_object_starts_a_new_generation` |
| N3 duplicate → conflict, nothing published | `test_duplicate_listing_conflicts_and_publishes_nothing` |
| N4 partial failure keeps previous | `test_partial_failure_leaves_previous_generation_current` |
| O1/O2 normalized identity | `test_governed_payload_sorts_relationships`, `test_index_hash_is_identical_across_reference_order` |
| O3 I.1 untouched | `test_frozen_i1_hash_semantics_are_untouched` |
| O4 cross-store same index_hash | PG `test_index_builds_from_postgres_with_identical_hash_and_freshness` |
| P1–P3 governance coverage | `TestGovernanceCoverage` 3 tests |
| Q1–Q7 model truth | `TestModelTruth` 8 tests |
| R1 no internal body anywhere | `TestInternalMaterial` (harness + stripping) |
| R2 policy untouched | `test_policy_module_is_untouched` (SHA pin) |
| S1 no route | `test_no_route_is_added` |
| S2 no commercial/provider | `test_no_commercial_or_provider_object_is_created` |
| S3 no dependency/migration | `test_no_new_migration` |
| S4 no I.5 behavior | `test_no_route_is_added`, boundary inventory |
| T1/T2 reproducibility, no clock/random | `test_two_builds_are_byte_identical`, `test_report_is_deterministic` |
| U1 cross-store identical hash | PG integration (19 passed) |
| U2 staleness on real PG | PG integration (19 passed) |
| U3 CI green on final head | CI run `37861618933` on `017fc96`: test ✓, postgres ✓ (recorded in RATIFICATION.md post-ratification verification) |
| V1 deny-before-load | instrumented-loader tests (search + navigation) |
| V2 no snippet on denial | `test_denial_never_produces_a_body` |
| V3 quarantine + internal fail closed | quarantine + `TestInternalMaterial` tests |
| V4 no credentials introduced | `test_retrieval_package_has_no_credential_material`, `test_no_credential_material_in_tests_or_sources` |
| W1 regressions green, nothing weakened | gates: I.1 41, I.2 41, II.2 56, II.3 66, II.4 86, I.3 72, service 36, Signal Guard 64 |
| W2 full suite green | 570 passed / 19 skipped (no PG env); 589 / 0 with live PG |
