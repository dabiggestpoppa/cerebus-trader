# Book I / Bloc I.2 — Evidence

Status: IMPLEMENTED — TEST EXECUTION RECORDED
Date: 2026-10-06

## Planning identity

- Freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24 (verified ancestor of HEAD)
- Dependency head: Bloc I.1 ratified PASS at aca9438 (evidence 90ccc80)
- Branch: `forge`

## Commit ladder (I.2)

- 9731a86 — PLAN.md
- a2c1488 — ACCEPTANCE.md
- ce2daad — app/forge/provenance.py (implementation)
- 1dde6f6 — tests/test_forge_provenance.py (tests)
- this commit — EVIDENCE.md
- next commit — RATIFICATION.md

## Runtime environment

- Windows 10 (10.0.26200), Python 3.11.9, pydantic 2.13.4, pytest 9.0.3
- Established repository test environment: `.github/workflows/forge-tests.yml`
  (Python 3.11, `pip install -r requirements.txt`, `python -m pytest -q`).
  No new dependency was added; the module imports stdlib + pydantic + app.forge only.
- Executed at branch `forge`, HEAD `1dde6f613467dc95b794b120ab2b8be2955dd5d7`,
  clean working tree.

## Commands executed and exact results

```
$ python -m pytest -q tests/test_forge_provenance.py
.........................................                                [100%]
41 passed in 0.34s

$ python -m pytest -q tests/test_forge_canonical.py tests/test_forge_schemas.py
.........................................                                [100%]
41 passed in 0.37s

$ python -m pytest -q
........................................................................ [ 55%]
..........................................................               [100%]
130 passed in 2.76s
```

- I.2 focused suite: **41 passed**
- I.1 focused suite (regression): **41 passed** — unchanged, not weakened
- Full repository suite: **130 passed** (89 at I.1 ratification + 41 new)
- Failures: 0. Errors: 0. Skips: 0.

## Implementation files

- `app/forge/provenance.py` (718 lines) — ArtifactClass + extensible
  ArtifactClassRegistry; SourceState machine with explicit transition map;
  MaterializationState (derived); deterministic `compute_content_identity` /
  `derive_artifact_id`; Artifact + ArtifactRegistry; ProvenanceRelation +
  ProvenanceEdge + ProvenanceRegistry; SupportClassification + classify_support;
  ClaimChainStatus + claim_source_chain; deterministic ProvenanceAuditReport.
- `tests/test_forge_provenance.py` (729 lines, 41 tests).
- `implementation/forge/book_i/bloc_i_2/PLAN.md`, `ACCEPTANCE.md`.

No existing file was modified for I.2 (`git diff --name-only aca9438..HEAD` is
exactly the four files above). No Signal Guard file changed.

## Source/provenance coverage counts (from test fixtures)

Audit of the primary deterministic fixture (claim CL.EUR.HO.D3_DIRECTION ->
evidence EV.EUR.HO.D3_DIRECTION.V1; artifacts: PDF VERIFIED, VISUAL VERIFIED,
CSV PARTIAL; 3 provenance edges):

```json
{
  "artifact_count": 3,
  "canonical_object_count": 2,
  "provenance_edge_count": 3,
  "source_coverage": {
    "objects_total": 2,
    "objects_with_source": 2,
    "objects_without_source": 0,
    "objects_with_empirical_source": 2
  },
  "artifacts_by_source_state": {"VERIFIED": 2, "PARTIAL": 1, "LOCATED": 0,
    "READ": 0, "MATERIALIZED": 0, "MISSING": 0, "CONVERSATION_DERIVED": 0},
  "orphan_objects": [],
  "evidence_without_source": [],
  "launch_numerical_claims_without_source_chain": [],
  "numerical_claims_non_empirical_source": [],
  "unresolved_sources": [{"artifact_id": "ART.CSV.SAMPLE_TABLE.V1", "source_state": "PARTIAL"}],
  "partial_sources": ["ART.CSV.SAMPLE_TABLE.V1"],
  "conversation_derived_sources": [],
  "historical_unresolved_references": [],
  "visual_only_support": ["CL.EUR.HO.D3_DIRECTION"],
  "conversation_derived_support": [],
  "support_classification_counts": {"EMPIRICAL": 1, "VISUAL_ONLY": 1,
    "NO_SOURCE": 0, "CONVERSATION_DERIVED_ONLY": 0, "MIXED_NON_EMPIRICAL": 0,
    "NOT_YET_READ": 0},
  "gaps": [{"kind": "PARTIAL_SOURCE", "target": "ART.CSV.SAMPLE_TABLE.V1",
    "detail": "explicit unresolved provenance state"}],
  "content_hash": "39c4383b32e67fff16ea135305ef9e2d2e73c7bcef5066bc9a3162f79f8e0f8f"
}
```

Interpretation (honest scope): these are **fixture** counts produced by tests,
not corpus backfill. The real corpus is not yet provenance-backed — that is
Bloc I.3. Notable fixture behaviors proven by tests:

- the visual edge on the claim is reported as `visual_only_support` while the
  claim's chain still resolves only through the evidence's empirical PDF source;
- a claim with no artifact at all surfaces in
  `launch_numerical_claims_without_source_chain` and in `gaps`
  (`test_launch_numerical_claim_without_provenance_is_a_gap`);
- MISSING/PARTIAL/CONVERSATION_DERIVED artifacts always appear in
  `unresolved_sources` and as GAP entries; content identity for MISSING is
  always `None` (never fabricated);
- rebuilding the same fixture in reversed insertion order yields a
  byte-identical `to_json()` and `content_hash` (no timestamps).

## Defects discovered and repairs

- Implementation defects: none found during acceptance execution.
- One test-authoring defect found during the first run of the new suite: the
  conversation-derived test asserted an artifact ID where the report field holds
  canonical object IDs. Classified as **test defect** (wrong expectation, not a
  product defect); repaired in the same uncommitted working tree before the test
  commit `1dde6f6`. No production code was altered to make a test pass, and no
  test was weakened.
- Final runs above are after the repair.

## Migrations

NONE. The fabric is in-memory only; persistence is Book II.

## Security implications

- No secrets, no network I/O, no persistence, no provider/UI imports — enforced
  by `test_provenance_module_has_no_persistence_retrieval_or_provider_imports`
  (module imports limited to stdlib + pydantic + app.forge).
- The audit report exposes only canonical/artifact IDs, states and counts; no
  artifact bytes or corpus content is embedded in report output.
- Retrieval/entitlement filtering and corpus-extraction controls remain Book
  II/VIII scope and are untouched.

## Unresolved provenance gaps

- MISSING, PARTIAL and CONVERSATION_DERIVED sources are explicitly reported as
  gaps by design; I.2 represents them honestly rather than resolving them.
- Historical objects with `allow_unresolved_historical` references are reported
  in `historical_unresolved_references` + `UNRESOLVED_HISTORICAL_REFERENCE`
  gaps instead of being dropped or fabricated.
- No real-corpus provenance graph exists yet (I.3 backfill).

## Known limitations

- Numerical-claim detection is metadata-based (`numerical: true` or a
  non-empty `result`/`statistic` in claim metadata), frozen for I.2; Bloc I.3
  stamps launch claims accordingly.
- `visual_only_support` / `conversation_derived_support` classify an object's
  direct provenance edges; source coverage/orphan detection additionally walks
  typed references (CLAIM -> EVIDENCE -> SOURCE).
- Artifact classes are extensible at runtime; the frozen default set cannot be
  removed or overwritten (asserted by tests).
- Edge relation vocabulary is the six typed provenance relations; concept/model
  lineage remains object->object LINEAGE/CanonicalReference in the I.1 kernel.
- Hand-authored Markdown corpus cards are not parsed by I.2 (unchanged from
  I.1 evidence: models 0/7, evidence 5/10 status-conformant, setups 0/3);
  mapping/backfill is Bloc I.3.

## Acceptance-clause mapping

| Clause | Executable assertion |
|---|---|
| A all default classes registrable with typed IDs | `test_all_default_artifact_classes_register_with_typed_ids` |
| A extensible; duplicates rejected; defaults protected | `test_artifact_registry_is_extensible_and_frozen_defaults_protected`, `test_registered_class_usable_and_unregistered_class_rejected` |
| B identical/different content -> identical/different identity | `test_content_identity_and_derived_ids_are_deterministic` |
| B materialization state derived | `test_materialization_state_derived_from_content_and_source_state` |
| B duplicate artifact identity rejected | `test_duplicate_artifact_identity_rejected` |
| B MISSING carries no content identity | `test_missing_source_cannot_carry_content_identity` |
| C all six relations accepted | `test_valid_provenance_edges_accepted_for_all_relations` |
| C invalid edges/endpoints/duplicates rejected | `test_invalid_provenance_edges_rejected` |
| C chain resolution requires a claim | `test_claim_source_chain_requires_a_claim` |
| D visual never independent empirical proof | `test_visual_support_never_counts_as_independent_empirical_proof` |
| E conversation-derived never empirical / never directly VERIFIED | `test_conversation_derived_source_is_not_empirical_and_never_verifies_directly` |
| F seven states valid; legal/illegal transitions; unknown rejected | `test_legal_source_state_transitions` (9), `test_illegal_source_state_transitions` (5), `test_unknown_source_state_value_rejected`, `test_registry_applies_source_state_lifecycle` |
| F MISSING explicit, recoverable, unfabricated | `test_missing_source_state_is_explicit_and_never_fabricated` |
| F PARTIAL explicit | `test_partial_source_state_reported_explicitly` |
| F historical unresolved stays explicit | `test_historical_unresolved_source_stays_explicit_rather_than_fabricated` |
| G orphan + coverage report | `test_orphan_canonical_object_and_coverage_report` |
| G evidence lacking source | `test_evidence_without_source_reported` |
| G numerical claim without chain -> GAP | `test_launch_numerical_claim_without_provenance_is_a_gap`, `test_claim_without_evidence_reference_is_a_gap` |
| G non-numerical claims not flagged | `test_non_numerical_claim_is_not_treated_as_launch_numerical_claim` |
| G deterministic audit, no timestamps | `test_audit_output_is_deterministic_regardless_of_insertion_order`, `test_audit_report_fields_are_sorted` |
| H artifacts never create Evidence objects | `test_artifact_registry_does_not_create_evidence_objects` |
| H edges never promote status | `test_provenance_edge_never_promotes_canonical_status` |
| H no persistence/retrieval/provider imports | `test_provenance_module_has_no_persistence_retrieval_or_provider_imports` |
| I I.1 suite green | focused 41 passed |
| I full suite green | 130 passed |
| I no test weakened / no Signal Guard file changed / no new dependency | `git diff --name-only aca9438..HEAD` = 4 new files only |
