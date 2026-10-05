# Book I / Bloc I.1 — Evidence

Status: IMPLEMENTED — TEST EXECUTION PENDING
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
