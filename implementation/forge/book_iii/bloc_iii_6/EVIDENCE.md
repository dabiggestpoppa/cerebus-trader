# BOOK III / BLOC III.6 — EVIDENCE

**Bloc:** III.6 — Intelligence API & Snapshot Service
**Authority:** BA-22 Rung 2 (implementation, acceptance, ratification)
**Starting head:** `3439a8c22c79555763ebf393925d22ad2d8e6060`
**Mode:** append-only, evidence-first

## 1. Phase 0 verification

| # | Check | Result |
|---|---|---|
| 1 | local HEAD == `origin/forge` == `3439a8c` | PASS |
| 2 | `5fa2502`, `825c240`, `d74f10a` ancestry | PASS |
| 3 | Book I corpus and freeze manifest present | PASS |
| 4 | Book II 50/50 contract hashes | PASS (0 mismatches) |
| 5 | 23/23 planning pins | PASS |
| 6–10 | III.1 11, III.2 12, III.3 13, III.4 13, III.5 16 modules | PASS |
| 11 | III.5 RATIFIED PASS (CLOSED), 162/162 | PASS |
| 12 | migrations `001`–`004` only | PASS |
| 13 | `market_data: NOT_CONFIGURED` unchanged | PASS |
| 14 | Book II service/policy/identity/error interfaces inspected | PASS |
| 15 | starting-head CI `42043536875` | success |

Frozen-surface finding: `app/forge/service/routes.py` is **inside** the Book II
freeze manifest (`145757e0…`). Under Ruling C it was **not** modified; the
internal service and route-adapter contract were implemented instead and the
registration remains blocked pending separate authorization.

## 2. Implemented modules

`app/forge/intelligence_api/` — 14 modules:

| Module | Responsibility |
|---|---|
| `versions.py` | API/schema versions, views, 18-code refusal vocabulary |
| `errors.py` | `RefusalError`/`SchemaIncompatibleError`, Book II error mapping |
| `serialization.py` | canonical JSON, Decimal text, float refusal, bounded response |
| `contracts.py` | immutable key/sections/envelope/views |
| `identity.py` | derived `snapshot_id`, ordered component hashes |
| `composition.py` | pure composer over III.1–III.5 facts |
| `requests.py` | five typed request families, forbidden-field refusal |
| `freshness.py` | quality/version/cutoff/staleness semantics |
| `policy_gate.py` | policy-first gateway, cache after allow |
| `history.py` | retained-input replay under pinned versions |
| `cache.py` | two-tier cache, bounded deterministic eviction |
| `refusals.py` | governed refusals, card machine-validity probe |
| `views.py` | layer-preserving instrument and JPY basket views |
| `__init__.py` | bounded public surface |

Routes: none registered. The adapter contract is
`IntelligenceGateway.read / read_historical / instrument_view / basket /
setup_context`, callable from a future router once Book II authorization exists.
No upstream module imports this package; no Book I, II or III.1–III.5 file was
modified.

## 3. Snapshot identity

Key = instrument, model id/version, layer, `as_of`, data cutoff, calculation
version, clock id, session id. `snapshot_id = "SNAP." + sha256(key payload)[:40]`.
Snapshot hash covers the whole canonical payload except projection labels
(`view`, `view_label`), so a pinned historical replay reproduces the recorded
hash. Principal identity is absent from the key and from the payload.

Same-input composition is byte-identical; changing model version, cutoff, clock,
session or a material source digest changes the derived id and is never served
from an older entry.

## 4. Acceptance traceability

`ACCEPTANCE.md` is unchanged: **300 clauses** (A–T) and **258 executable test
names** (T1–T14). Reconciliation is executed inside the suite
(`test_final_test_counts_recorded`): 258 unique test functions across 14 groups
and 300 clause lines. Frozen names missing = 0; unauthorized omissions = 0;
skipped = 0; xfailed = 0; unmapped clauses = 0.

## 5. Measured results

| Check | Command | Result |
|---|---|---|
| focused suite | `python -m pytest tests/test_forge_intelligence_api.py -q` | **258 passed**, 0 skipped, 0 xfail |
| full regression | `python -m pytest -q` | **1867 passed, 29 skipped**, exit 0 |
| fixture reproduction | `python implementation/forge/book_iii/bloc_iii_6/fixtures/generate.py --check` | `fixtures reproduce byte-identically (14 files)` |

The 29 skips are pre-existing provider/environment skips in earlier blocs; no
III.6 test is skipped.

## 6. Behaviour verified

- Deterministic payload per identity; two compositions produce identical bytes.
- Current vs historical views distinguished; the recorded hash is stable across
  the projection label, and a replayed hash is checked against its identity.
- L3/L2/L1 ownership preserved in the instrument view; conflicts reported as
  facts, never averaged.
- JPY basket carries per-pair roles; `EURJPY` is confirmation/veto only; equal
  vote and flattening are refused.
- Policy denies before composition (spy loader proves zero invocations); cache
  hits still require a fresh II.4 decision; caches never cross principals; a
  denied read stores nothing reusable.
- Provider-not-configured, blocked quality, non-final bar, unresolved clock,
  mixed cutoff, version drift and missing history are distinct governed
  outcomes; no staleness threshold is invented.
- Setup context preserves the four-valued verdict, exposure, execution class
  and automation prohibition; research/manual surfaces refuse production or
  automation projection.
- Book I card defect reproduced on all three cards: exactly three machine
  failures each (`setup_id`, `status`, `parent_model_ids`). Served verbatim;
  strict projection returns `SCHEMA_INCOMPATIBLE`.

## 7. Golden fixtures

Twelve deterministic fixtures under
`implementation/forge/book_iii/bloc_iii_6/fixtures/`, generated by
`generate.py`, hashed in `FIXTURE_MANIFEST.json`, with upstream module counts and
aggregate hashes in `FROZEN_BASELINE.json`. Regeneration is byte-identical and
LF-normalised. Fixture expectations are declared independently of the library
and asserted in the suite.

Cases: consistent EUR snapshot; model-only/no eligible setup; active stand-down
lock; missing provider; data-quality failure; research-only Fib; manual JPY;
XAU `WATCH`; historical model-version mismatch; setup-card schema
incompatibility; restricted exposure; deterministic historical reconstruction.

## 8. Root-cause repairs during this rung

| Defect found by the suite | Root cause | Repair |
|---|---|---|
| calculation timestamp equalled `as_of` | fixture clock collided with the cut | fixture `CALC_TS` moved to `00:05Z` |
| replay hash mismatch | component hashes included the `view_label` projection | component and payload hashes computed over view-neutral content |
| historical evidence still labelled current | direct `inputs.evidence` bypassed the requested view | composer relabels retained links to the requested view |
| unknown model generation collapsed to "unavailable" | identity lookup failed before generation comparison | same pinned key with a different version now returns `VERSION_DRIFT` |
| automation refusal crashed on manual cards | registry field is a property, not a method | guarded read accepts bool or callable |
| cache-hit policy test saw zero audit records | helper built a fresh gateway per call | shared gateway plus explicit injection in isolation tests |
| boundary test flagged the package's own `requests` module | naive substring token match | narrowed to real transport imports |
| policy test imported a non-existent class name | Book II exposes `ResourcePolicyMetadata` | corrected import |
| ambiguous path assertion was vacuously true | builder cleared the resolvability flag but never set ambiguity | builder marks the path ambiguous explicitly |

No test was weakened to obtain green: every repaired assertion was replaced by a
stronger or more precise statement of the same frozen clause.

## 9. III.6-GAP dispositions

| Gap | Disposition | Affects |
|---|---|---|
| III.6-GAP-1 no durable snapshot/history store | OPEN — retained-input replay only, no migration | Book III integration, beta, production |
| III.6-GAP-2 provider not configured | OPEN — `PROVIDER_NOT_CONFIGURED` governed refusal; no live claim | Book III integration, beta, production |
| III.6-GAP-3 Book I Setup Card schema defect | OPEN — verbatim DTO + `SCHEMA_INCOMPATIBLE`; `ADR-BOOK-I-001` deferred | Book III integration, beta, production |
| III.6-GAP-4 no versioned staleness threshold | OPEN — timestamps carried, staleness unresolved, no invented threshold | beta, production |
| III.6-GAP-5 no canonical confluence model | OPEN — no score or probability emitted | Book III integration, beta |
| III.6-GAP-6 no stable entitlement fingerprint | OPEN — recompute/refuse rather than invent a hash | beta, production |
| III.6-GAP-7 Book IV/V consumers absent | OPEN — transport contract only | Book III integration |
| III.6-GAP-8 Book VIII transport hardening incomplete | OPEN — no deployment or exposure | beta, production |

Also carried open: XAU materialisation (maximum `WATCH`), Fib R15 production
eligibility, JPY automation parity, BTC weekly/monthly anchors, ST/P90
historical/manual restrictions, and all III.1–III.5 registers. No gap is closed
by the API being able to represent it.

## 10. Book III end-to-end gate

Lineage evidence inside III.6 is structural: the composer consumes ratified
observation → measurement → model → transition → setup → snapshot facts and
re-projects them deterministically, with policy applied before any load. The
cross-bloc gate additionally requires a configured provider, a retained history
store, consumer contracts and transport hardening, none of which exist.

Verdict: **III.6 PASS/CLOSED; Book III end-to-end gate OPEN.** A dedicated Book
III integration packet is required. No production GO is claimed and Book IV was
not begun.
