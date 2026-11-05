# BOOK III / BLOC III.5 — OPERATOR SETUP ENGINE — RATIFICATION.md

**Bloc:** III.5 · **Book:** III
**Authority:** BA-21 Rung 2
**Base head:** `5fa2502bd5809605c0aeedb7e4dbe0227748df9a`
**Implementation head:** `fec9ba8171f6de788d4f0c5b5126f314b9efcf6a`
**CI at implementation head:** run `42029134502` — success

---

## Verdict

**RATIFIED — PASS (CLOSED) for the III.5 scope.**

All 162 frozen tests pass, repository regression is green, the fixture set
reproduces byte-identically, and no ratified upstream module moved. The
seven III.5 gaps and the three upstream findings recorded in `EVIDENCE.md`
§12–13 are **carried and disclosed**, not closed: the Bloc delivers a
fail-closed engine whose positive verdicts are bounded by what the corpus
actually materialises.

III.6 has **not** been started.

---

## Basis of the verdict

| Requirement | Result |
|---|---|
| Frozen clause map executed, 162/162 names, no skip/xfail/weakening | PASS |
| Bidirectional name reconciliation (0 missing, 0 extra) | PASS |
| Four-valued eligibility total and fail-closed | PASS |
| III.4 stand-down lock binding first-class | PASS |
| Registry-wide `automation_permitted == False` | PASS |
| Trigger downgrade matrix (touch ≠ close ≠ acceptance ≠ rejection) | PASS |
| Invalidation trichotomy non-substitutable | PASS |
| Statistics numeric-free without a `CL.*` claim | PASS |
| 12 fixtures + manifest + baseline, byte-identical regeneration | PASS |
| Frozen upstream hashes 11/12/13/13 unchanged | PASS |
| Boundaries: no network, no clock, no I/O, no provider, no migration | PASS |
| CI green at the implementation head | PASS |

---

## Clause results

| Section | Clauses | Result |
|---|---|---|
| A common contract | 14 | PASS |
| B registry | 16 | PASS |
| C eligibility | 18 | PASS |
| D triggers | 14 | PASS |
| E invalidation | 10 | PASS |
| F targets | 12 | PASS |
| G XAU | 14 | PASS |
| H Fib | 12 | PASS |
| I JPY | 14 | PASS |
| J ST + P90 | 12 | PASS |
| K statistics | 10 | PASS |
| L adversarial | 16 | PASS |
| M acceptance drivers | 8 | PASS |
| N cross-model invariants | 20 | PASS |
| O execution class/ownership | 14 | PASS |
| P gap discipline | 14 | PASS |
| Q authority model | 10 | PASS |
| R boundaries/security | 14 | PASS |
| S fixtures | 8 | PASS |
| **Total** | **250** | **PASS** |

---

## Restrictions proven at this head

1. **XAU** reaches `ELIGIBLE` only with canonically materialised
   `QUARTER_ZONE_MAPPING` and `LADDER_INVALIDATION`; with declared
   parameters it caps at `WATCH`; a blind touch, a parked context, an
   L3-destination-only entry, a lock, or a fired invalidation is
   `BLOCKED`.
2. **Fib** is `RESEARCH_ONLY` end to end: production and operator requests
   are `BLOCKED`; with the R15 rule unmaterialised the anchor gate yields
   `UNRESOLVED`; there is no pivot fallback, no invented anchor and no
   automated signal.
3. **JPY** is `MANUAL_OPERATOR`: roles verbatim, EURJPY is
   confirmation/veto only, equal-vote aggregation is impossible (no
   aggregate field exists), the executed pair needs its own native,
   non-no-go tier.
4. **ST** is a manual historical framework with no `SETUP.*` identity and
   no automation path.
5. **P90** lineages are `UNVERIFIED`; historical statements stay
   `HISTORICAL` and cannot be restated as current.
6. **No execution authority** of any kind is emitted: no order, size,
   allocation, probability, win rate, expectancy or risk/reward.

---

## Carried items (open, disclosed)

* III.5-GAP-1…7 — see `EVIDENCE.md` §13 for dispositions.
* III.5-DEFECT-1 — Book I `SetupOperatorCard`/`CanonicalId` cannot
  represent the three canonical cards (3 validation errors).
* III.5-REC-1 — corpus `SETUP.*` identity carried verbatim instead of
  minting `SET.*`.
* III.5-REC-2 — card status carried verbatim; projection onto
  `EvidenceStatus` is downward-only.
* Upstream gaps III.4-GAP-1…12, III.3-GAP-1…10, III.2-GAP-1…6,
  III.1 GAP-1…5.

---

## Non-authorizations

This record ratifies III.5 only. It does not authorize:

* Bloc III.6 (Intelligence API & Snapshot Service);
* any brokerage, order, sizing or allocation surface;
* persistence or a new migration for setup history (III.5-GAP-6);
* materialising the XAU quarter mapping or ladder invalidation — that is
  a corpus/Book I decision, not a III.5 one;
* modifying Book I's `SetupOperatorCard` to resolve III.5-DEFECT-1.

---

## Evidence of closure

* `pytest tests/test_forge_setup_engine.py -q` → 162 passed.
* `pytest tests/ -q` → 1609 passed, 29 pre-existing skips.
* `generate.py --check` → 12 files byte-identical.
* `EVIDENCE.md` §9 module-hash baseline; §10 frozen upstream integrity.
* CI run `42029134502` (test + postgres) at `fec9ba8`.

---

## CI record

| Head | Workflow run | Result |
|---|---|---|
| `fec9ba8` — implementation (fixtures + engine + suite) | `42029134502` | success |
| `db747f7` — EVIDENCE + RATIFICATION | `42029455159` | success |
| final head — CI record commit | recorded by the run following this commit | — |

A run receipt is a deployment fact, not a substitute for the local
verification recorded above: the 162 focused tests, the 1609-test
regression and the byte-identical fixture check were all executed
locally at every head in this ladder.
