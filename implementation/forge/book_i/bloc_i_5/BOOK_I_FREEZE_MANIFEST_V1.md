# BOOK I FREEZE MANIFEST V1

Status: CANONICAL (Book I / Bloc I.5, frozen chapters I.5.7)
Scope: Book I canonical corpus + published retrieval index snapshot.
Written outside `corpus/` so the frozen I.3 inventory is never perturbed.

## Frozen index generation

- generation: 1
- source_fingerprint: 9675431033dd1fa667e3ef3d7ea65526c7bf5a545bf073875af11496236fa226
- index_hash: 28be01dbab570f9391df23540ee0a35618f95ebed5a0e7345094de2e850dac9b
- index records: 30
- quarantined sources: 9

## Corpus counts (I.3 inventory, re-verified by I.5 detectors)

- objects: 30
- artifacts: 29
- edges: 38
- quarantined: 9
- claims: 10
- claims_with_evidence: 10
- digit_claims: 6
- digit_claims_evidence_linked: 6

## Object-type breakdown

- MODEL: 7
- CLAIM: 10
- EVIDENCE: 10
- SETUP: 3
- DOCTRINE: 0
- TERM: 0
- LINEAGE: 0

## Exposure inventory

- PUBLIC_TEACHING: 0
- SUBSCRIBER_MODEL: 24
- RESEARCH_LAB: 4
- OPERATOR_ONLY: 2
- INTERNAL_METHOD: 0
- INTERNAL_CODE: 0

## Schema versions

- CANONICAL_OBJECT_SCHEMA: V1 (RETRIEVAL_OBJECT_SCHEMA_V1)
- CLAIM_IDENTITY: eight-dimension frozen contract (V1)
- ANSWER_CONTRACT: ASK_CEREBUS_ANSWER_CONTRACT_V1
- EXPOSURE_POLICY: PRODUCT_EXPOSURE_RULES_V1 / II.4 policy engine
- PROVENANCE: PROVENANCE_SCHEMA_V1 (I.2)
- TAXONOMY: CEREBUS_CANONICAL_TAXONOMY_V1 (I.1)

## Test counts (recorded at ratification, Phase 13)

- focused I.5 suite: see EVIDENCE.md
- full suite: see EVIDENCE.md

## Known gaps and exclusions (never invented away)

- DOCTRINE / TERM / LINEAGE compiler: 0 lines — no canonical catalog files
  exist; these object types have no compiler path and are declared
  unsupported until a catalog is ratified.
- AUC-001 claim identity gap: metric is `NOT_SPECIFIED_IN_SOURCE` (single
  recorded gap, disclosed by the I.5.2/L detectors as data, not repaired).
- 9 quarantined out-of-scope sources (5 setup, 2 Bitcoin, 2 oil) are absent
  from persistence by construction.
- Membership must-exist / must-not-exist lists were never frozen.
- BTC Game rules are not in the corpus: answers disclose the gap
  (NO_EVIDENCE_REFERENCE) and never invent them.
