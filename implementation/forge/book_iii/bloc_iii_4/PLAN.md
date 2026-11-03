# BOOK III / BLOC III.4 — STATE, PATH & TRANSITION ENGINE — PLAN.md

Status: **PLANNING ONLY — committed before any implementation** (frozen
Book II/III.1/III.2/III.3 order rule reused: PLAN + ACCEPTANCE are
committed first; no implementation is authorized by this packet).
Date: 2026-11-03
Branch: `forge` · Planning head: `2bd48917f969d57770516a039788ddc902a70a34`
(= `origin/forge`; no advancement to reconcile)
Authority: BA-20 Rung 1 (operator-directed planning)
Frozen source: `planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(pinned in `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` line 35, commit
`3eb91e2b289dc2fbbf0dd0019a3fbd20f524dbf5`) — sections `# BLOC III.4` (Ch
III.4.1–III.4.10 + Objective + Acceptance III.4), `# BOOK III CROSS-MODEL
INVARIANTS`, `# BOOK III GOLDEN FIXTURE PROGRAM`, `# BOOK III FAILURE
BEHAVIOR`, `# BOOK III ACCEPTANCE / RATIFICATION GATE` §State/path +
final-record fields, `# BOOK III EXCLUSIONS`, `# RECOMMENDED
IMPLEMENTATION ORDER` step 5.

Scope here is exactly the frozen Bloc III.4 chapters. No Book III scope
is inferred from the Book title, and no cross-Bloc work is reopened: Book
I, Book II and Blocs III.1–III.3 are ratified and closed, and nothing in
this packet re-derives, redesigns or repeats them.

**A transition is an earned state change under a canonical rule. A
terminal outcome must never erase how the market arrived there.**

---

## 1. Governing authority model (mandatory, restated)

These distinctions govern every design decision in this Bloc and are
re-verified in `ACCEPTANCE.md` §Q:

- **Observation → Measurement → Model interpretation → State transition
  → Governed setup eligibility.** No stage inherits the authority of the
  next. III.4 owns *transition facts only*: it may not re-measure, may
  not re-interpret, may not grant setup eligibility.
- **Measurement ≠ interpretation ≠ path ≠ eligibility.** III.4 consumes
  III.3 `ModelOutput` facts read-only. The core law applies in both
  directions: III.4 may consume III.3 state, never silently redefine it —
  and III.3/III.2 may never be reached *backwards* from III.4 (no
  retro-fit of a transition to justify an upstream output).
- **Model state ≠ trade eligibility** (invariant #12). Every III.4
  artifact carries the upstream `production_authorization`
  *classification* verbatim; III.4 defines no field that confers trade
  eligibility. Setups are III.5's; snapshots/APIs are III.6's.
- **Touch ≠ acceptance** (invariant #6). A `TOUCHED` fact is never
  coerced into an `ACCEPT` transition; acceptance requires the declared
  canonical acceptance evidence.
- **Reach ≠ trade win** (invariant #7). Delivery/path events are
  structural facts. No win rate, expectancy, RR or probability may be
  derived from path events, in either direction.
- **First delivery/path can matter more than terminal both-side reach**
  (invariant #8). Terminal both-side reach must not erase first-delivery
  sequence.
- **Rekey is a remapping transition** (invariant #9), never "price
  touched a number".
- **Range-left updates conditional opportunity after states are
  consumed** (invariant #10); an unconditional historical frequency is
  never substituted for conditional remaining opportunity.
- **L3 destination ≠ L2 path ≠ L1 entry** (invariant #11). No upward
  probability laundering; no automatic entry eligibility; no monolithic
  confluence score.
- **Historical observation ≠ current state**, and **simulation ≠
  empirical performance**. Golden-fixture reproduction is a
  deterministic contract test over committed (mostly synthetic) inputs —
  never empirical or performance evidence.
- **Manual strategy validity ≠ automation parity** (invariant #14). JPY
  `MANUAL_OPERATOR` and Fib `RESEARCH_ONLY` classifications travel
  unchanged; III.4 never promotes them.
- **No-go cannot silently become executable eligibility.** A stand-down
  state is a stateful output with a reason, and it *locks* eligibility
  downstream.
- **No deterministic rhetoric in runtime status labels** (invariant #18):
  all labels are bounded enums and typed facts, never prose.

## 2. Scope (frozen chapters, in)

| Ch | Frozen requirement (compressed; frozen plan is authority) |
|---|---|
| III.4.1 | **State snapshot.** Immutable/versioned snapshot: model, layer, timestamp, active state, measurements, active levels, quality, claim/evidence refs. |
| III.4.2 | **Transition vocabulary.** At minimum `ENTER_STATE`, `ACCEPT`, `REJECT`, `FAIL`, `REPAIR`, `PROMOTE`, `DELIVER`, `REKEY`, `INVALIDATE`, `COMPRESS`, `RELEASE`, `STAND_DOWN`. Models may restrict vocabulary. |
| III.4.3 | **First-delivery engine.** Track ordered target/state delivery; both-side hit without order is insufficient when the model depends on first delivery. |
| III.4.4 | **Failure/repair grammar.** Support canonical failure paths (e.g. historical P90/structural: valid acceptance → failure → midpoint repair → compression/reacceptance/opposite acceptance) **only** for models/generations that declare it. |
| III.4.5 | **Rekey.** A structural remapping/state transition, not "price touched 132". Store prior range/state → rekey event → new active mapping/eligibility. |
| III.4.6 | **Layer handoff.** Formal L3 destination context → L2 path/opportunity → L1 execution eligibility. No upward probability laundering. |
| III.4.7 | **Range-left.** Represent remaining distribution conditioned on what has already occurred; do not keep quoting unconditional target reach after states are consumed. |
| III.4.8 | **No-go/stand-down.** A stateful output with a reason: range too large, data bad, anchor unresolved, conflicting model rule, exhausted/parked state, insufficient evidence where required. |
| III.4.9 | **Transition history.** Persist the transition sequence enough for operator explanation, replay, research analysis and historical state questions. |
| III.4.10 | **Path invariants.** Terminal outcome cannot erase path; target order stable; rekey closes/replaces mapping according to model; no-go prevents setup eligibility; L1 cannot mutate L3 state. |
| Acceptance III.4 | Path replay reconstructs current state; first-delivery order preserved; rekey is an explicit transition; no monolithic confidence score appears unless a future canonical model explicitly defines one. |

Plus the applicable cross-model invariants (frozen #1–#18, especially
#6–#11 and #18), the Book III golden-fixture requirements for
state/path, the `# BOOK III FAILURE BEHAVIOR` clauses landing on this
layer, gate §State/path, gate §Evidence pack, and the final-record field
III.4 owns (**golden fixture hashes** for its own fixture set, plus its
**test counts** contribution, and its contribution to **unresolved
research gates**). III.4 also owns the *runtime version identity* that
Book III's final record will cite for the transition layer
(`STATE_ENGINE_V1`), recorded as a proposed field only.

## 3. Scope exclusions (out — never in this Bloc)

- **No model interpretation.** No re-evaluation of a family rule, no
  recomputation of a III.2 measurement, no subclassing of `Measurement`
  or `ModelOutput`, no re-derivation of tier/calibration/anchor/session
  logic. If a fact is not in a III.1/III.2/III.3 contract object, III.4
  refuses — it never fills the hole.
- **No setup engine.** No eligibility grant, no trigger, no entry, no
  invalidation-as-setup, no target selection, no position sizing, no
  execution. III.5 owns setups; III.4 may only *carry* the fact that a
  stand-down state blocks downstream eligibility.
- **No API/service surface.** No endpoints, no snapshot service, no
  caching, no multi-model view. III.6 owns the API.
- **No persistence migration.** No SQL schema, no new migration version
  (baseline `[1, 2, 3, 4]` stays). Durable *design* of history records is
  planned here; a storage decision (if any) is a separate governed
  packet.
- **No providers, no network, no wall clock, no file I/O** in the
  package. Time is injected.
- **No probability/confidence/confluence** field anywhere; no
  `latest()`-style implicit resolution; no default versions.
- **No implementation, tests, fixtures, generators or code** in this
  rung. This packet is PLAN + ACCEPTANCE only.
- **No trading/game concepts as package identifiers.** Canonical
  corpus vocabulary (`XAU.GAME.L1_L2_L3.V1`, `JPY.CARRY_GAME.L1_L3.V1`,
  BTC `trigger_levels`) is passed as *data* and disclosed exactly as
  III.2/III.3 disclosed it — it is never mirrored into new identifiers.

## 4. Phase 0 foundation verification (verified at this head)

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Local HEAD equals `origin/forge` | **PASS** | `git rev-parse HEAD` = `git rev-parse origin/forge` = `2bd48917f969d57770516a039788ddc902a70a34`; branch `forge`; no advancement |
| 2 | Book I corpus/freeze integrity | **PASS** | `implementation/forge/book_i/bloc_i_5/BOOK_I_FREEZE_MANIFEST_V1.md` present and unmodified; Book I `RATIFIED (CLOSED)` |
| 3 | Book II 50/50 frozen hashes + 23/23 planning pins | **PASS** | 50 manifest pairs re-hashed: **0 mismatches**; 23 commit pins parsed: **23/23**, all pinned paths present |
| 4 | III.1 11-module interface baseline | **PASS** | 11/11 LF-normalized sha256 identical to the recorded baseline (§6.1) |
| 5 | III.2 12-module interface baseline | **PASS** | 12/12 identical (§6.2) |
| 6 | III.3 13-module baseline + PASS/CLOSED | **PASS** | 13/13 identical to `bloc_iii_3/RATIFICATION.md` §3 (§6.3); verdict `RATIFIED — PASS (CLOSED)` |
| 7 | Migration baseline `[1,2,3,4]` | **PASS** | `discover_migrations()` → `[1, 2, 3, 4]`; no `005_*.sql` |
| 8 | `market_data: NOT_CONFIGURED` seam unchanged | **PASS** | `as_readiness_dependencies()["market_data"]` = `{status: NOT_CONFIGURED, required: False, note: market-data providers belong to Book III; not wired at II.1}` |
| 9 | CI status + clean tracked worktree | **PASS** | FORGE Tests run `39523659538` on `2bd4891` = **success**; `git status --porcelain` = only untracked `.bu_tmp/` (preserved) |
| 10 | Canonical model cards + frozen Book III plan | **PASS** | All 7 model cards read in full: `EUR_DAILY_NEWS_REKEY`, `EUR_WEEKLY_ENGINE`, `EUR_HIGHER_ORDER`, `XAU_GAME_L1_L2_L3`, `BTC_DAILY_WEEKLY_MONTHLY_TRACKER`, `FIB_RANGE_BIRTH`, `JPY_CARRY_GAME` (V1 each). Frozen Book III plan read: goal, core law, III.4.1–III.4.10, Acceptance III.4, all 18 cross-model invariants, golden-fixture program, failure behavior, ratification gate, exclusions, implementation order |

**Missing prerequisites: none.** Verdict: dependency-ready.

## 5. Dependency, ownership and canonical-source/authority matrix

### 5.1 Upstream contracts (consumed read-only, never redefined)

**From III.3 (`app/forge/model_runtime/`)** — inspected API at this head,
not inferred from summaries:

- `contract.ModelOutput` — the per-call immutable model state:
  `model_id`, `model_version`, `model_runtime_version`, `output_hash`,
  `model_state`, `layer`, `direction_bias`, `active_ranges`,
  `active_anchor_states`, `levels`, `range_left`, `no_go`, `warnings`,
  `claim_refs` (structurally empty), `evidence_refs`, `quality_state`,
  `production_authorization`, `explanation_facts`, `sub_states`,
  `identity`. This is the **only** model-state input III.4 accepts.
- `contract.Layer` (`L1`/`L2`/`L3`/`CROSS_LAYER`),
  `ProductionAuthorization` (4 values), `NoGoReason` (5 values),
  `WarningCode` (7 values), `ExplanationFact`/`make_fact`,
  `DirectionBias`, `TypedLevel`/`LevelKind`, `AnchorStateRef`,
  `RangeLeftField`, `SubState`, `InputIdentity`, `prior_ref`,
  `resolve_quality`, `evidence_union`.
- `errors.ModelRuntimeError` and its bounded codes
  (`MODEL_CONTRACT`, `MODEL_VERSION_UNAVAILABLE`,
  `DATA_QUALITY_BLOCKED`, `NO_CALCULATION`,
  `INSTRUMENT_SCOPE_MISMATCH`, `PRIOR_STATE_MISMATCH`,
  `INPUT_MEASUREMENT_MISSING`, `RULE_NOT_MATERIALIZED`,
  `REPLAY_HASH_MISMATCH`) — imported verbatim where semantics match;
  III.4 defines its **own** codes for its own refusals (§7.2), never
  redefining an upstream one.
- `registry.ModelKey`/`RegistryEntry`/`MODEL_REGISTRY`/`resolve` —
  exact `(model_id, model_version)` match only; 8 entries including the
  registered-but-never-dispatched historical `JPY.CARRY_GAME.L1_L3.V1@DT_12_4PM`.
- `replay.canonical_payload`/`canonical_blob`/`compute_hash`/
  `finalize_output`/`run_model`/`verify_replay` — canonical
  serialization (sorted keys, compact separators, `Decimal`→string,
  enum→value, LF, UTF-8) and `sha256` identity. III.4's history/replay
  hashing reuses this serialization discipline; it does not invent a
  second canonical form.
- `versions.MODEL_RUNTIME_VERSION = "MODEL_RUNTIME_V1"`.

**From III.2 (`app/forge/measurements/`)** — the path/measurement facts
III.4 carries but never recomputes:

- `path_metrics`: `PathMeasurement` (`reference_price`, `mae`, `mfe`,
  `levels`, `first_delivery`, `delivery_order`, `remaining_state`,
  `remaining_distribution`, `bar_count`), `LevelOutcome` (`touch_state`,
  `acceptance_state`, `close_beyond_state`, `re_entry_state`,
  `rejection_state`, `max_excursion`, `first_delivery`),
  `DeliveryObservation` (`level_id`, `bar_index`, `realized_at`,
  `order_index`), and the enums `TouchState`, `AcceptanceState`,
  `CloseBeyondState`, `ReEntryState`, `RejectionState`, `RemainingState`,
  `LevelSide`.
- `anchors`: `AnchorStatus` (UNRESOLVED/ELIGIBLE/ACTIVE/INVALIDATED/
  REKEYED), `AnchorEligibility`, `AnchorRefusalCode`,
  `ANCHOR_RULE_REGISTRY` (empty at this head — the R15 gate).
- `contracts`: `Measurement`, `Provenance`, `SourceWindow`,
  `RuleMaterialization` (CANONICAL/DECLARED/NOT_MATERIALIZED),
  `CalibrationKey`, `NativeMagnitude`.
- `state_age`: `elapsed_since`, `checkpoint_reached`,
  `acceptance_duration`, `failure_age`, `time_to_delivery`,
  `measure_session_phase`, `measure_period_phase`.
- `versions.MEASUREMENT_ENGINE_V1`.

**From III.1 (`app/forge/market_data/`)**: `Bar`/finality, `NativePrice`/
`convert_native`, `ClockIdentity`, `SessionRegistry`/
`SessionResolution`, `ResearchDayRegistry`/`assign_research_day`,
`QualityPolicy`/`QualityFlag`/`DataOutcome`, `MARKET_DATA_SCHEMA_V1`,
`CLOCK_REGISTRY_V1`, `SESSION_REGISTRY_V1`, `MarketDataError`.

**From Book I/II (read-only references only)**: canonical corpus object
IDs (`MODEL`/`EVIDENCE`/`SETUP`/`LINEAGE`), evidence/claim IDs, and
Book II policy/audit surfaces as *references* — III.4 imports no Book II
module and writes no corpus, ledger or audit record.

### 5.2 Model-family transition authority matrix (canonical source per family)

Authority is **per family and per generation**. A transition that is
canonical for one family is never inherited by another.

| Family | Model key(s) | Layer | Canonical source | Transition authority granted |
|---|---|---|---|---|
| EUR Daily | `EUR.DAILY.NEWS_REKEY.V1@PHASE1` | L1 | `EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md` | Seed/tier `ENTER_STATE`; ordered `DELIVER`; `ACCEPT`/`REJECT` (touch ≠ acceptance); rekey ladder 100/125/132/168/185 as distinct `REKEY` states, extension; event conditioning as *modifier only*; failure/repair **only** as its declared generation grammar (P90-merged lineage) |
| EUR Weekly | `EUR.WEEKLY.V1_1@V1_1` | L2 | `EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md` | Route `ENTER_STATE`; **outer-node `PROMOTE` only**; `FROZEN` static-after-completion; weekly path must not populate `destination_evidence`; no weekly→L3 promotion |
| EUR Higher Order | `EUR.HIGHER_ORDER.V1@V1` | L3 | `EUR_HIGHER_ORDER_MODEL_CARD_V1.md` | D3 prior `ENTER_STATE`; M1→M2→M3 checkpoint `DELIVER`; unfinished-side completion as **conditional** destination state; layer-conflict facts; no confluence score; no L1-driven L3 mutation |
| XAU Game | `XAU.GAME.L1_L2_L3.V1@V1` | CROSS_LAYER | `XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md` | `PROMOTE` 68+8h→80 (eligible) and 120+8h→132 (research/small-N, flag preserved); **132→168 NOT automatic**; 50–68 failure / 68+ repair bands with declared `FAIL`/`REPAIR`; `ACCEPT`/`REJECT` with blind-touch blocked; 132 `REKEY` as structural remap; 80 `INVALIDATE` family; `STAND_DOWN`/`PARKED` restrictions |
| BTC Tracker | `BTC.TRACKER.DWM.V1@V1` | CROSS_LAYER | `BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md` | Daily tier `ENTER_STATE`; ordered `DELIVER`; `ACCEPT`/`REJECT`; >$3,000 `STAND_DOWN`; slot×tier range-left re-conditioning; weekly/monthly anchor/rekey/rekey-excursion transitions **UNRESOLVED** (no canonical definitions); no Game/setup transition may enter |
| Fib / Range Birth | `CROSSASSET.FIB.RANGE_BIRTH.V1@R15` | CROSS_LAYER | `FIB_RANGE_BIRTH_MODEL_CARD_V1.md` | `RANGE_BIRTH_UNRESOLVED` → `RANGE_ACTIVE` gated by R15 materialization; A/B → Alpha/Beta/Gamma/Delta sequence `DELIVER`; structural `REKEY` (`REKEY_REMAPPED`); `INVALIDATE` (`ANCHOR_INVALIDATED`); **no** pivot fallback, no invented anchor |
| JPY Carry | `JPY.CARRY_GAME.L1_L3.V1@V1` (+ historical `@DT_12_4PM`, registered/not dispatched) | CROSS_LAYER | `JPY_CARRY_GAME_MODEL_CARD_V1.md` | Per-role state `ENTER_STATE`; separate `DELIVER` per role; confirmation ≠ entry; per-pair native no-go `STAND_DOWN`; **no equal-vote/aggregate transition**; `MANUAL_OPERATOR` preserved; DT 12–4PM geometry crosswalk only on explicit source |

Rules that follow from the matrix:

1. **Restriction is mandatory.** Every family declares an allowed subset
   of the frozen vocabulary; a transition outside the subset is refused
   (`TRANSITION_NOT_IN_FAMILY_VOCABULARY`), never silently dropped.
2. **Absence is authority.** Where canonical evidence is missing (BTC
   weekly/monthly, JPY parity, Fib R15), the transition exists as an
   explicit `UNRESOLVED`/`NOT_MATERIALIZED` outcome — that is a valid,
   reportable result, not a defect to be papered over.
3. **Small-N is not universal.** XAU 120+8h→132 keeps its
   `RESEARCH_FLAG_SMALL_N` identity and sample size; it never becomes a
   universal promotion rule. Historical P90 failure/repair behavior is
   never generalized to unrelated models.
4. **Cross-family transfer refuses.** A transition defined for one family
   cannot be applied to another family's state, even when the numbers
   coincide (`TRANSITION_AUTHORITY_MISMATCH`).

## 6. Existing implementation reuse + interface-integrity baselines

- `app/forge/` has **no** transition, snapshot, history or path-ordering
  code at this head (verified: no `app/forge/state_engine/` exists;
  `app/forge/model_runtime/` contains no state-machine or history code).
  III.4 is greenfield; there is no parallel-abstraction risk.
- Legacy Signal Guard code (`app/state_engine.py`) is a naive
  position-state file writer (LONG/SHORT/FLAT + `data/position_state.json`,
  max 100 history entries). It is **not** reusable, is deliberately
  untouched, and its name is an unrelated collision — the III.4 package
  is `app/forge/state_engine/` and must not import it.
- Reusable *patterns* (not code): frozen dataclasses + bounded refusal
  codes; versioned registry objects; append-only ordered records; fixture
  manifest + generator + provenance README; the honesty-disclosure
  vocabulary (`NOT_CONFIGURED`, `GAP-n`, `RESEARCH`, `NOT_MATERIALIZED`,
  `UNRESOLVED`); III.2's `RuleMaterialization` reused verbatim for rule
  gating.

### 6.1 III.1 interface baseline — 11 modules (LF-normalized sha256, verified 11/11)

```
app/forge/market_data/__init__.py        7d57349bba68c6a090ab2f7739e9bd095e436ba01bf110da1ed1c1aa22611fd0
app/forge/market_data/bars.py            97fc99e44c7abab0545a33e2b0fbf0b3d354ae5bae2b4c6e446ff3b336666366
app/forge/market_data/clocks.py          2698d527f6cfcfac7f92285a879e722dfd9a174fd3ce9078f566e0af01fef172
app/forge/market_data/errors.py          52f108165f5b6f34ec1d828984cff69e24f6099fbebeae2a16f41fcb6786c88c
app/forge/market_data/instruments.py     8c6d6ad05db973122265bca76ea6b3c0c3e248974fa26cb6409ef4cce67ed94d
app/forge/market_data/normalize.py       04c4ecfc97e111e281d90158df5ee7b6cff1aeb25e4df6eaf81f93a66e9d026b
app/forge/market_data/parity.py          0bb765af9943fd0dead7a26a9155449b4f5716412fe03c00fb4522b26818ce8c
app/forge/market_data/quality.py         6b77c6dfa11e6b22013b7f128e0d6b8095b5e035b660c93c309df220bcb58687
app/forge/market_data/research_day.py    b5c82e4098ea5a0ebe79f89d2da4841fd5f9235210f0fd59d90bb1835cdd5307
app/forge/market_data/sessions.py        037dbaaa308e210e945b220ff88f792d82ee45de06e87df3213c89adbc7b77e5
app/forge/market_data/versions.py        9e502d7f9e95c567feb11e3a5c3224cabb4d809155926bbc6810dcfdc2f7842e
```

### 6.2 III.2 interface baseline — 12 modules (verified 12/12)

```
app/forge/measurements/__init__.py        2b243ddec1d03579804deb6ef54a3bb7e59012819bb19beeaa4cc1c6fb070bc2
app/forge/measurements/anchors.py         227a17d112ccd35588aeee958b28c113d3550228c3f912aa3d360e23e5694e5a
app/forge/measurements/calibration.py     62a53d65b5895d3b5bd07cc444bd741752f35d371e711bac4d378a2856a22693
app/forge/measurements/contracts.py       847074d84825358067cb290a4da30a92e10c837fc4f609722c1d5ca49b552a69
app/forge/measurements/coordinates.py     c224d775c68cd49eb41b3afbfcbb0ef9b4468dc8e6b0baa7d9103c35a5b70e23
app/forge/measurements/errors.py          974fe1ae769c9bb21b8ddc02ea7010a6a6a524a812be2ba2ad327a905d2f44ff
app/forge/measurements/events.py          306093100ed065c2368f69cb6fc66aa2a321af8d76d4f86d314f3860772af89e
app/forge/measurements/higher_order.py    554061988e9890f318a6d319c0c6b89815b0eab0ce4b15ecb2893e16c5ace60d
app/forge/measurements/path_metrics.py    f55dcc24f6620fa13fffb12cb82d92c6b8a81732cf3ff7298ce73adc3ce79743
app/forge/measurements/ranges.py          1addf5d06626eb0f39fe58640740af10d26b54b1c758d2db8a66cd21463bdfed
app/forge/measurements/state_age.py       3c4e45f83381c9239dc0cd834ddb073c921d18abfda92100f885e64f1e2a65b5
app/forge/measurements/versions.py        f139b51ca24ed050532e404f284885a989ed0d123c5ecf5144b2d13404331bd3
```

### 6.3 III.3 interface baseline — 13 modules (verified 13/13 vs `bloc_iii_3/RATIFICATION.md` §3)

```
app/forge/model_runtime/__init__.py         4d742dea51e4067fb8fa174e7a50971b379dc9feaa24f20bd7481ddd12c8311a
app/forge/model_runtime/btc_tracker.py      603409300770db11042e1b87d0f11753e1f1272ffbf0181b20c1759038af45a5
app/forge/model_runtime/contract.py         d0dc91f79e8183638d5eef606541c290b29d2cbdc759aef35341d1004c3f9056
app/forge/model_runtime/errors.py           9a29936df62852884b364822115ad5f33de1f327d2f446df1bb60016aefa6f1e
app/forge/model_runtime/eur_daily.py        4cb0fb57b0f548e2e27c36f6bc750f954546fc1e8bcf111c4c6d30139dada606
app/forge/model_runtime/eur_higher_order.py 19621c53daed5772456e17d2a605836105d15b4b1bffbfb304a06576bbf038fe
app/forge/model_runtime/eur_weekly.py       f532d2633c2a530d8724a502d6693ae411228e0ca75d513d70762cf31b62f62d
app/forge/model_runtime/fib_range_birth.py  c64ebf9057af052050b49e4e456f89a4ea7f3bd3bfa3e9c61a6f08b51a054d2d
app/forge/model_runtime/jpy_carry.py        bde7aa387987ef57cdda5882ba1d6c77c0105ee70ff2f50b36496031248f9c16
app/forge/model_runtime/registry.py         3ce67bf4e782614fab508ced473acdce29c3426f061b9a593d11cc8db3867ca9
app/forge/model_runtime/replay.py           c6a14aca8853212bd485ae2dc552c75f91c9998fff0075b3e78bff74fa43b611
app/forge/model_runtime/versions.py         87823a0505289423ad3110a67b5f5740d7b13ff4b8b1b07e51279c2bb1c9ea81
app/forge/model_runtime/xau_game.py         3255d6d1275a78223c481e374501ee68d60b03cf2b284b1bfbbf175a440baa0c
```

Method: `sha256` over the file bytes with `\r\n` normalized to `\n`, so
the baselines verify identically on this Windows `core.autocrlf=true`
checkout and on the Linux CI checkout. Any change to a module hash above
during III.4 implementation is a **frozen-surface violation** and a stop
condition (§12.2) — these files are never modified by III.4.

## 7. Proposed design (planning intent — implementation needs its own authorization)

### 7.1 Package layout (new; touches no ratified file)

`app/forge/state_engine/`

| Module | Ch | Contents |
|---|---|---|
| `snapshot.py` | III.4.1 | `StateSnapshot` — frozen dataclass: `snapshot_id`, `model_id`, `model_version`, `model_runtime_version`, `state_engine_version`, `layer`, `event_time`, `calculation_timestamp`, `active_state`, measurement refs (definition id + version + source window, never recomputed values), `active_ranges`, `levels`, `range_left`, `quality_state`, `evidence_refs`, `claim_refs` (empty), `production_authorization`, `no_go`, `warnings`, `source_output_hash`, `prior_snapshot_id`, `snapshot_hash`; validation refuses a snapshot not derived from a finalized `ModelOutput` |
| `vocabulary.py` | III.4.2 | `TransitionKind` (exactly the 12 frozen members, no additions); `TransitionAuthority` per `(model_id, model_version)` declaring allowed/restricted/unresolved kinds; `QualifyingPriorState` (required/forbidden prior-state sets per kind); `TransitionRequest` (kind, prior snapshot ref, canonical rule id/version, source lineage, injected event time); `evaluate_transition()` — pure guard function |
| `delivery.py` | III.4.3 | Ordered target/state delivery: `DeliveryRecord` (`target_id`, `order_index`, `realized_event_time`, `realizing_bar_ref`), `FirstDelivery` (first-hit side + timing), stable `target_order`, both-side-reach record that **retains** first-delivery sequence, and explicit `AMBIGUOUS_PATH` refusal when intrabar ordering cannot be resolved from OHLC |
| `failure_repair.py` | III.4.4 | Declared failure/repair grammar per family+generation: `FailureState` (NONE / FAILED / REPAIR_ATTEMPTED / REPAIR_CONFIRMED / REACCEPTED / OPPOSITE_ACCEPTED / COMPRESSED); transitions only where `RuleMaterialization` is CANONICAL/DECLARED for that model version; `FAIL` without prior valid acceptance refuses (`FAILURE_WITHOUT_ACCEPTANCE`) |
| `rekey.py` | III.4.5 | `RekeyRecord`: prior range ref, qualifying structural event, canonical rule id/version, new active mapping, eligibility change, prior-state lineage; the record **closes/replaces** the prior mapping per model; a bare touch/threshold crossing refuses (`REKEY_NOT_STRUCTURAL`) |
| `handoff.py` | III.4.6 | `LayerHandoff`: `source_layer` → `destination_layer` (L3→L2→L1 only), destination context, path/opportunity record, execution-context ownership marker; typed so a lower layer can never populate a higher-layer field; no score field exists |
| `range_left.py` | III.4.7 | `ConditionalRangeLeft`: remaining distribution with an explicit `conditioned_on` tuple of consumed transition/state ids, recomputed after delivery/acceptance/exhaustion/invalidation/rekey; `UNRESOLVED` when unsupported; refuses an unconditional historical frequency (`UNCONDITIONAL_FREQUENCY_REFUSED`) |
| `stand_down.py` | III.4.8 | `StandDownState` enum — `DATA_QUALITY_FAILURE`, `INVALID_RANGE`, `UNRESOLVED_ANCHOR`, `MODEL_CONFLICT`, `PARKED_OR_EXHAUSTED`, `EVIDENCE_UNAVAILABLE`; `StandDownRecord` (state, reason code, blocking rule ref, capability lock); an `eligibility_lock` fact that downstream setup eligibility must respect |
| `history.py` | III.4.9 | `TransitionEvent` (`event_id`, `sequence`, `kind`, `source_snapshot_ref`, `event_time`, `rule_id`, `rule_version`, `resulting_state_id`, `payload`), `TransitionLedger` (append-only, ordered), `reconstruct_state()`, `explain()` (ordered facts, never prose), `history_hash` + `prev_event_hash` chain, `verify_history()` |
| `invariants.py` | III.4.10 | Path-invariant enforcement: target-order stability, explicit-rekey requirement, history persistence, layer isolation, no-go restriction, deterministic replay, unearned-transition refusal |
| `errors.py` | III.4.2/§12 | Bounded refusal vocabulary (§11) — own codes only, upstream codes imported where semantics match |
| `versions.py` | final record | `STATE_ENGINE_VERSION`, proposed value `"STATE_ENGINE_V1"` |
| `__init__.py` | — | Bounded public surface re-exporting snapshot, vocabulary, history and invariant helpers |

### 7.2 Transition contract (frozen field set for the future implementation)

Every transition — without exception — carries:

1. **Source lineage.** `source_output_hash` of the III.3 `ModelOutput`
   it derives from, plus the `snapshot_id` it reads. A transition whose
   source is missing, unfinalized or from another model key refuses
   (`SOURCE_LINEAGE_MISSING` / `PRIOR_STATE_MISMATCH` reused).
2. **Qualifying prior state.** The prior `active_state` must be in the
   declared `required_prior_states` for that kind and outside
   `forbidden_prior_states`; otherwise `TRANSITION_NOT_EARNED`.
3. **Canonical rule.** `rule_id` + `rule_version` + canonical source ref,
   materialization status. A rule that is `NOT_MATERIALIZED` cannot earn
   a transition, in either direction.
4. **Event time.** Injected `event_time` (never wall clock), distinct
   from `calculation_timestamp`; ordering within a bar is explicit, and
   unresolvable ordering refuses.
5. **Resulting state identity.** `resulting_state_id` + family state
   value, so replay can reconstruct.

### 7.3 History, replay and reconstruction identity

- Append-only, ordered, gapless `sequence`; each event stores
  `prev_event_hash`; `history_hash` = canonical hash (III.3
  serialization discipline: sorted keys, compact separators, `Decimal`
  → string, enum → value, LF, UTF-8) over the ordered event payloads.
- **Reconstruction**: replaying the ledger from a genesis snapshot must
  reproduce the current `StateSnapshot` byte-identically; failure is
  `REPLAY_RECONSTRUCTION_MISMATCH`.
- **Mutation detection**: any reorder, deletion, insertion or silent
  rewrite breaks the chain (`HISTORY_CHAIN_MISMATCH`).
- **Determinism**: identical inputs + identical rule/version identity ⇒
  identical `history_hash` and `snapshot_hash` across runs and
  platforms.
- History is *queried facts*, never prose: an explanation is an ordered
  tuple of events/facts, so Book IV may render prose and III.4 may not.

### 7.4 Cross-cutting rules for the future implementation

Pure functions + frozen dataclasses; `Decimal` in asset-native units
(never float, never cross-unit without III.1 `convert_native`); injected
clocks only; no network, no file I/O, no wall time, no randomness; no
imports from `qa/`, `retrieval/`, `app/forge/provenance.py`,
`canonical.py`, `policy.py`, `service/`, `providers/`, `persistence/`,
`observability/`, `backfill/`, or any frozen/ratified file; the only
absolute `app.*` imports are `app.forge.market_data`,
`app.forge.measurements` and `app.forge.model_runtime`;
`ForgeServiceContainer` never appears; outputs immutable; no
`latest()`; no default version; no credential/PII path; all enums are
bounded and no field is free text.

## 8. Model-specific transition restrictions (summary of §5.2)

| Family | Allowed | Restricted / unresolved | Never |
|---|---|---|---|
| EUR Daily | ENTER_STATE, DELIVER, ACCEPT, REJECT, REKEY, (declared) FAIL/REPAIR | COMPRESS/RELEASE only as its own declared generation grammar | Universalizing historical P90 failure/repair to other models; ST/P90 automation promotion |
| EUR Weekly | ENTER_STATE, PROMOTE (outer node), DELIVER, FROZEN | REKEY unspecified for this generation | Weekly path as L3 destination evidence; promoting everything at once |
| EUR Higher Order | ENTER_STATE, DELIVER (D3/M1/M2/M3) | INVALIDATE/COMPRESS unspecified | L1-driven L3 mutation; confluence score; D3 statistics as WR |
| XAU Game | ENTER_STATE, PROMOTE (68→80, 120→132 small-N), ACCEPT/REJECT, REKEY (132), FAIL/REPAIR (bands), INVALIDATE (80), STAND_DOWN | 132→168 not automatic; parked cannot promote | Blind-touch confirmation; universalizing small-N promotions; L2 state as direct entry |
| BTC Tracker | ENTER_STATE, DELIVER, ACCEPT/REJECT, STAND_DOWN (>3000), range-left re-conditioning | Weekly/monthly anchor/rekey = UNRESOLVED | Any Game/setup transition; Gold setup import; invented weekly/monthly anchors |
| Fib / Range Birth | Structural REKEY, INVALIDATE, sequence DELIVER | RANGE_ACTIVE gated by R15 = NOT_MATERIALIZED | Pivot fallback; invented anchor; coordinate availability as eligibility |
| JPY Carry | Per-role ENTER_STATE, per-role DELIVER, per-pair STAND_DOWN | Per-pair tier interpretation partial | Equal-vote majority; confirmation as entry; aggregate score; automation parity claim; auto-merged DT geometry |

## 9. Proposed executable test matrix (summary; full clause→test map in `ACCEPTANCE.md`)

Proposed suite: `tests/test_forge_state_engine.py`. Deterministic,
offline, network-free, no wall clock, injected timestamps only.

| Group | Frozen driver | Scope |
|---|---|---|
| T1 | III.4.1 | Snapshot contract: immutability, version fields, layer, timestamps, active state, measurement refs (not values), ranges, levels, quality, evidence refs, `source_output_hash`, `snapshot_hash` determinism, refusal of unfinalized/unowned sources |
| T2 | III.4.2 | Vocabulary: exactly 12 kinds; per-family allowed sets; qualifying prior state required; canonical rule required; source lineage required; unearned transition refused; no new kind by construction |
| T3 | III.4.3 | First delivery: ordered delivery, first-hit side + timing, stable target order, terminal both-side reach preserving sequence, ambiguous intrabar refusal, OHLC never used to invent ordering |
| T4 | III.4.4 | Failure/repair: declared-only grammar; valid acceptance → failure → repair → compression/reacceptance/opposite acceptance; repair without prior failure refuses; no cross-family generalization; repair ≠ new acceptance |
| T5 | III.4.5 | Rekey: structural remapping record (old range, qualifying event, new mapping, lineage); touch alone refuses; ladder steps distinct; rekey closes/replaces prior mapping; invalid rekey refused |
| T6 | III.4.6 | Layer handoff: L3→L2→L1 direction only; destination/path/execution ownership typed; no upward probability field; L1 cannot mutate L3; no monolithic confluence |
| T7 | III.4.7 | Range-left: conditional on consumed states; re-conditioned after delivery/acceptance/exhaustion/invalidation/rekey; unconditional frequency refused; `UNRESOLVED` honesty |
| T8 | III.4.8 | Stand-down: six bounded states; machine-readable reasons; no-go cannot become setup eligibility; parked/exhausted restriction; evidence-unavailable path |
| T9 | III.4.9 | History: append-only ordering, gapless sequence, per-event source/time/rule/result, reconstruction of current state, explanation facts, event-order mutation detection, non-deterministic replay detection |
| T10 | III.4.10 | Path invariants + the 15-class adversarial matrix (§10.2): same terminal result different path, first-delivery reversal, ambiguous intrabar, touch-without-acceptance, invalid rekey, repair-without-failure, XAU parked promotion, L1→L3 mutation, BTC Game into Tracker, JPY equal-vote, missing source, nonfinal/poor-quality bars, historical version drift, event-order mutation, no-go eligibility leak |
| T11 | Invariants #6–#11, #18; gate §State/path | Label/serialization discipline: no probability/confidence/confluence/win-rate/expectancy/prediction/signal field (AST + field + enum + payload-key scan); touch/acceptance/path distinctions survive serialization; bounded enums only; immutability |
| T12 | §3 exclusions; Book gate §Evidence pack; final record | Boundaries: no network (socket guard); import discipline (no Book II/authority modules, no frozen files, no legacy `app.state_engine`); no corpus/ledger write; migration baseline `[1,2,3,4]`; readiness seam unchanged; Book II 50 hashes + 23 pins + Book I manifest + III.1 11 + III.2 12 + III.3 13 module hashes unchanged after the suite; deterministic repeat runs; no credentials/PII |

## 10. Golden fixture program (proposed; fixtures are NOT created in this rung)

Proposed directory: `implementation/forge/book_iii/bloc_iii_4/fixtures/`
with `FIXTURE_MANIFEST.json` (LF-normalized sha256, same convention as
III.1–III.3), a `README.md` provenance table, and a deterministic
`generate_fixtures.py`.

### 10.1 Proposed fixture set

| File | Fixture id | Contents |
|---|---|---|
| `state_snapshots.json` | `BLOC_III_4.STATE_SNAPSHOTS.V1` | One snapshot per family + layer, version/quality/evidence fields, `prior_snapshot_id` chaining |
| `transition_vocabulary_cases.json` | `BLOC_III_4.TRANSITION_VOCABULARY.V1` | All 12 kinds; per-family allowed/refused matrices; qualifying-prior-state edges |
| `first_delivery_cases.json` | `BLOC_III_4.FIRST_DELIVERY.V1` | Order preserved, both-side terminal reach, reversal pair, ambiguous intrabar |
| `failure_repair_cases.json` | `BLOC_III_4.FAILURE_REPAIR.V1` | Declared EUR-generation grammar, XAU 50–68/68+ bands, repair-without-failure refusal, cross-family refusal |
| `rekey_cases.json` | `BLOC_III_4.REKEY.V1` | EUR ladder 100/125/132/168/185, XAU 132 structural remap, Fib structural rekey, touch-only refusal |
| `layer_handoff_cases.json` | `BLOC_III_4.LAYER_HANDOFF.V1` | EUR L3→L2→L1 chain, XAU L3/L2/L1 isolation, L1→L3 mutation refusal |
| `range_left_cases.json` | `BLOC_III_4.RANGE_LEFT.V1` | Re-conditioning after each consumed event; unconditional-frequency refusal; `UNRESOLVED` |
| `stand_down_cases.json` | `BLOC_III_4.STAND_DOWN.V1` | Six states incl. BTC >$3,000, XAU parked, Fib unresolved anchor, JPY per-pair no-go, evidence-unavailable |
| `transition_history_cases.json` | `BLOC_III_4.TRANSITION_HISTORY.V1` | Ordered ledgers per family, chain hashes, mutation variants |
| `path_invariants_cases.json` | `BLOC_III_4.PATH_INVARIANTS.V1` | Same-terminal-different-path pair, target-order stability, refusal matrix |
| `model_family_transition_authority.json` | `BLOC_III_4.FAMILY_AUTHORITY.V1` | The §5.2/§8 matrix verbatim: allowed/restricted/unresolved/never per family |
| `replay_hashes.json` | `BLOC_III_4.REPLAY_HASHES.V1` | `history_hash` + `snapshot_hash` per golden ledger |

### 10.2 Required adversarial classes (all 15 from the authorization)

Same terminal result with different path · first-delivery order
reversal · ambiguous intrabar events · touch without acceptance · invalid
rekey · repair without prior failure · parked XAU state promoting
without authority · L1 mutation of L3 · BTC Game logic entering Tracker ·
JPY equal-vote interpretation · missing source evidence · nonfinal/poor
quality bars · historical version drift · event-order mutation ·
non-deterministic replay · no-go incorrectly allowing setup eligibility.
Sixteen classes are enumerated by the authorization (§6); all are mapped
in `ACCEPTANCE.md` §J and §T10 above.

### 10.3 Provenance honesty

Every fixture is labeled `SYNTHETIC_FIXTURE` or
`CANONICAL_SOURCE_SLICE`. Synthetic fixtures are **contract validation,
never empirical trading evidence**; canonical constants (tiers, bands,
promotion sample sizes, evidence ids) enter only quoted verbatim with
source refs. Replay-hash reproduction is determinism evidence only.

## 11. Failure and security matrix

| Condition (frozen) | Required behavior | Proposed test |
|---|---|---|
| Incomplete/missing input data | `DATA_QUALITY_FAILURE` stand-down state or explicit `DATA_QUALITY_BLOCKED` — never a fabricated transition | T8, T10 |
| Clock/session/event time unresolvable | `NO_CALCULATION` (explicit, never empty success) | T3, T9 |
| Intrabar ordering ambiguous | `AMBIGUOUS_PATH` refusal; OHLC never used to infer order | T3, T10 |
| Anchor unresolved | `UNRESOLVED_ANCHOR` stand-down; no eligibility-bearing transition | T8 |
| Model/version missing | `MODEL_VERSION_UNAVAILABLE` (upstream code, reused) — no fallback | T2 |
| Evidence missing | Transition may exist when the rule is canonical, but **no unsupported statistic** is attached | T7, T11 |
| Higher/lower layer conflict | `MODEL_CONFLICT` stand-down + conflict facts; never a confluence score | T6, T8 |
| Prior state does not qualify | `TRANSITION_NOT_EARNED` | T2, T10 |
| Rule not materialized | `RULE_NOT_MATERIALIZED` (upstream code, reused) | T4, T5, T10 |
| History tampered/reordered | `HISTORY_CHAIN_MISMATCH` | T9, T10 |
| Replay diverges | `REPLAY_RECONSTRUCTION_MISMATCH` | T9, T10 |
| No-go followed by eligibility-bearing state | `ELIGIBILITY_WITHOUT_AUTHORITY` refusal | T8, T10 |
| Provider/feed failure | No feed path exists here; stale *serving* is III.6 product policy — review: recorded in EVIDENCE | review |
| Frozen-surface drift (Book I/II + III.1/III.2/III.3) | manifest-hash tests unchanged after the suite | T12 |
| Secrets/PII in the data path | none: no credentials, bounded enums, no free-text payload | T11, T12 |

## 12. Known gaps and stop conditions

### 12.1 Known gaps (recorded, not hidden)

- **III.4-GAP-1 (carries III.3-GAP-1 / III.2-GAP-1)** — Fib **R15 Range
  Birth eligibility is not materialized** (`ANCHOR_RULE_REGISTRY` empty).
  III.4 can represent `RANGE_BIRTH_UNRESOLVED`, structural rekey and
  invalidation; any transition into `RANGE_ACTIVE` without the rule is
  refused. No invented eligibility. **Blocks:** Fib production-path
  transitions only.
- **III.4-GAP-2 (carries III.3-GAP-2 / III.2-GAP-2)** — JPY pair-native
  tier parity not established; manual classification in force. III.4
  implements role-separated state transitions only. **Blocks:** JPY
  automation-parity claims and any equal-vote transition (impossible by
  construction).
- **III.4-GAP-3 (carries III.3-GAP-3 / III.2-GAP-3)** — XAU calibration
  is spatial bands + promoted examples + doctrine, not a tier table.
  III.4 keeps small-N flags and evidence refs on every promotion
  transition; no universal rule.
- **III.4-GAP-4 (carries III.3-GAP-4 / III.2-GAP-4)** — No event/news
  calendar in-repo; event conditioning is a modifier fact only.
- **III.4-GAP-5 (carries III.3-GAP-5 / III.2-GAP-6)** — Higher-order
  statistics are evidence-bound; III.4 stores evidence ids, never
  values, and never converts them to probabilities.
- **III.4-GAP-6 (carries III.3-GAP-6 / III.1 GAP-1)** — No real bar
  slices; golden fixtures are synthetic-labeled contract material.
- **III.4-GAP-7 (carries III.3-GAP-7 / III.1 GAP-2…5)** — Sessions/
  final-bar/provider seam/scripted-parity only; clock-bound transitions
  degrade to `NO_CALCULATION` explicitly.
- **III.4-GAP-8 (carries III.3-GAP-8, new here)** — BTC **weekly/monthly**
  anchor/rekey/excursion transitions are `UNRESOLVED`
  (`NOT_MATERIALIZED`): representable as explicit unresolved outcomes,
  never as invented remappings. **Blocks:** BTC weekly/monthly
  transition classification.
- **III.4-GAP-9 (carries III.3-GAP-9)** — XAU parked and quarter-zone
  *confirmation* doctrine are III.5's. III.4 enforces parked-stays-parked
  and blocked blind-touch, but defines no setup semantics.
- **III.4-GAP-10 (new)** — **Durable storage of transition history is
  undecided.** III.4 plans the *logical* append-only history contract
  (ordering, chain hashes, reconstruction) with no persistence
  migration (`[1,2,3,4]` unchanged). A storage packet is required before
  any durable write. **Blocks:** persistence only, not the contract.
- **III.4-GAP-11 (disclosure; carries III.3-GAP-10)** — ST manual / P90
  version-identity setup objects still have no canonical MODEL
  representation; transition-level golden cases for them are deferred to
  III.5.9/III.5.10. III.4 claims neither.
- **III.4-GAP-12 (new, boundary)** — **First-delivery ordering is only
  as good as the bar granularity supplied.** Where canonical evidence
  cannot resolve ordering within a bar, III.4 refuses rather than
  guesses; it does not claim tick-level reconstruction.

### 12.2 Stop conditions (report, do not improvise)

1. Any frozen III.4 clause that cannot be planned without contradicting
   a Book I/II frozen contract, the ratified III.1/III.2/III.3
   interfaces, or by inventing a non-canonical rule/transition.
2. Any need to modify a frozen Book I/II file, any III.1/III.2/III.3
   module (any change to the §6 hashes), the container readiness seam, or
   to add a migration → stop; governed packet first.
3. Conflicting canonical sources (e.g. two definitions of the same
   family's failure/repair grammar, or two rekey rules for one
   generation) → operator/governance ruling; never pick silently.
4. Any requirement to emit a probability, confluence score, confidence
   score, prediction, expectancy, win rate or performance metric from
   this layer → stop.
5. Any transition that would grant setup eligibility or execution
   authority → bounded interface proposal only, never implementation.
6. Being blocked on III.4 does **not** authorize beginning III.5 or any
   other Bloc without a new operator handoff. **This packet authorizes
   planning only: STOP AFTER PLANNING.**

## 13. Acceptance / ratification requirements (this Bloc)

Per the frozen Book III gate §Evidence pack, III.4 is DONE only with:
`PLAN.md` (this file), `ACCEPTANCE.md`, an implementation commit ladder
(separate authorization), test output, `EVIDENCE.md`, known-gaps list
with dispositions, and a ratification record. `ACCEPTANCE.md` freezes
the clause→test map now; any implementation must satisfy it or report a
deviation — never weaken it. At implementation time, EVIDENCE must
re-verify **all three** interface baselines (11 + 12 + 13 module hashes),
the Book II 50 hashes + 23 pins, the Book I manifest, the migration
baseline and the readiness seam — and re-verify that III.3 remains
byte-identical (III.4 is not permitted to "fix" upstream on the way
past).

## 14. Handoffs

- **To III.5 (setup engine):** III.4 offers immutable snapshots, an
  append-only ordered transition history with reconstruction, the
  `stand_down` eligibility lock, conditional range-left with its
  conditioning set, and layer-ownership markers. III.5 may consume these
  facts; it may not re-derive model interpretation or convert a path
  event into a probability.
- **To III.6 (API):** snapshot/transition identity (`snapshot_hash`,
  `history_hash`), event ordering and reconstruction are designed to be
  served deterministically; serving, caching and stale policy remain
  III.6's.
- **To Book IV (Ask CEREBUS):** transition history is queryable *facts*
  in order — never prose; Book IV renders explanations and must not
  recompute path state inside an LLM.
- **To Book V:** charts may render the path; they may not create
  transitions or model logic in the frontend.

**STOP AFTER PLANNING. No implementation of III.4 is authorized by this
packet, and III.5 is not authorized by it either.**
