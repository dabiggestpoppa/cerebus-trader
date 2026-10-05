# Book I / Bloc I.1 — Canonical Registry Kernel Implementation Plan

Status: ACTIVE
Planning freeze: 60e067547b9d9165d94e4f074e0db0ba58e59e24

## Scope
Implement the smallest Python kernel that gives FORGE stable canonical object identity, controlled enums, references, lifecycle validation and claim conflict identity.

The existing Signal Guard application remains untouched except for adding the new isolated `app/forge` package and tests.

## Reuse
Source contracts:
- corpus/canonical/CEREBUS_CANONICAL_TAXONOMY_V1.md
- corpus/canonical/schemas/MODEL_CARD_SCHEMA_V1.md
- corpus/canonical/schemas/EVIDENCE_CARD_SCHEMA_V1.md
- corpus/canonical/schemas/SETUP_OPERATOR_CARD_SCHEMA_V1.md
- corpus/canonical/RETRIEVAL_OBJECT_SCHEMA_V1.md
- corpus/canonical/CLAIM_REGISTRY_V1.md

Runtime baseline: Python 3.11, Pydantic >=2 already in requirements.

## Deliverables
1. `app/forge/__init__.py`
2. `app/forge/canonical.py`
3. `tests/test_forge_canonical.py`
4. evidence and ratification artifacts in this folder.

## Kernel contract
- Stable typed IDs for MODEL/CLAIM/EVIDENCE/SETUP/DOCTRINE/TERM/LINEAGE/ARTIFACT.
- Controlled object/status/exposure/layer/setup/evidence enums.
- Immutable canonical identity.
- Reference records with explicit partial/historical allowance.
- Registry uniqueness and dangling-reference validation.
- Lifecycle transition validation.
- Claim comparison identity sufficient to decide comparable vs parallel claims.
- Deterministic serialization/hash.

## Non-goals
No persistence, database, FastAPI route, retrieval embeddings, live market data, LLM, Whop, UI, trading execution or corpus backfill.

## Implementation sequence
1. Freeze acceptance tests.
2. Implement enums/ID/object contracts.
3. Implement references/registry.
4. Implement lifecycle.
5. Implement conflict identity.
6. Run tests.
7. Write evidence/ratification.

## Stop conditions
Stop and write a GAP/ADR if implementation requires changing the frozen taxonomy, collapsing object classes, or creating schema exceptions for the kernel contract.
