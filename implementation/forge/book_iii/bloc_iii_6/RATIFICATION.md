# BOOK III / BLOC III.6 — RATIFICATION

**Bloc:** III.6 — Intelligence API & Snapshot Service
**Authority:** BA-22 Rung 2
**Verdict:** **PASS / CLOSED** (conditional record; Book III gate remains open)

## Scope ratified

The intelligence API and snapshot service transport the ratified III.1–III.5
facts: snapshot identity, current state, typed levels, path and range-left,
setup context, evidence links, historical replay, multi-model instrument views,
JPY basket views, canonical serialization, two-tier caching and policy-first
authorization.

## Conditions and results

| # | Condition | Result |
|---|---|---|
| 1 | Acceptance contract unchanged: 300 clauses / 258 tests | PASS |
| 2 | Focused suite green, zero skips, zero xfails | PASS — 258/258 |
| 3 | Fixture manifest reproduces byte-identically | PASS — 14/14 files |
| 4 | Frozen upstream hashes unchanged (III.1–III.5, Book II 50/50) | PASS |
| 5 | Full repository regression | PASS — 1867 passed, 29 pre-existing skips |
| 6 | Final-head CI (both jobs) | recorded in `CI_RECEIPT.md` |

## Not ratified

- No API route registration: `app/forge/service/routes.py` is frozen by Book II
  (`145757e0…`), so registration requires separate authorization. The internal
  service and adapter contract are delivered and tested.
- No persistence, migration, provider adapter, deployment or Book IV/V work.
- No Book I schema repair: `SCHEMA_INCOMPATIBLE` remains a governed refusal and
  III.5-DEFECT-1 stays open. `ADR-BOOK-I-001` remains deferred.
- No claim that DTO serialization repairs Book I, that fixtures are market
  intelligence, or that III.6 PASS closes Book III.

## Carried gaps

III.6-GAP-1…8 remain open (see `EVIDENCE.md` §9), plus III.5-DEFECT-1/REC-1/REC-2,
III.5-GAP-1…7, III.4-GAP-1…12, III.3-GAP-1…10, III.2-GAP-1…6 and III.1 GAP-1…5.
No gap closes because a DTO can represent its absence.

## Book III gate

III.6 PASS does not close Book III. The end-to-end gate requires all six blocs,
provider readiness, durable history, consumer contracts and deployment
hardening. Book III end-to-end integration remains **OPEN** and is handed off as
a separate packet. No production GO is claimed. Book IV was not begun.
