# BLOC III.4 — STATE, PATH & TRANSITION ENGINE — EVIDENCE

**Bloc:** III.4 · **Book:** III
**Authority:** BA-20 Rung 2 (operator-directed implementation)
**Branch:** `forge` · **Planning head:** `7ff238575d2e47428467f91abbf5c983ac1c0498`
**Frozen contract:** `PLAN.md` + `ACCEPTANCE.md` (committed at `7ff2385`,
unmodified by this rung)

This evidence pack records what was implemented, what was measured, what
was refused, and what remains unresolved. It claims no empirical trading
performance, no automation parity and no production readiness.

---

## 1. Scope delivered

| Chapter | Delivered |
|---|---|
| III.4.1 | `snapshot.py` — immutable, versioned `StateSnapshot`; measurement refs; source-output lineage; deterministic hash |
| III.4.2 | `vocabulary.py` — exactly 12 kinds; per-family authority; qualifying prior state; canonical rule; source lineage; ordered injected event time |
| III.4.3 | `delivery.py` — ordered delivery, first-hit side/timing, stable target order, retained both-side sequence, intrabar refusal |
| III.4.4 | `failure_repair.py` — declared grammars only; acceptance→failure→repair→compression→reacceptance; attempt ≠ confirmation |
| III.4.5 | `rekey.py` — structural remapping; prior range closed/replaced; 132-touch refusal; ladder distinct |
| III.4.6 | `handoff.py` — L3→L2→L1 only; typed ownership; no upward laundering; no score; no entry eligibility |
| III.4.7 | `range_left.py` — conditional on consumed events; re-conditioned per event; unconditional frequency refused |
| III.4.8 | `stand_down.py` — six bounded states; bounded reasons; eligibility lock |
| III.4.9 | `history.py` — append-only, gapless, hash-chained; reconstruction; ordered facts |
| III.4.10 | `invariants.py` — path assertions; reversal/order/replay integrity |
| — | `errors.py`, `versions.py`, `__init__.py` — bounded codes, `STATE_ENGINE_V1`, public surface |

Boundaries held: no model interpretation, no measurement re-derivation,
no setup, no execution, no probability/confidence field, no API, no
migration, no provider, no network, no wall clock, no file I/O.

---

## 2. Phase 0 foundation verification

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | `forge` HEAD, remote, ancestry | **PASS** | HEAD = `origin/forge` = `7ff238575d…`; ancestry confirmed |
| 2 | Book I corpus/freeze | **PASS** | `BOOK_I_FREEZE_MANIFEST_V1.md` present, unmodified |
| 3 | Book II 50 hashes + 23 pins | **PASS** | 50/50 re-hashed, 0 mismatches; 23/23 pinned paths present |
| 4 | III.1 11-module baseline | **PASS** | 11/11 unchanged |
| 5 | III.2 12-module baseline | **PASS** | 12/12 unchanged |
| 6 | III.3 13-module baseline | **PASS** | 13/13 unchanged vs `bloc_iii_3/RATIFICATION.md` §3 |
| 7 | III.4 PLAN + ACCEPTANCE published | **PASS** | `7ff2385`, read in full, unmodified |
| 8 | Migrations `[1,2,3,4]` | **PASS** | `discover_migrations()` = `[1,2,3,4]`; no `005_*.sql` |
| 9 | `market_data: NOT_CONFIGURED` | **PASS** | readiness dict identical, `required: False` |
| 10 | Upstream APIs, evidence, cards inspected | **PASS** | `contract.py`, `replay.py`, `registry.py`, `path_metrics.py`, `anchors.py` read; 7 canonical cards; frozen plan |

---

## 3. Clause-to-test traceability

Frozen `ACCEPTANCE.md` section map, all implemented:

| Section | Clauses | Driver |
|---|---|---|
| A | A1–A13 | III.4.1 snapshot |
| B | B1–B16 | III.4.2 vocabulary |
| C | C1–C12 | III.4.3 first delivery |
| D | D1–D12 | III.4.4 failure/repair |
| E | E1–E11 | III.4.5 rekey |
| F | F1–F11 | III.4.6 handoff |
| G | G1–G9 | III.4.7 range-left |
| H | H1–H10 | III.4.8 stand-down |
| I | I1–I11 | III.4.9 history |
| J | J1–J21 | III.4.10 invariants + adversarial matrix |
| K | K1–K7 | Acceptance III.4 |
| L | L1–L7 | Book gate §State/path + final record |
| M | M1–M8 | Failure behaviour |
| N | N1–N24 | Invariants #1–#18 + governance prohibitions |
| O | O1–O7 | Seven model families |
| P | P1–P15 | Gap/authority discipline |
| Q | Q1–Q7 | Authority-model preservation |
| R | R1–R12 | Boundaries/security |

**213 clauses mapped. 155 unique frozen test names, all implemented.
156 executed tests** — one name (`test_first_delivery_order_reversal`) is
referenced by both T3 (C4) and T10 (J7) in the frozen map, so it runs
once per group. Reconciliation is machine-checked: 0 frozen names
missing, 0 implemented names outside the frozen map.

---

## 4. T1–T12 executable results

`python -m pytest tests/test_forge_state_engine.py -q` → **156 passed**.

| Group | Tests | Result | Coverage note |
|---|---|---|---|
| T1 Snapshot | 15 | PASS | immutability, identity versions, layer/state verbatim, injected timestamps, refs, quality, evidence, lineage, hash determinism, prior chaining |
| T2 Vocabulary | 18 | PASS | exact 12; family restriction; no expansion; qualifying prior; rule; materialization; lineage; cross-family; ordered event time; touch; matrix; promotion evidence; invalidation lineage; declared compression; no-op; fail-closed versions; time-alone; event-fact geometry |
| T3 First delivery | 11 | PASS | order, first side/timing, both-side sequence, reversal, stability, ambiguity, bar refs, roundtrip, undeclared target, clock |
| T4 Failure/repair | 10 | PASS | declared-only, full chain, repair-without-failure, failure-without-acceptance, four distinct states, confirmation ≠ new acceptance, no P90 generalization, compression/release guards, XAU evidence link |
| T5 Rekey | 10 | PASS | record completeness, 132-touch refusal, replacement, ladder distinctness, lineage, unresolved anchor, Fib born range, XAU 132↛168, BTC unresolved, ambiguous order |
| T6 Handoff | 11 | PASS | direction, typed ownership, no laundering, L1↛L3, no eligibility, no score, XAU layer isolation, EUR chain, conflict facts, both snapshots, roundtrip |
| T7 Range-left | 8 | PASS | conditioning, per-event updates, unconditional refusal, honest unresolved, consumed-target refusal, BTC slot×tier, exhausted state, native units |
| T8 Stand-down | 10 | PASS | six states, bounded reasons, eligibility block, lock exposure, parked, data-quality, unresolved anchor, evidence-unavailable, family mapping, state-not-erasure |
| T9 History | 11 | PASS | repair replay, append-only, gapless, required fields, reconstruction, facts-not-prose, historical query, order mutation, hash determinism, negative evidence, cross-platform hash |
| T10 Adversarial | 20 | PASS | all 16 required classes plus path invariants (see §4.1) |
| T11 Discipline | 18 | PASS | no eligibility grant, no trading semantics, no performance/probability fields, no setup objects, evidence discipline, no automation field, `MANUAL_OPERATOR` preserved, fixture honesty, bounded labels, no claims, no prediction/signal |
| T12 Boundaries | 14 | PASS | migrations, version stamping, manifest reproduction, import discipline, legacy exclusion, network, I/O/wall clock, composition root, corpus writes, readiness seam, frozen manifests, secrets, determinism, no floats |

### 4.1 Required adversarial classes — all present

Same terminal result/different path (T10) · first-delivery reversal
(T3, T10) · ambiguous intrabar (T3, T10) · touch without acceptance
(T2, T10) · invalid rekey (T5, T10) · repair without prior failure
(T4, T10) · parked XAU promotion (T8, T10) · L1→L3 mutation (T6, T10) ·
BTC Game into Tracker (T10) · JPY equal vote (T10) · missing source
evidence (T2, T10) · nonfinal/poor-quality bars (T10) · historical
version drift (T2, T10) · event-order mutation (T9, T10) ·
non-deterministic replay (T9, T10) · no-go→eligibility leak (T8, T10).

---

## 5. Governed review dispositions

| Review | Clause | Disposition |
|---|---|---|
| Provider/feed failure and stale serving | M7 | **Not applicable at this layer.** III.4 consumes only III.1/III.2/III.3 contract objects; there is no feed path, no provider port and no serving decision. Stale-serving policy remains III.6's. Verified structurally by T12 (no provider/composition-root import, no network). |
| ST/P90 runtime representation | P10 | **Deferred, disclosed.** No canonical MODEL object exists for the manual ST strategy; III.4 carries only the declared EUR Daily P90-merged failure/repair grammar (`EUR_DAILY_P90_FAILURE_REPAIR`) and never promotes it to automation or to another family (T4 asserts the grammar is not generalized; T11 asserts no automation field). Deferral to III.5.9/III.5.10 stands. |

---

## 6. Model-family transition coverage

| Family | Model key | Allowed | Restricted | Unresolved | Enforced prohibition |
|---|---|---|---|---|---|
| EUR Daily | `EUR.DAILY.NEWS_REKEY.V1@PHASE1` | ENTER_STATE, DELIVER, ACCEPT, REJECT, REKEY, FAIL, REPAIR, COMPRESS, RELEASE, INVALIDATE, STAND_DOWN | REKEY, FAIL, REPAIR, COMPRESS, RELEASE | — | event facts never earn geometry (T2); ladder steps stay distinct (T5) |
| EUR Weekly | `EUR.WEEKLY.V1_1@V1_1` | ENTER_STATE, PROMOTE, DELIVER, ACCEPT, REJECT, REKEY, COMPRESS, RELEASE, INVALIDATE, STAND_DOWN | PROMOTE | REKEY, COMPRESS, RELEASE | outer-node promotion only; FROZEN not re-delivered (T2) |
| EUR Higher Order | `EUR.HIGHER_ORDER.V1@V1` | ENTER_STATE, DELIVER, REKEY, COMPRESS, RELEASE, INVALIDATE, STAND_DOWN | — | REKEY, COMPRESS, RELEASE | L1 cannot mutate L3 (T6); statistics never emitted (T8) |
| XAU Game | `XAU.GAME.L1_L2_L3.V1@V1` | ENTER_STATE, PROMOTE, ACCEPT, REJECT, REKEY, FAIL, REPAIR, INVALIDATE, STAND_DOWN | PROMOTE, REKEY, FAIL, REPAIR | — | 132↛168 by declared forbidden pair (T5); parked never promotes (T8, T10); band transitions evidence-linked (T4) |
| BTC Tracker | `BTC.TRACKER.DWM.V1@V1` | ENTER_STATE, DELIVER, ACCEPT, REJECT, REKEY, INVALIDATE, STAND_DOWN | — | REKEY | no PROMOTE/FAIL/REPAIR/compression; Game rule source refuses (T2, T10); daily-only states |
| Fib / Range Birth | `CROSSASSET.FIB.RANGE_BIRTH.V1@R15` | ENTER_STATE, DELIVER, REKEY, INVALIDATE, STAND_DOWN | — | — | `RANGE_ACTIVE` requires a CANONICAL rule (R15 gate); rekey needs a born range (T5) |
| JPY Carry | `JPY.CARRY_GAME.L1_L3.V1@V1` | ENTER_STATE, DELIVER, INVALIDATE, STAND_DOWN | — | — | no ACCEPT/PROMOTE/aggregate; equal-vote impossible (T10); `MANUAL_OPERATOR` preserved (T11) |

Historical generation `JPY.CARRY_GAME.L1_L3.V1@DT_12_4PM` is registered
upstream but declares **no** transition authority — dispatch fails closed
(T2, T10).

---

## 7. Golden fixtures and provenance

Twelve `BLOC_III_4.*.V1` JSON fixtures plus `FIXTURE_MANIFEST.json`,
generated by `generate_fixtures.py` from `_builders.py` (the same module
the suite reproduces with). Manifest: **12/12 hashes reproduce**, 0
mismatches, over LF-normalized content.

Provenance: `SYNTHETIC_FIXTURE` (outputs, snapshots, events, targets,
bars) and `CANONICAL_SOURCE_SLICE` (12-kind vocabulary, family matrix,
EUR ladder, declared grammars, stand-down mapping, evidence ids). No
fixture carries a win rate, expectancy or profit figure; asserted by
`test_no_performance_claims_from_fixtures`.

---

## 8. Replay, reconstruction and determinism

- Three-event EUR ledger (DELIVER `SEED_T1→REKEY_100`, REKEY
  `REKEY_100→REKEY_125`, STAND_DOWN `REKEY_125→INVALID_RANGE`).
- `verify_history` re-derives every event hash and every chain link;
  `history_hash` reproduces exactly (T9).
- `reconstruct_state` replays the ledger and returns the current
  snapshot with its recorded hash (T9 `test_replay_reconstructs_current_state`).
- Reorder → `HISTORY_CHAIN_MISMATCH`; resequence → `HISTORY_SEQUENCE_GAP`;
  rewritten field → `HISTORY_CHAIN_MISMATCH` (T9, T10).
- Reversal paths with identical terminal both-side reach produce
  different path hashes (T3, T10).
- Two independent runs produce identical snapshot and history hashes
  (T9, T12).

---

## 9. Frozen-interface and surface verification

Verified unchanged after the suite (T12):
Book I freeze manifest · Book II 50 contract hashes · 23 planning pins ·
III.1 11 modules · III.2 12 modules · III.3 13 modules ·
migration baseline `[1,2,3,4]` · `market_data: NOT_CONFIGURED`
readiness seam · no corpus/ledger write · no composition-root import ·
no network · no wall clock · no file I/O.

**New baseline recorded for downstream blocs — III.4, 13 modules
(LF-normalized sha256):**

```
__init__.py     6c009b036812b773b97c426919504624fafb0dbdb35bf0ce59326a062aed1fd9
delivery.py     ae912568b577929371573967db4d959290bdd96197ec5b2f58539856bf2c34e5
errors.py       91f14ea70ceb26a5da77555d73a24d0c2d5767e5ee7727d5e281d05bf2ef94d6
failure_repair.py 776de84f6f2fa5bbe324666270dbcedd215d491dc4e5c27737c1ec8db9a4161f
handoff.py      b8e404ed2f5bbaff96e7bdb8a54cf22b5698c16e81eed62f7850378340f0ba1f
history.py      acf2b518458e1dc0f9286de70022b43a7a836c0bc2474ee4f91176adaf6f2b25
invariants.py   891481822db04b1177353669d5879e9bdd64b889de89959d114a295ac0d96a6b
range_left.py   61d0789ed9d324f5b3c003beede8e40b9d67897e961f2c16ec4f410ae10126af
rekey.py        2a9ac377fe47f3521d9fdd0ebfe431570903fac47530bfc55d5a7c71c43aecd7
snapshot.py     5e6d8c0274db6dd46d36be1e2a25c085716d493b5c66bb30bb568ff15b4c96c7
stand_down.py   31ed18dcbb929237b698ea998efeeb668c3cfee5afdd5de52528447ca2571d23
versions.py     af648a64c09a747b5611ddab40c26daeace1725645a0a1717ed5bdd669499ace
vocabulary.py   c5a559d4bb6540d73ccb4af5dd751cfdacd737d364dd48d440cde828c344752d
```

Any modification of these modules requires a new authorization and a new
recorded hash set.

---

## 10. Known-gap dispositions

| Gap | Status at this head | Effect |
|---|---|---|
| III.4-GAP-1 (R15 not materialized) | **OPEN** — `RANGE_ACTIVE` requires `CANONICAL`; declared/unmaterialized rules refuse | Fib production-path transitions blocked; research/unresolved states available |
| III.4-GAP-2 (JPY parity) | **OPEN** — role-separated states only; `MANUAL_OPERATOR` preserved | JPY automation parity blocked; equal vote impossible by construction |
| III.4-GAP-3 (XAU calibration shape) | **OPEN** — promotions/repairs evidence-linked, small-N preserved | no universal promotion rule |
| III.4-GAP-4 (no event calendar) | **OPEN** — event facts cannot earn geometry | no real-history conditioning claims |
| III.4-GAP-5 (HO statistics evidence-bound) | **OPEN** — evidence ids only, never values | no numerical destination statistics |
| III.4-GAP-6 (no real bars) | **OPEN** — synthetic fixtures labelled | no empirical claims |
| III.4-GAP-7 (sessions/parity) | **OPEN** — clock-bound transitions degrade explicitly | no live-feed claims |
| III.4-GAP-8 (BTC weekly/monthly) | **OPEN** — REKEY declared unresolved (`RULE_NOT_MATERIALIZED`) | BTC weekly/monthly remapping blocked |
| III.4-GAP-9 (XAU parked doctrine) | **OPEN** — parked enforced, setup semantics absent | III.5 owns confirmation doctrine |
| III.4-GAP-10 (durable history storage) | **OPEN by design** — logical contract only; no migration | persistence requires a separate packet |
| III.4-GAP-11 (ST/P90) | **OPEN** — deferred to III.5.9/III.5.10 | no ST/P90 transition representation |
| III.4-GAP-12 (bar-granularity bound) | **OPEN** — ordering refuses rather than guesses | no tick-level reconstruction claim |

Carried upstream registers (III.3-GAP-1…10, III.2-GAP-1…6, III.1
GAP-1…5) are unchanged and remain dispositioned in their own packs. No
gap was closed by widening a rule's materialization status.

---

## 11. Defect and repair history (root cause, not test relaxation)

| # | Defect | Root cause | Repair | Tests weakened? |
|---|---|---|---|---|
| D1 | 9 tests raised `AttributeError` for upstream refusal codes | `state_engine/__init__` re-exported only III.4-owned codes, though the engine raises the reused `MODEL_VERSION_UNAVAILABLE`, `RULE_NOT_MATERIALIZED`, `PRIOR_STATE_MISMATCH`, `NO_CALCULATION`, `DATA_QUALITY_BLOCKED` | exported the reused classes on the public surface (no semantic change) | **No** |
| D2 | A family-vocabulary refusal surfaced as `RULE_NOT_MATERIALIZED` for BTC `PROMOTE` | The authority model allowed `unresolved` to be disjoint from `allowed`, conflating "never this family's vocabulary" with "rule missing" | added the invariant **`unresolved ⊆ allowed`** and corrected the BTC/Weekly/Higher-Order declarations; a kind outside `allowed` now refuses as `TRANSITION_NOT_IN_FAMILY_VOCABULARY` | **No** |
| D3 | The canonical EUR L3→L2→L1 chain refused | `build_handoff` required one model key, but those layers are three distinct registered models | replaced model-key equality with **instrument** equality: a handoff may cross model keys, never instruments (calibration stays local, invariant #2) | **No** |
| D4a | Event reorder reported a sequence gap instead of a chain break | `verify_history` checked sequence before chain linkage | reordered to link → sequence → content hash, so each mutation class reports its own refusal | **No** |
| D4b | `explain()` raised the upstream bounded-payload contract error | the fact payload used `str(datetime)` (contains a space) | ISO-8601 formatting (`isoformat()`) for the event-time fact | **No** |
| D5 | `COMPRESS` required both `FAILED` and `REPAIR_ATTEMPTED` | alternatives were modelled as one conjunctive set instead of two alternatives | split into two alternative condition sets (any one suffices) | **No** |
| D6 | `test_confirmed_repair_not_new_acceptance` compressed from the confirmed state | test bug: compression must follow failure/attempted repair | corrected the test to compress from the attempted repair and reaccept from compression | test fixed to match the clause; **engine not relaxed** |

No assertion was deleted, skipped, xfailed or loosened. No runtime rule
was relaxed to obtain a pass; D2 and D3 were genuine design corrections
that made the engine *stricter* and more faithful to the frozen chapters.

---

## 12. Regression and CI

- Focused: `pytest tests/test_forge_state_engine.py -q` → **156 passed**.
- Full repository: `pytest -q` → **1447 passed, 29 skipped** (29
  pre-existing Postgres-gated skips; baseline before this Bloc was 1291
  passed + 29 skipped, i.e. exactly +156 new tests, no regressions).
- Final-head CI: recorded by the closing CI-record commit on `forge`
  (FORGE Tests: `test` + `postgres` jobs).

---

## 13. Ratification recommendation

**Recommend RATIFIED — PASS (CLOSED)** with III.4-GAP-1…12 carried
open and disclosed. All ten frozen chapters, the Acceptance drivers, the
seven family contracts, the carried gap register, the authority-model
preservation rules and the boundary/security surface are implemented and
covered; every refusal is an explicit coded error; no downstream
authority is manufactured.

## 14. III.5 prerequisite-readiness

III.5 (Operator Setup Engine) may proceed on the following bounded
facts only: immutable snapshots, the append-only ledger with
reconstruction, the stand-down **eligibility lock**, conditional
range-left with its conditioning set, and typed layer-ownership markers.
III.5 must not re-derive model interpretation, convert a path event into
a probability, or clear an eligibility lock without a declared transition
of its own. Durable history storage (III.4-GAP-10) remains an open
governed decision.
