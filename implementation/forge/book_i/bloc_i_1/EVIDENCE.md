# Book I / Bloc I.1 — Evidence

Status: TEST EXECUTION RECORDED — EVIDENCE COMPLETE
Date: 2026-10-05

## Planning identity
Freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24

## Commit ladder
- 99c073d7acb1e3ef2c59f84339ec0e2a5f285a8e — PLAN
- 5d66f1855e4e377c497a8dd68332d9742b87dc89 — ACCEPTANCE
- ab7b191d5a27549da17b7f5dd7c570a6a8ca3f61 — app/forge package
- 362e83af6ae69ea105e3bb0f844f3d6fb0c0fc0f — canonical registry kernel
- 3280d19e0228afb7a765bcaddc201c0d0fc80205 — acceptance tests
- 2928ce06eae018ea5ce4bd6392287f26bc2cc405 — FORGE pytest workflow

## Implemented
- typed canonical IDs and prefix/type validation
- immutable Pydantic contracts
- object/status/exposure/layer/setup/evidence enums
- deterministic serialization/SHA-256 content hash
- canonical references
- uniqueness/self-reference/dangling-reference integrity
- explicit historical partial-reference escape hatch
- conservative lifecycle transition validator
- registry status transition preserving identity
- claim comparison identity and PARALLEL behavior

## Test suite added
tests/test_forge_canonical.py covers:
- ID parsing/mismatch/invalid/immutability
- enum rejection
- deterministic hashing
- duplicate/self/dangling/resolved references
- historical partial references
- legal/illegal lifecycle transitions
- identity preservation
- all eight material claim-comparison dimensions.

## Regression isolation
Existing Signal Guard implementation files were not modified.
New runtime code is isolated under app/forge.
No dependency was added; Pydantic and pytest already exist in requirements.txt.

## Test execution status
A GitHub Actions workflow was added to execute:
`python -m pytest -q`

At evidence-write time, GitHub returned no workflow run for commit 2928ce06eae018ea5ce4bd6392287f26bc2cc405. Therefore this evidence record does NOT claim the tests passed.

Local container execution was also unavailable because the runtime could not resolve github.com to clone the repository.

## Ratification decision
NOT YET RATIFIED.

Implementation is present, but the frozen acceptance law requires exact test output. Bloc I.1 must not be marked complete until the suite is executed successfully and the result is appended to this evidence/ratification ladder.

## Known gaps
- Machine-readable specialized Model/Evidence/Setup schemas are intentionally not duplicated in this kernel; their full parsing/backfill belongs to subsequent I.1/I.3 work after the common registry contract is proven.
- Persistence belongs to Book II.
- Relationship-type enum can be tightened when I.2 provenance fabric is implemented.

---

## Test execution — 2026-10-06 (appended; closes the pending test gate)

### Repository truth (Phase 0 verification)

- Working copy: fresh clone of `https://github.com/dabiggestpoppa/cerebus-trader.git`, branch `forge`.
- Branch: `forge`
- HEAD at execution: `e5a3b28cb3f95e44bb89ef778722c14f3a794642` (test-coverage commit `9a7da3a` followed)
- Freeze-head check: `git merge-base --is-ancestor 60e067547b9d9165d94e4f074e0db0ba58e59e24 HEAD` → **true**.
- `git status --porcelain` before any edit → empty (clean tree).
- I.1 commit range `60e0675..e5a3b28` touched only: `.github/workflows/forge-tests.yml`, `app/forge/*`, `tests/test_forge_*`, `implementation/forge/book_i/bloc_i_1/*`, `planning/forge/agents/FIRST_BUILD_AGENT_PROMPT_V1.md`. No pre-existing Signal Guard file was modified.
- CI status: GitHub Actions API (`/repos/dabiggestpoppa/cerebus-trader/actions/runs?branch=forge`) returned **zero** workflow runs, so no remote CI evidence exists. This ratification rests on local executable evidence.
- The surrounding workspace checkout (`larger-lab`, branch `master`) holds unrelated uncommitted work from other threads; it was not modified. Only this clone was added to the workspace.

### Runtime environment

- OS/Python: Windows 10 (10.0.26200), **Python 3.11.9**
- pydantic 2.13.4, pytest 9.0.3, pluggy 1.6.0
- `requirements.txt` satisfied with no new installs: fastapi 0.136.1, uvicorn 0.47.0, pydantic 2.13.4, python-dotenv, PyYAML 6.0.3, pytest 9.0.3, httpx 0.28.1
- Established repository test environment (`.github/workflows/forge-tests.yml`): Python 3.11 → `pip install -r requirements.txt` → `python -m pytest -q`. Local execution used the same command and Python minor version.
- The repository has no `pytest.ini` / `pyproject.toml` / `conftest.py`. Runs were executed from the repository root. Inside this workspace pytest reports a parent-directory `pyproject.toml` as `configfile`, but it defines no `[tool.pytest.ini_options]` and no `conftest.py` exists outside the repo, so collection is cwd-scoped and identical to CI.

### Commands executed and exact results

```
$ python -m pytest -q tests/test_forge_canonical.py tests/test_forge_schemas.py
.........................................                                [100%]
41 passed in 0.39s

$ python -m pytest -q
........................................................................ [ 80%]
.................                                                        [100%]
89 passed in 3.08s
```

- Focused FORGE suite: **41 passed** (35 pre-existing + 6 acceptance-coverage tests added in this pass)
- Full repository suite: **89 passed** (83 pre-existing + 6)
- Failures: **0**. Errors: **0**. Skips: **0**.
- Run before the coverage additions: focused 35 passed, full 83 passed (also zero failures).

### Defects discovered and repairs performed

- Implementation defects: **none**. The kernel, specialized card contracts and registry behavior met frozen acceptance on first execution; no implementation file was changed in this pass.
- Test defect (missing assertions, not failing tests): acceptance clause B3 (frozen registry class set), clause E3 (claim results excluded from population identity), the "enum fidelity to frozen taxonomy" review item and the "no persistence/retrieval/UI/provider leakage inside the kernel" review item had no executable assertion.
- Repair: 6 acceptance-coverage tests added to `tests/test_forge_canonical.py` (commit `9a7da3a`). No existing test was edited, relaxed or removed. Nothing was weakened to reach green.

### Regression tests added (commit 9a7da3a)

1. `test_object_type_covers_frozen_i1_registry_classes` — ACCEPTANCE B3
2. `test_evidence_status_enum_matches_frozen_taxonomy` — enum fidelity vs `corpus/canonical/CEREBUS_CANONICAL_TAXONOMY_V1.md`
3. `test_evidence_type_enum_matches_frozen_taxonomy` — enum fidelity vs taxonomy §12 EVIDENCE
4. `test_exposure_enum_matches_frozen_exposure_rules` — enum fidelity vs `corpus/canonical/PRODUCT_EXPOSURE_RULES_V1.md`
5. `test_claim_population_identity_excludes_result_values` — ACCEPTANCE E3
6. `test_kernel_imports_have_no_persistence_retrieval_or_provider_leakage` — ACCEPTANCE F / kernel isolation

### Corpus card status — measured, NOT claimed as parsed

This bloc validates the **schema contract**. It is not corpus backfill; backfill is Bloc I.3.

A direct probe of the current hand-authored Markdown cards (no machine-readable card fixtures exist under `corpus/`):

| Card set | Cards | `*_id` parses as typed canonical ID | `status` in frozen enum |
|---|---|---|---|
| `corpus/canonical/models/*.md` | 7 | 0/7 (bare IDs e.g. `EUR.DAILY.NEWS_REKEY.V1`, no `MOD.` prefix) | 0/7 (e.g. `CANONICALIZATION_CANDIDATE`) |
| `corpus/canonical/evidence/*.md` | 10 | 10/10 (`EV.*`) | 5/10 (others: `VALIDATED_RESEARCH`, `NEGATIVE_EVIDENCE`, `VALIDATED_RELATIONSHIP`, `VALIDATED_SMALL_N`, `RESEARCH_FLAG_SMALL_N`) |
| `corpus/canonical/setups/*.md` | 3 | 0/3 (`SETUP.*` vs kernel `SET.*`) | 0/3 |

No test claims the Markdown cards parse end-to-end, and none currently do. Card→contract mapping (ID prefixing, status vocabulary mapping, structured field extraction) is I.3 scope. If a mapping would require changing frozen ID/status semantics rather than mapping onto them, that packet must stop for a GAP/ADR.

### Acceptance-clause mapping

| Clause | Executable assertion |
|---|---|
| A valid canonical IDs parse into type + local identity | `test_id_parses_type` |
| A ID prefix/type mismatch fails | `test_id_prefix_type_mismatch_fails`, `test_invalid_id_fails` |
| A canonical identity immutable | `test_identity_is_immutable` |
| A unsupported enum fails | `test_unsupported_enum_fails` |
| B object validates with version/status/exposure/layer | `obj()` construction + `tests/test_forge_schemas.py` (4 tests) |
| B deterministic payload/hash across dictionary order | `test_deterministic_hash_ignores_metadata_dictionary_order` |
| B object type includes frozen I.1 registry classes | `test_object_type_covers_frozen_i1_registry_classes` |
| C registry rejects duplicate IDs | `test_duplicate_id_rejected` |
| C dangling references fail | `test_dangling_reference_rejected`, `test_nonhistorical_cannot_use_partial_escape_hatch` |
| C explicit historical partial references allowed | `test_historical_partial_reference_may_be_explicitly_unresolved`, `test_reference_resolves_when_target_present` |
| C self-reference rejected | `test_self_reference_rejected` |
| D legal promotion/status transitions pass | `test_legal_lifecycle_transitions` (5 cases) |
| D illegal resurrection/promotion fails | `test_illegal_lifecycle_transitions` (4 cases) |
| D SUPERSEDED/FALSIFIED terminal for V1 | `SUPERSEDED→VALIDATED` and `FALSIFIED→CANDIDATE` cases in `test_illegal_lifecycle_transitions` |
| D status transition never mutates identity | `test_registry_transition_preserves_identity` |
| E equal identity dimensions → same population | `test_equal_claim_identity_same_population` |
| E material mismatch → PARALLEL, not contradiction | `test_material_claim_identity_mismatch_is_parallel` (parametrized over all 8 dimensions) |
| E claim values/results not part of population identity | `test_claim_population_identity_excludes_result_values` |
| F existing tests continue to pass | full suite: 89 passed |
| F no existing Signal Guard files changed | `git diff --name-only 60e0675..HEAD` inventory below |
| F no new external dependency | `requirements.txt` unchanged in `60e0675..HEAD`; kernel imports only stdlib + pydantic (asserted) |
| Specialized Model/Evidence/Setup card validation | `tests/test_forge_schemas.py::test_model_card_*`, `test_evidence_card_*`, `test_setup_card_*` |
| No persistence / retrieval / UI / provider behavior in kernel | `test_kernel_imports_have_no_persistence_retrieval_or_provider_leakage` |

### Changed-file inventory (`git diff --name-only 60e0675..HEAD`)

```
.github/workflows/forge-tests.yml
app/forge/__init__.py
app/forge/canonical.py
app/forge/schemas.py
implementation/forge/book_i/bloc_i_1/ACCEPTANCE.md
implementation/forge/book_i/bloc_i_1/EVIDENCE.md
implementation/forge/book_i/bloc_i_1/PLAN.md
implementation/forge/book_i/bloc_i_1/RATIFICATION.md
planning/forge/agents/FIRST_BUILD_AGENT_PROMPT_V1.md
tests/test_forge_canonical.py
tests/test_forge_schemas.py
```

11 files, all within I.1 scope, purely additive (1295 insertions, 0 deletions).

### Known gaps (updated)

- ~~Machine-readable specialized Model/Evidence/Setup schemas absent from the kernel~~ — closed by commits `9ac9608` (`app/forge/schemas.py`) and `84cd5e2` (tests).
- Hand-authored corpus cards do not yet conform to the kernel contract (measured above). Bloc I.3.
- `Layer.NONE` is a kernel-local neutral value for objects without a layer (doctrine/term/lineage); it does not alter frozen L1/L2/L3 semantics.
- Relationship/provenance-relation typing remains open; typed provenance edges are implemented in Bloc I.2.
- Persistence, retrieval, LLM, commerce and UI remain out of kernel scope (Book II and later).
- Remote CI still has no recorded run for this branch; local executable evidence is the record for this ratification.
