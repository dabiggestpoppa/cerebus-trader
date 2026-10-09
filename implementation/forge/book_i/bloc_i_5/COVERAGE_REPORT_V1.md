# CEREBUS I.5 Corpus Coverage Report

Deterministic regeneration of the frozen I.5 corpus coverage snapshot.

## Frozen snapshot (I.5 manual audit)

| Dimension | Frozen value |
|---|---|
| Canonical objects | 30 (10 CLAIM, 10 EVIDENCE, 7 MODEL, 3 SETUP, 0 DOCTRINE/TERM/LINEAGE) |
| Source artifacts | 29 |
| Provenance edges | 38 |
| Exposure inventory | PUBLIC_TEACHING 0, SUBSCRIBER_MODEL 24, RESEARCH_LAB 4, OPERATOR_ONLY 2, INTERNAL_METHOD 0, INTERNAL_CODE 0 |
| Quarantined out-of-scope | 9 files (5 setup + 2 Bitcoin + 2 oil; none is a canonical card, term, doctrine, or lineage file) |
| Claims | 10, evidence-linked 10/10; digit-bearing 6, digit-linked 6/6; research-claim layers 6; research-only claims 0; identity gaps 1 (AUC-001 metric NOT_SPECIFIED_IN_SOURCE) |
| Catalog debt | 0 canonical catalog files; DOCTRINE/TERM/LINEAGE compiler = 0 lines |
| Membership | 0 must-exist / 0 must-not-exist (never frozen) |
| Index membership | frozen deliverable: exactly these 30 records |

## Automated corpus counts (regenerated)

- canonical objects: 30 (MODEL 7, CLAIM 10, EVIDENCE 10, SETUP 3)
- exposure inventory: SUBSCRIBER_MODEL 24, OPERATOR_ONLY 2, RESEARCH_LAB 4
- source artifacts: 29
- provenance edges: 38
- quarantined: 9 (canonical-card quarantines: 0)
- claims: 10, evidence-linked 10/10; digit-bearing 6, evidence-linked 6/6
- subscriber-visible records: 24

## Automated checks

- PASS — I.5.1 link integrity (broken parent/related/evidence/provenance or claim route)
- PASS — I.5.2 unsupported number (promoted digit-bearing claim without evidence)
- PASS — I.5.3 status/generation leakage (index vs canonical divergence)
- PASS — I.5.4 exposure leakage (default PUBLIC_TEACHING / internal bodies)
- PASS — Index membership (canonical object absent from index)
- PASS — Quarantine truth (card quarantined / quarantined source in index)

## Findings

None.
