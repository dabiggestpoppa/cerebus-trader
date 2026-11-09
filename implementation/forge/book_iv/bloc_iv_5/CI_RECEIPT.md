# BOOK IV / BLOC IV.5 — CI RECEIPT

**Branch:** `forge`
**Evidence head:** `7ac555ad827b53e9d52cda4c273d835216b17f78`
**Workflow:** FORGE Tests
**Run id:** `42635776090`
**Trigger:** push
**Status:** completed / success

## Jobs

| Job | Result |
|---|---|
| `test` | success |
| `postgres` | success |

## Commit ladder at this head

| Commit | Scope |
|---|---|
| `5baec01` | Rung 1 planning documents (pre-existing) |
| `5d33b82` | 46 Q5 fixtures, builders, generator, SHA-256 manifest |
| `70f318e` | IV.5 answer compiler and validator package |
| `72aa746` | 86 acceptance drivers |
| `7ac555a` | `EVIDENCE.md`, `RATIFICATION.md`, acceptance errata |

## Local reconciliation

| Check | Local | CI |
|---|---|---|
| Full suite | 2461 passed, 29 skipped | `test` job success |
| PostgreSQL job | not run locally | `postgres` job success |
| IV.5 drivers | 86 passed | included in `python -m pytest -q` |

The 29 local skips are the pre-existing PostgreSQL/pgvector-gated tests; the
`postgres` job executes them against a live service. No IV.5 test is skipped.

## Note

This receipt documents the head that contains the complete implementation,
fixtures, tests and ratification documents. The publication of this receipt is
itself a docs-only commit whose own run is verified separately.
