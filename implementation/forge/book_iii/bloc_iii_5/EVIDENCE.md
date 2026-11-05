# BOOK III / BLOC III.5 — OPERATOR SETUP ENGINE — EVIDENCE.md

**Bloc:** III.5 · **Book:** III
**Authority:** BA-21 Rung 2 (implementation, acceptance, ratification)
**Base head:** `5fa2502bd5809605c0aeedb7e4dbe0227748df9a` (frozen planning packet)
**Implementation head:** `fec9ba8171f6de788d4f0c5b5126f314b9efcf6a`
**Branch:** `forge` · **Mode:** append-only, evidence-first

---

## 1. Phase 0 — foundation verification

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Local HEAD == `origin/forge` == `5fa2502…` | **PASS** | `git rev-parse HEAD` = `git rev-parse origin/forge` |
| 2 | `825c240` is an ancestor (append-only) | **PASS** | `git merge-base --is-ancestor 825c240 HEAD` |
| 3 | III.1 baseline | **PASS** | `app/forge/market_data/` — 11 modules |
| 4 | III.2 baseline | **PASS** | `app/forge/measurements/` — 12 modules |
| 5 | III.3 baseline | **PASS** | `app/forge/model_runtime/` — 13 modules |
| 6 | III.4 baseline | **PASS** | `app/forge/state_engine/` — 13 modules |
| 7 | Migrations | **PASS** | exactly `001`–`004`; no `005_*` |
| 8 | `market_data: NOT_CONFIGURED` seam | **PASS** | `app/forge/service/health.py` unchanged |
| 9 | Working tree | **PASS** | only `?? .bu_tmp/` before work |
| 10 | Setup engine absent before Rung 2 | **PASS** | `app/forge/setup_engine/` did not exist |

No branch drift; no reconciliation required.

---

## 2. Artifacts delivered

| Path | Content |
|---|---|
| `app/forge/setup_engine/` | 16 modules (PLAN §7.1 inventory, verbatim) |
| `tests/test_forge_setup_engine.py` | 162 frozen tests, T1–T12 |
| `implementation/forge/book_iii/bloc_iii_5/fixtures/` | 12 fixtures + manifest + frozen baseline + builders + generator + README |

No ratified upstream module, migration or planning document was modified.

---

## 3. Clause and test reconciliation (bidirectional)

Machine check, run against the frozen `ACCEPTANCE.md`:

```
frozen: 162 implemented: 162
missing: []
extra: []
```

* **250 clauses** across A–S (A14, B16, C18, D14, E10, F12, G14, H12, I14,
  J12, K10, L16, M8, N20, O14, P14, Q10, R14, S8).
* **162 unique test names**, group counts 16/18/14/10/12/14/12/14/12/10/16/14.
* Zero deleted names, zero renamed names, zero added-but-unmapped tests,
  **zero skipped, zero xfailed, zero weakened assertions** (the suite
  contains no `skip`/`xfail` marker of any kind).

Reconciliation was re-run after every repair; the final run is the one
recorded above.

---

## 4. Gate chain and precedence

`GATE_ORDER` is asserted verbatim:

```
REGISTRY, STAND_DOWN, MODEL_STATE, ANCHOR, TIER, CLOCK,
HIGHER_LAYER, DATA_QUALITY, PARAMETERS, TRIGGER, INVALIDATION
```

Precedence is total and asserted: `BLOCKED(3) > UNRESOLVED(2) > WATCH(1) >
ELIGIBLE(0)`; the result is the most severe gate verdict, and
`evaluate_setup` exposes no verdict parameter, so no caller can set one.
`test_eligible_requires_every_gate` flips nine distinct gates and requires
each to leave `ELIGIBLE` unreachable.

The III.4 lock is invoked first-class through
`assert_setup_eligibility_allowed`; a satisfied trigger under an active
lock is `BLOCKED` (`test_valid_trigger_under_lock_blocked`).

---

## 5. Registry authority matrix

| Setup id | Execution class | Card status (verbatim) | Exposure | Resolution |
|---|---|---|---|---|
| `SETUP.XAU.QUARTER_ZONE.V1` | `MANUAL_OPERATOR` | `CANONICALIZATION_CANDIDATE` | `OPERATOR_ONLY` | operator/production surfaces; `WATCH` at most while parameters are declared |
| `SETUP.FIB.REKEY.V1` | `RESEARCH_ONLY` | `RESEARCH_OPERATOR_CANDIDATE` | `RESEARCH_LAB` | research only; production/operator ⇒ `BLOCKED` |
| `SETUP.JPY.CARRY_ROLE_GATE.V1` | `MANUAL_OPERATOR` | `CANONICALIZATION_CANDIDATE` | `OPERATOR_ONLY` | operator surface; automation ⇒ `BLOCKED` |

`automation_permitted` is `False` for **all three** cards and for every
evaluated record (`test_registry_has_no_automation_approved_card`,
`test_p90_automation_permitted_false_everywhere`). No card is
`AUTOMATION_APPROVED`, so no positive automation verdict is reachable at
this head — by construction, not by convention.

---

## 6. Golden fixtures

12 fixtures + `FIXTURE_MANIFEST.json` + `FROZEN_BASELINE.json` + README.

`generate.py --check` output:

```
fixtures reproduce byte-identically: 12 files
```

Each case is evaluated at generation time and compared with the
expectation declared in `generate.py`; a disagreement aborts generation.
Provenance labels are `SYNTHETIC_FIXTURE` (all instances) and
`CANONICAL_SOURCE_SLICE` (ids, classes, statuses, exposures, trigger
names, evidence/claim ids). No fixture carries a performance figure.

**Honest limit:** a Fib evaluation never reaches `ELIGIBLE` in this
fixture set. An `ACTIVE` anchor requires an earned range, and the R15 rule
is not materialised (III.2-GAP-1); the builder that would have fabricated
one was removed rather than faked.

---

## 7. Adversarial matrix (15 classes, all executed)

| # | Class | Driver |
|---|---|---|
| 1 | touch without required rejection | `test_touch_without_rejection_refused` |
| 2 | valid trigger under a no-go lock | `test_valid_trigger_under_lock_blocked` |
| 3 | L3 direction without L1 eligibility | `test_l3_direction_without_l1_eligibility_blocked` |
| 4 | unresolved R15 requested as production | `test_unresolved_r15_requested_as_production_blocked` |
| 5 | JPY equal-vote / automation request | `test_jpy_equal_vote_request_blocked` |
| 6 | ST automation request | `test_st_manual_framework_cannot_automate` |
| 7 | unsupported P90 performance claim | `test_unsupported_p90_claim_blocked` |
| 8 | stale / nonfinal data | `test_stale_data_request_blocked`, `test_nonfinal_bar_is_data_quality_blocked` |
| 9 | wrong asset tier | `test_wrong_tier_request_blocked` |
| 10 | parked XAU setup | `test_parked_xau_setup_blocked` |
| 11 | missing Setup Card | `test_missing_setup_card_unresolved` |
| 12 | historical/current version drift | `test_version_drift_request_blocked` |
| 13 | unauthorised target promotion | `test_unauthorized_target_promotion_blocked` |
| 14 | ambiguous intrabar first delivery | `test_ambiguous_intrabar_first_delivery_blocked` |
| 15 | model state serialised as a trade signal | `test_model_state_serialized_as_signal_refused` |

---

## 8. Defects found during implementation and their repairs

No defect was closed by weakening a test or widening a status.

| # | Defect | Root cause | Repair |
|---|---|---|---|
| D1 | Card source refs rejected | identifier pattern excluded `#` (`…#Entry`) | bounded pattern widened to include `#`; still prose-impossible (no spaces) |
| D2 | Invalidation gate raised `unknown invalidation kind` | card kinds are strings, resolver expects the enum | gate converts through `InvalidationKind` |
| D3 | Target promotion accepted an unrecorded transition when no transitions were supplied | empty "known" set skipped the check | promotion now refuses unless the transition is among the recorded transitions |
| D4 | JPY local geometry never resolved | matched `pair in model_id` instead of the pair's instrument identity | matches `identity.instrument_id` |
| D5 | ST explanation fact rejected by III.3 fact grammar | payload used `TIER->AU->TIER`, `>` is outside the bounded value pattern | encoded as `TIER_TO_AU_TO_TIER` |
| D6 | Repository regression failed at collection (III.4 test imported the wrong `_builders`) | the III.5 suite put its fixtures dir on `sys.path` | builders loaded by explicit path under the unique module name `bloc_iii_5_builders`; fixtures dir never enters `sys.path` |
| D7 | Frozen baseline recorded zero modules | generator root depth off by one | root corrected; baseline regenerated |
| D8 | Two assertions could have passed for the wrong reason | after-03:00 case used a matching checkpoint with a foreign session; intrabar case used a single unambiguous target | corrected to genuine shapes (`BEFORE_0300_NY`; two simultaneous deliveries with ordering unresolved) |

D6 is the reason repository-wide regression was run before committing:
the focused suite alone was green.

---

## 9. New III.5 module hash baseline (sha256, prefix)

| Module | sha256 |
|---|---|
| `__init__.py` | `c6b33adefe202ac1…3d5874c4` |
| `contracts.py` | `eea1d93a36813e9d…92f79bc6` |
| `eligibility.py` | `61884ef141d2c4b7…e7eb52b8` |
| `errors.py` | `6ee335afc459ced7…aad7a2b7` |
| `fib_rekey.py` | `7ce90a5545695f4e…22d2a18d` |
| `invalidation.py` | `a62cbbb6ca60153b…ff322fd0` |
| `invariants.py` | `9237e20e5909699a…ed0b46b5` |
| `jpy_role_gate.py` | `045192ecc65594b7…ef680726` |
| `p90_lineage.py` | `38ecb316e7cbffd2…63d25a02` |
| `registry.py` | `1b900b6b93b9df6c…10999807` |
| `st_manual.py` | `fd641a2e379cc297…2bc7c5d4` |
| `statistics.py` | `a44d53e16e110515…80f68017` |
| `targets.py` | `a2df0d98c822be20…78a95920` |
| `triggers.py` | `d6fc6c54f0809f6b…3f8a9900` |
| `versions.py` | `11657107b72afb73…52a7bee6` |
| `xau_quarter_zone.py` | `4c0a6c8ba6c5d4ff…604192a8` |

Any future change to these modules requires a new recorded baseline.

---

## 10. Frozen upstream integrity

`FROZEN_BASELINE.json` pins every module of the four ratified packages;
`test_frozen_upstream_hashes_unchanged` recomputes them at test time.

Counts asserted: `market_data` 11, `measurements` 12, `model_runtime` 13,
`state_engine` 13. Import direction is one-way
(`test_import_direction_is_one_way`): no upstream module mentions
`setup_engine`, and the package imports only the five allowed upstream
roots.

---

## 11. Verification runs

| Run | Command | Result |
|---|---|---|
| Focused | `pytest tests/test_forge_setup_engine.py -q` | **162 passed** |
| Full regression | `pytest tests/ -q` | **1609 passed, 29 skipped** |
| Fixtures | `generate.py --check` | **12 files byte-identical** |
| CI (implementation head) | run `42029134502` on `fec9ba8` | **success** |

The 29 skips are pre-existing repository skips; the III.5 suite contains
no skip or xfail, so none of them belongs to this Bloc.

---

## 12. Findings that require operator attention

These are upstream truths discovered while implementing, not III.5
changes. All are carried, none is closed, and none was worked around by
inventing identity or parameters.

| Id | Finding | Consequence |
|---|---|---|
| **III.5-DEFECT-1** | Book I's `SetupOperatorCard` cannot validate **any** canonical Setup Card — 3 validation errors: `setup_id` (`SETUP.*` fails `CanonicalId`'s `SET.` prefix rule), `status` (`CANONICALIZATION_CANDIDATE` / `RESEARCH_OPERATOR_CANDIDATE` are not `EvidenceStatus` members), `parent_model_ids` (`XAU.GAME.L1_L2_L3.V1` is not `MODEL.`-prefixed) | The machine card contract and the corpus cards are inconsistent. III.5 loads card descriptors in code and validates identity against the frozen three-card set instead of minting ids. |
| **III.5-REC-1** | Clause A2's literal `SET.*` form is unsatisfiable with corpus ids | The engine carries `SETUP.*` verbatim and admits only the three canonical ids — narrower than a prefix test. Disclosed rather than silently renamed. |
| **III.5-REC-2** | Card lifecycle status vocabulary (16 values) is broader than `EvidenceStatus` (14) | `CardStatus` carries the verbatim value; projection onto `EvidenceStatus` is **downward only** (`CANONICALIZATION_CANDIDATE → CANDIDATE`) and used solely for refusal classification. |

---

## 13. Gap dispositions (III.5-GAP-1…7, all carried)

| Gap | Disposition at this head |
|---|---|
| III.5-GAP-1 quarter-zone mapping uncanonicalised | **OPEN.** XAU caps at `WATCH` unless a canonical `QUARTER_ZONE_MAPPING` binding is supplied; no numeric zone is invented. |
| III.5-GAP-2 no canonical ST/P90 Setup Card | **OPEN.** ST is a manual framework with `setup_identity = None`; P90 is an `UNVERIFIED` lineage. No `SETUP.*` id minted. |
| III.5-GAP-3 XAU ladder invalidation uncanonicalised | **OPEN.** Price invalidation is `DECLARED` (5-point ladder / 80-family structural); verdict capped. |
| III.5-GAP-4 trigger observation vocabulary absent from measurement layer | **OPEN.** The matching contract exists and refuses blind touch; observations must come from a governed source. |
| III.5-GAP-5 no canonical setup statistics | **OPEN.** `statistics.py` exposes no numeric result type; a statement requires a `CL.*` claim and matching population. |
| III.5-GAP-6 setup/registry durability undecided (inherits III.4-GAP-10) | **OPEN.** No persistence, no migration. |
| III.5-GAP-7 no live/feed parity | **OPEN.** Every lineage is `UNVERIFIED`; automation stays `False` registry-wide. |

Carried upstream gaps are unchanged: III.4-GAP-1…12, III.3-GAP-1…10,
III.2-GAP-1…6, III.1 GAP-1…5.
