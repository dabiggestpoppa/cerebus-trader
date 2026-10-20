# BOOK III / BLOC III.3 — CEREBUS MODEL RUNTIME — PLAN.md

Status: **PLANNING ONLY — committed before any implementation** (frozen
Book II/III.1/III.2 order rule reused: PLAN + ACCEPTANCE are committed
first; no implementation authorized by this packet).
Date: 2026-10-20
Branch: `forge` · Planning head: `f9dce4f2d612f447bd8d2fa9c659a926cab65235`
Frozen source: `planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(pinned in `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` line 35) —
sections `# BLOC III.3` (Common model contract + Ch III.3.1–III.3.9 +
Acceptance III.3), `# BOOK III CROSS-MODEL INVARIANTS`,
`# BOOK III GOLDEN FIXTURE PROGRAM`, `# BOOK III FAILURE BEHAVIOR`,
`# BOOK III ACCEPTANCE / RATIFICATION GATE` §Models + final-record
fields, `# BOOK III EXCLUSIONS`, and `# RECOMMENDED IMPLEMENTATION
ORDER` step 3 (common runtime/state contracts) + step 4 (the seven
launch families).

Scope here is exactly the frozen Bloc III.3 chapters — no Book III
scope is inferred from the Book title, and a model state never becomes a
trade by being useful. Cross-checked against
`planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` (§5 graph:
`I.3-I.5 -> III.1-III.3 -> III.4-III.6`; Phase C order) and
`planning/forge/AGENT_EXECUTION_HANDOFF_V1.md` (`III.1 -> III.2 -> III.3
-> III.4 -> …`; "later phase may start early only when its required
contracts are already frozen and the work does not create a circular
dependency" — both hold; III.1 and III.2 are ratified).

**A model runtime interprets measurements according to canonical rules.
It does not invent rules, evidence, probabilities, trade setups or
automation authority.**

---

## 1. Governing authority model (mandatory, restated — Phase 3)

These distinctions govern every design decision in this Bloc and are
re-verified in ACCEPTANCE.md:

- **Data establishes observation. Measurement establishes fact.
  Canonical models establish interpretation. Governed setups establish
  eligibility.** No stage inherits the authority of the next.
- **Model ≠ Claim ≠ Evidence ≠ Setup ≠ Artifact.** III.3 produces
  *model states*: versioned interpretations of III.2 measurements under
  canonical rules (`CEREBUS_CANONICAL_TAXONOMY_V1.md` class 1 MODEL /
  model output). Numerical statistics cite Book I evidence IDs
  read-only; III.3 never grants itself evidence authority and never
  creates a claim.
- **Measurement ≠ model interpretation.** III.2 measurement objects are
  consumed as facts; the runtime never redefines, re-labels or
  re-synthesizes them (core law: downstream may consume, never silently
  redefine).
- **Model state ≠ trade eligibility.** Every output distinguishes the
  descriptive state from production authorization; no output field
  confers eligibility, and no setup/entry/trigger/invalidation object
  exists at this layer (III.5 owns setups; III.4 owns transitions).
- **L3 destination ≠ L2 path ≠ L1 entry** (invariant #11): layer
  ownership is typed on the output and same-layer provenance is
  enforced structurally — a lower-layer input can never populate a
  higher-layer field and vice versa.
- **A model state is not a prediction.** No III.3 value may be labeled,
  typed or serialized as a probability, confidence score, confluence
  score, win rate, expectancy, RR, prediction or signal (Book III
  exclusions: no monolithic AI confidence score).
- **Historical observation ≠ current market state**; **simulation ≠
  empirical performance**: golden-fixture reproduction is a
  deterministic contract test over committed (mostly synthetic) inputs —
  never empirical or performance evidence.
- **Historical evidence ≠ verified current performance** (invariant
  #12): evidence IDs travel with any statistic reference; the runtime
  itself emits no statistics.
- **Asset calibration remains model-local** (invariant #2); cross-asset
  transfer refuses.
- **Manual strategy validity ≠ automation parity** (invariant #11 of
  the packet / #14 of the frozen set): `MANUAL_OPERATOR` and
  `RESEARCH_ONLY` classifications are preserved verbatim, never
  promoted by implementation convenience.
- **BTC Tracker ≠ BTC Game.** No Gold Game setup logic may enter the
  BTC Tracker runtime.
- **No trading/execution/game concepts as package identifiers.** The
  canonical model-ID strings (e.g. `JPY.CARRY_GAME.L1_L3.V1`,
  `XAU.GAME.L1_L2_L3.V1`) and the canonical BTC `trigger_levels` field
  are corpus vocabulary passed as *data*, disclosed exactly as III.2
  disclosed `trigger_levels` (PLAN III.2 §6); they are never mirrored
  into new package identifiers.

## 2. Scope (frozen chapters, in)

| Ch | Frozen requirement (compressed; frozen plan is authority) |
|---|---|
| — | **Common model contract.** Input: canonical model/version; normalized measurements; prior model state if stateful; calculation timestamp. Output: model_state; layer; direction/bias if the model defines one; active ranges/anchors; levels; range-left/distribution fields; no-go/warnings; evidence/claim references; data quality; model version/hash; explanation facts, not generated prose. |
| III.3.1 | EUR Daily News + Rekey runtime: Asian seed → tier → distance/asymmetry → consumed states → event/news conditioning → rekey/extension → remaining distribution. Protect: >45p source no-go; 100/125/132/168/185 state identity; news as modifier; slot × tier/range-left semantics. |
| III.3.2 | EUR Weekly Engine V1.1: Monday seed/range → weekly tier → route/range-left → hour × tier timing → outer-node state. Protect: static/frozen after defined completion; outer-node promotion only; weekly path not promoted into higher-order destination evidence. |
| III.3.3 | EUR Higher Order runtime: quarter seed → D3 prior → M1 scale → M2 shaping → M3 resolution → weekly/local handoff. Protect: L3 destination semantics; D3 agreement statistics ≠ trade WR; M1 correlation ≠ probability; unfinished-side completion as conditional destination evidence. |
| III.3.4 | XAU Game runtime: L3 destination/scale; L2 route/pace/distribution/delivery clocks (Tuesday pace/location/range-left); L1 Asian tier/relative consumption/execution context. Protect frozen rules: 68+8h → 80 eligible promotion; 120+8h → 132 research/small-N promotion; 132 → 168 NOT automatic; L2 state ≠ direct entry; parked setups remain parked; runtime does not execute quarter-zone trades. |
| III.3.5 | BTC Tracker runtime: Daily/Weekly/Monthly **Tracker only**. Daily: 19:00–03:00 NY source frame → native tiers/AU → 03:00–19:00 slot × tier range-left. Weekly/monthly: versioned anchor/rekey/tracker fields only where canonical definitions exist. Protect: BTC Tracker ≠ BTC Game; no Gold Game setup import; >$3,000 Asian-range no-go for the recovered native calibration. |
| III.3.6 | Fib / Range Birth runtime: range-birth eligibility → A/B active range → Alpha/Beta/Gamma/Delta sequence → coordinate/path → rekey/new range. Until R15 exact eligibility is canonicalized: explanation/research state allowed; production setup generation gated; no generic pivot fallback; no automatic anchor invention; coordinate availability ≠ structural eligibility. |
| III.3.7 | JPY Carry Game runtime: basket role state — USDJPY carry master; AUDJPY risk/execution expression; EURJPY confirmation/veto; pair-native daily/weekly tiers; role agreement and local state returned separately. Protect: no equal-vote majority; confirmation ≠ entry; historical 12–4 PM DT geometry not auto-merged; manual operator classification until parity approved; no invented aggregate score. |
| III.3.8 | Model registry/dispatch: resolve `model_id + version` explicitly; no "latest" without a version policy; historical requests can pin historical generation; unknown/unavailable versions fail closed. |
| III.3.9 | Deterministic replay: identical normalized inputs + identical model version ⇒ identical output hash; stable hashing; test previous-state handling, ordered transitions, version drift, clock identities and evidence-link stability; replay never silently substitutes current rules for historical versions. |

Plus the applicable cross-model invariants (#1 data clock is part of
model identity; #2 calibration local; #3 range/anchor before
coordinates; #4 tier is compression; #5 time weights state; #6 touch ≠
acceptance; #7 reach ≠ trade win; #8 first delivery/path; #9 rekey is a
remapping transition; #10 range-left; #11 L3 ≠ L2 ≠ L1; #12 model state
≠ setup; #13 setup ≠ automation approval; #14 manual valid strategy can
coexist with failed automation parity; #15 negative evidence queryable;
#16 historical claims ≠ current verified performance; #17 news
conditions geometry; #18 no deterministic rhetoric in status labels),
the packet's 15 governance invariants (§4 of the BA-19 authorization),
the failure-behavior clauses that land on this layer, gate §Models, and
the final-record fields III.3 owns (**model runtime versions/hashes**,
plus III.3's **golden fixture manifest hashes** feeding the book-level
golden fixture hashes, and III.3's **test counts** contribution).

## 3. Scope exclusions (out — never in this Bloc)

- No state snapshots, transition vocabulary, transition history,
  first-delivery tracking, failure/repair grammar, layer-handoff
  machinery or no-go *state engines* (III.4). The runtime emits
  bounded, immutable per-call states; anything that requires III.4
  transition ownership is a **bounded state/interface proposal**, never
  an unauthorized implementation.
- No setup objects, eligibility gates, triggers, invalidations or
  targets as trading objects (III.5). `production_authorization` on the
  output is a *classification fact* (RESEARCH_ONLY / MANUAL_OPERATOR /
  NOT_AUTHORIZED), not an eligibility grant; automation approval
  remains III.5 + governance.
- No API/endpoints/caching/serving (III.6); no snapshot identity keys.
- No persistence, no new migration; the container readiness seam
  `market_data: NOT_CONFIGURED` (`app/forge/service/container.py`) is
  not modified (Book II D4 boundary; III.1/III.2 carried it unchanged).
- No live provider network calls, credentials or SDKs; inputs arrive as
  III.1/III.2 contract objects over committed fixtures only.
- No Book I corpus writes, no exposure/policy changes, no HTTP surface.
- No modification of any frozen Book I/II file (50-file Book II freeze
  manifest + 23 planning pins + Book I freeze manifest), **no
  modification of any III.1 ratified file** (11 modules) and **no
  modification of any III.2 ratified file** (12 modules) — hashes
  recorded in §6 as the interface-integrity baselines.
- No statistical fitting, no probability/confluence/confidence output,
  no performance metrics (win rate, expectancy, RR) anywhere in the
  package; no autonomous ST engine; no unvalidated BTC Game; no
  arbitrary Fib anchor generator (Book III exclusions restated).
- No fixture generators, test implementations, migrations or API
  endpoints **in this rung** — only this PLAN.md and ACCEPTANCE.md are
  created now.

## 4. Phase 0 foundation (verified at this head; summary)

`HEAD == origin/forge == f9dce4f2d612f447bd8d2fa9c659a926cab65235`
(expected starting SHA of this packet, fast-forward ancestry confirmed
after fetch); tracked tree clean except the pre-existing untracked
`.bu_tmp/` (preserved untouched); planning freeze `60e0675` ancestor.

- Book I freeze manifest matches HEAD; corpus untouched; Book I I.5
  RATIFIED (CLOSED).
- Book II **RATIFIED — CONTRACTS FROZEN**: all **50/50** manifest
  hashes verify byte/EOL-identically at this head, all **23/23**
  planning pins content-verify against their pinned commits.
- Bloc III.1 **RATIFIED — PASS (CLOSED)** (`2aafef9`, BA-17): all 11
  module hashes recorded in III.2 PLAN §6 re-verify at this head.
- Bloc III.2 **RATIFIED — PASS (CLOSED)** (BA-18: PLAN `9b7def3` →
  fixtures `d372a8e` → package `ae08cb1` → tests `065a91d` →
  EVIDENCE/RATIFICATION `a49426e` → CI record `f9dce4f`): focused suite
  87/87, full regression 1168 passed / 29 pre-existing Postgres-gated
  skips, final-head CI run `39452676069` green on `test` + live-pgvector
  `postgres`; committed evidence pack + PASS—CLOSED record present; the
  12 measurement-module hashes recorded in §6 below re-verify at this
  head.
- Migrations `[1, 2, 3, 4]`; readiness seam `market_data:
  NOT_CONFIGURED` byte-identical; CI on the final head green (both
  jobs).
- Actual III.1 and III.2 Python APIs inspected by import and
  introspection this head (public `__all__` surfaces, signatures,
  registries — summarized in §6), not merely via agent reports.
- Carried gap registers acknowledged: III.1 GAP-1…5, III.2-GAP-1…6
  (dispositioned for III.3 in §10).
- Phase-order governance disposition resolved (Phase C in progress; no
  circular dependency; nothing downstream of III.3 has started).

**Foundation-readiness verdict: READY.** No missing prerequisite.

## 5. Dependency, ownership and canonical-source/authority matrix

### 5.1 Upstream contracts

| # | Upstream contract | Owner | Frozen status | How III.3 uses it | Ready? |
|---|---|---|---|---|---|
| D1 | III.1 `app/forge/market_data/` (instruments, bars, clocks, research_day, sessions, quality, normalize, parity, versions, errors) | Book III.1 (BA-17) | Ratified PASS — CLOSED at `2aafef9`; 11-module hashes in §6 | Consumed **read-only**: instrument identity + native units, final bars where a family consumes a bar window, clock/session identities, research-day ownership, quality vocabulary/outcomes, `MARKET_DATA_SCHEMA_V1` / `CLOCK_REGISTRY_V1` / `SESSION_REGISTRY_V1` versions as model-identity inputs (invariant #1). No redefinition, no wrapper reinterpretation | ✅ |
| D2 | III.2 `app/forge/measurements/` (contracts, ranges, calibration, coordinates, anchors, state_age, path_metrics, events, higher_order, errors, versions) | Book III.2 (BA-18) | Ratified PASS — CLOSED at `f9dce4f`; 12-module hashes in §6 | Consumed **read-only**: `Measurement` envelopes and typed measurements (`RangeMeasurement`, `TierClassification`, `AuScaleMeasurement`, `ThresholdLevelsMeasurement`, `SpatialBandClassification`, `AnchorEligibility`, `CoordinateProjection`, `ElapsedSinceEvent`, `CheckpointReached`, `TimeToDelivery`, `SessionPhase`, `PeriodPhase`, `PathMeasurement`, `EventBudget`/`EventFeatures`, `SeedRange`, `D1D3State`, `M1Scale`, `M2Shaping`, `UnfinishedSide`, `WeeklyPath`, `LayerConflict`), the calibration/coordinate/anchor registries, the bounded refusal codes and the unit-safe magnitude helpers. Model runtimes **interpret**; they never re-measure | ✅ |
| D3 | Canonical corpus (7 Model Cards, 10 Evidence Cards, 3 Setup Cards, taxonomy/crosswalk, schemas) | Book I | Frozen (23 pins) | Read-only citations by ID; every rule the runtime evaluates cites its canonical source; statistics are referenced by evidence ID only (the runtime stores **no** statistical parameters of its own); Setup Cards are referenced for boundary statements only — setup semantics belong to III.5; **no corpus writes** | ✅ |
| D4 | Book II platform patterns (frozen dataclasses, bounded typed errors, versioned records, redaction discipline) | Book II | Frozen (50-file manifest) | Structural precedent only — same record/refusal style; no Book II surface exercised (no HTTP/persistence/policy/observability touch) | ✅ (N/A directly) |
| D5 | Python stdlib (`Decimal`, `dataclasses`, `enum`, `hashlib`, `json`; `zoneinfo` reached via III.1 clocks) | stdlib/platform | Available | Pure deterministic computation and canonical serialization for replay hashing; **no new pip dependency** | ✅ |
| D6 | Fixture/manifest discipline (`FIXTURE_MANIFEST.json`, generator script, `SYNTHETIC_FIXTURE` labels, LF-normalized content hashes) | Book III.1/III.2 | Ratified | Pattern reused verbatim for III.3 golden fixtures (including the EOL-independence lesson from BA-17 repairs `5127fa7`→`8b43cb4`) | ✅ |

**Missing prerequisites: none.** Verdict: dependency-ready.

### 5.2 Model-family canonical-source / authority matrix

Every runtime family binds exactly these authorities; anything not in
this table is not a rule the runtime may evaluate.

| Ch | `model_id` @ `model_version` | Canonical Model Card | Layer(s) declared | Calibration binding (III.2 registry) | Coordinate set (III.2) | Evidence IDs (read-only refs) | Setup Card (III.5 boundary — referenced, never implemented here) | III.1 sessions/clocks used |
|---|---|---|---|---|---|---|---|---|
| III.3.1 | `EUR.DAILY.NEWS_REKEY.V1` @ `PHASE1` | `EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md` | L1 (local distribution-execution context) | `EUR_DAILY_PHASE1_TIERS` `V1` (`FROZEN_LAUNCH`) | `EUR_DAILY_100/125/132/168/185` | `EV.EUR.DAILY.PHASE1_TIERS.V1`, `EV.EUR.DAILY.NEWS_AUC.V1` | — (daily context feeds setups downstream) | Asian-range 19:00–03:00 research-day frame, daily checkpoints (where canonically defined) |
| III.3.2 | `EUR.WEEKLY.V1_1` @ `V1_1` | `EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md` | L2 (path) | `EUR_WEEKLY_TIER_RANGE` `V1` (`RESEARCH` — status travels with every output) | — (outer nodes via `WeeklyOuterNodeTable`) | `EV.EUR.WEEKLY.TIER_RANGE.V1` | — | Weekly-seed window, weekly/monthly period phases |
| III.3.3 | `EUR.HIGHER_ORDER.V1` @ `V1` | `EUR_HIGHER_ORDER_MODEL_CARD_V1.md` | L3 + cross-layer routing | none required (structure is evidence-bound; no statistical engine constants) | — | `EV.EUR.HO.D3_DIRECTION.V1`, `EV.EUR.HO.M1_RANGE_CORR.V1`, `EV.EUR.HO.UNFINISHED_M3.V1` | — | Quarter/month boundary sessions, weekly seed for handoff |
| III.3.4 | `XAU.GAME.L1_L2_L3.V1` @ `V1` | `XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md` (`CANONICAL_FROZEN_FAMILY`) | CROSS_LAYER (L3/L2/L1 typed separately) | `XAU_SPATIAL_BANDS` `V1` (explicit status; promoted examples cited) | `XAU_50/61.8/68/72/80/82/132` (+ declared `-50`) | `EV.XAU.PROMOTION.68_80.V1`, `EV.XAU.PROMOTION.120_132.V1` | `SETUP.XAU.QUARTER_ZONE.V1` (MANUAL_OPERATOR — no quarter-zone execution here) | Asian range, 03:00 NY boundary, daily checkpoints, week/quarter boundaries |
| III.3.5 | `BTC.TRACKER.DWM.V1` @ `V1` | `BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md` | CROSS_LAYER_CONTEXT | `BTC_TRACKER_DWM_TIERS` `V1` (`FROZEN_LAUNCH`; native $ tiers/AU/`trigger_levels`/density zones) | — | (card-cited constants; `EV`-linked statistics are evidence-gated per card) | — (no BTC setup card exists; **BTC Game does not exist**) | 19:00–03:00 NY source frame; 03:00–19:00 slot window; weekly/monthly boundaries where defined |
| III.3.6 | `CROSSASSET.FIB.RANGE_BIRTH.V1` @ `R15` | `FIB_RANGE_BIRTH_MODEL_CARD_V1.md` | L1_L2 | none (anchor rules are the gate; **`ANCHOR_RULE_REGISTRY` is empty** — R15 not materialized) | `FIB_50/61.8/68/72/80/82/132/168/185` + declared `FIB_NEG_25/50` | `EV.FIB.R11.ANCHOR_OVERGEN.V1` (negative evidence) | `SETUP.FIB.REKEY.V1` (RESEARCH_ONLY — production gated) | any instrument's registered clocks/sessions (cross-asset by design; calibration stays instrument-bound) |
| III.3.7 | `JPY.CARRY_GAME.L1_L3.V1` @ `V1` | `JPY_CARRY_GAME_MODEL_CARD_V1.md` | CROSS_LAYER (roles typed per pair) | pair-native tiers: **partially canonical** (III.2-GAP-2) — implemented only where canonical; DT structures carried in III.2 `jpy_dt_structures` fixture | `JPY_132/168` (+ declared `187.5`) under `DT_12_4PM` — **not consumed** by Carry states without explicit reference | `EV.JPY.CARRY.BASKET_RELATION.V1` | `SETUP.JPY.CARRY_ROLE_GATE.V1` (MANUAL_OPERATOR) | per-pair native clocks; DT window only when explicitly referenced |
| III.3.8 | registry across all of the above | each card above | declared per entry | resolved exactly per entry | per entry | per entry | — | — |
| III.3.9 | replay over all registered versions | — | — | — | — | — | — | clock/session registry versions pinned in the request identity |

Registry/version note (frozen requirement, recorded as data): the
calibration and coordinate registries key EUR Daily by
`model_version='PHASE1'`, EUR Weekly by `'V1_1'`, Fib by `'R15'`, JPY
DT coordinates by `'DT_12_4PM'`. The registry entries in §7.4 bind each
family's dispatch version to its exact calibration/coordinate key —
dispatch never re-derives a version and never falls back.

## 6. Existing implementation reuse + interface-integrity baselines

- `app/forge/measurements/` and `app/forge/market_data/` are consumed
  as-is; III.3 adds a **new** package `app/forge/model_runtime/` that
  touches no ratified file. There is no parallel-abstraction risk:
  neither upstream package contains any state-machine, registry-dispatch
  or replay code (verified by API inspection this head).
- Consumed primitives (actual APIs, inspected this head):
  III.2 `Measurement`/`MeasurementContext`/`Provenance`/
  `SourceWindow`, `measure_range`, `classify_tier`/`classify_spatial_
  band`/`measure_au_scale`/`measure_threshold_levels`/
  `measure_density_zones`, `evaluate_anchor`/`rekey_anchor`,
  `project_coordinates`, `elapsed_since`/`checkpoint_reached`/
  `time_to_delivery`/`measure_session_phase`/`measure_period_phase`,
  `measure_path`, `measure_event_budget`/`measure_event_features`,
  `measure_seed_range`/`measure_d1d3_state`/`measure_m1_scale`/
  `measure_m2_shaping`/`measure_unfinished_side`/`measure_weekly_path`/
  `measure_layer_conflict`, `CALIBRATION_REGISTRY`,
  `COORDINATE_SETS`, `ANCHOR_RULE_REGISTRY`, `DEFINITION_REGISTRY`,
  `MEASUREMENT_ENGINE_V1`, the bounded `MeasurementError` codes, and
  the unit-safe helpers (`add_magnitude`, `subtract_magnitude`,
  `scale_magnitude`, `native_span`, `quantize_ratio`) for any
  rule-declared derived quantity; III.1 `Bar`/`Instrument`/
  `NativePrice`/`convert_native`, `ClockIdentity`, `SessionRegistry`/
  `SessionResolution`, `ResearchDayRegistry`/`assign_research_day`,
  `QualityPolicy`/`QualityFlag`/`DataOutcome`, `Finality`/
  `final_state_input`, `MARKET_DATA_SCHEMA_V1`/`CLOCK_REGISTRY_V1`/
  `SESSION_REGISTRY_V1`, and the bounded `MarketDataError` refusal
  pattern.
- Reusable *patterns*: frozen dataclasses + bounded refusal codes;
  versioned registry objects; fixture manifest + generator +
  provenance README; the honesty-disclosure vocabulary
  (`NOT_CONFIGURED`, `GAP-n`, `RESEARCH`, `NOT_MATERIALIZED`); III.2's
  `RuleMaterialization` enum (CANONICAL / DECLARED / NOT_MATERIALIZED)
  reused verbatim for rule gating.
- Legacy Signal Guard code (`app/state_engine.py`, etc.) remains
  naive-timezone, not reusable, deliberately untouched.
- **III.1 interface integrity baseline** (planning-time `sha256` of the
  checked-out ratified modules; same reading as III.2 PLAN §6 — raw
  hashes bind the committed blobs as checked out on this Windows
  `core.autocrlf=true` checkout; EOL-normalized comparison for
  cross-platform verification):

  `__init__.py 7d57349b…11fd0` · `bars.py 97fc99e4…66366` ·
  `clocks.py 2698d527…ef172` · `errors.py 52f10816…6c88c` ·
  `instruments.py 8c6d6ad0…ed94d` · `normalize.py 04c4ecfc…d026b` ·
  `parity.py 0bb765af…8ce8c` · `quality.py 6b77c6df…58687` ·
  `research_day.py b5c82e40…d5307` · `sessions.py 037dbaaa…b77e5` ·
  `versions.py 9e502d7f…7842e` (verified 11/11 at this head; full
  64-hex values re-derivable with `sha256sum app/forge/market_data/*.py`
  and cross-checkable against III.2 PLAN §6).

- **III.2 interface integrity baseline** (same method; recorded here so
  the III.3 implementation rung can assert both upstreams unchanged —
  same mechanism, no new governance gate):

  `__init__.py 2b243dde…70bc2` · `anchors.py 227a17d1…94e5a` ·
  `calibration.py 62a53d65…22693` · `contracts.py 847074d8…52a69` ·
  `coordinates.py c224d775…70e23` · `errors.py 974fe1ae…f44ff` ·
  `events.py 30609310…af89e` · `higher_order.py 55406198…ce60d` ·
  `path_metrics.py f55dcc24…79743` · `ranges.py 1addf5d0…bdfed` ·
  `state_age.py 3c4e45f8…a65b5` · `versions.py f139b51c…31bd3`
  (verified 12/12 at this head).

- Implementation-compatible clarification (recorded per planning change
  control, no semantic change): canonical model-ID strings containing
  `GAME`/`CARRY_GAME` and the canonical BTC `trigger_levels` field are
  corpus vocabulary passed as data (III.2 precedent); the no-trading-
  concepts test in III.3 checks package identifiers, enum member values
  and dataclass field names exactly as III.2 did, with these disclosed
  literal-data exceptions and nothing else.

## 7. Proposed design (planning intent — implementation needs its own authorization)

### 7.1 Package layout (new; touches no ratified file)

`app/forge/model_runtime/`

| Module | Ch | Contents |
|---|---|---|
| `contract.py` | common | Frozen `ModelRequest` and `ModelOutput` envelopes (fields in §7.2); `Layer` enum (`L1`/`L2`/`L3`/`CROSS_LAYER`); `ProductionAuthorization` enum (`RESEARCH_ONLY`, `MANUAL_OPERATOR`, `NOT_AUTHORIZED`, `NOT_APPLICABLE`); `NoGoReason`/`WarningCode` bounded enums; `ExplanationFact(fact_id, rule_id, rule_version, source_ref, typed payload)` — structured facts, never prose; `DirectionBias` (typed side + basis fact, or explicit `NONE_DECLARED`); `TypedLevel(level_id, level_kind, family/level, price, active, source_ref)`; contract validation refusing inconsistent construction |
| `errors.py` | common | Bounded refusal vocabulary (§9): `ModelRuntimeError` base + `ModelContractError`, `ModelVersionUnavailableError`, `DataQualityBlockedError`, `NoCalculationError`, `InstrumentScopeMismatchError`, `PriorStateMismatchError`, `InputMeasurementMissingError`, `RuleNotMaterializedError`, `ReplayHashMismatchError`. Codes mirror the frozen Book III failure vocabulary; III.2 refusal codes are imported, never redefined |
| `registry.py` | III.3.8 | `ModelKey(model_id, model_version)`; `RegistryEntry(model_key, family, runtime_version, layer, market_scope, calibration_bindings, coordinate_set_keys, canonical_source_refs, stateful: bool)`; `MODEL_REGISTRY` (immutable mapping); `resolve(model_id, model_version)` exact-match only — unknown ⇒ `MODEL_VERSION_UNAVAILABLE`; **no `latest()`, no default version parameters, no implicit fallback anywhere**; version-pinned historical resolution returns the registered historical entry (retired generations stay registered, never silently upgraded) |
| `replay.py` | III.3.9 | `run_model(request) -> ModelOutput`; canonical serialization (sorted keys, compact separators, `Decimal`→string, enum→value, LF, UTF-8) → `sha256` → `output_hash`; `verify_replay(request, expected_hash)`; hash covers model key + runtime version + input identity versions (market-data/clock/session/measurement) + clock/session IDs + injected calculation timestamp + prior-state ref + all output fields. Ordered-transition handling: a stateful family consumes `prior_state` only when its `model_version` matches exactly (else `PRIOR_STATE_MISMATCH`); replay never re-derives a rule under a different version |
| `eur_daily.py` | III.3.1 | `EurDailyInputs` (seed `RangeMeasurement`, tier `TierClassification` or seed magnitude + calibration key, path `PathMeasurement` (consumed states), `EventFeatures`/`EventBudget` optional, rekey/extension facts from `AnchorEligibility`/`rekey_anchor`, session phase/checkpoint measurements, quality state); `evaluate(request) -> ModelOutput`. Rule chain: Asian seed → tier (incl. >45p no-go as `NoGoReason.AR_SOURCE_NO_GO`) → distance/asymmetry facts (declared rule ids over III.2 magnitude helpers) → consumed states → event conditioning (budget subtractive; conditioning field only) → rekey/extension state (REKEYED = remapping, ladder 100/125/132/168/185 as distinct states) → remaining distribution (`range_left` + distribution state, `UNRESOLVED` when unsupported). News conditioning never mutates geometry fields (structurally separate field) |
| `eur_weekly.py` | III.3.2 | `EurWeeklyInputs` (Monday/early-week seed `SeedRange`, weekly tier classification, hour×tier timing via `SessionPhase`/`PeriodPhase`, consumed node facts, OCC/completion flag, higher-order context ref optional); `evaluate(...)`. Outer-node promotion only (promoted node flag from `WeeklyOuterNodeTable`); completion/freeze ⇒ `frozen_structure: true` output (static thereafter); `destination_evidence` field is structurally `NOT_THIS_LAYER` — weekly path facts can never populate it; `RESEARCH` calibration status travels on every output |
| `eur_higher_order.py` | III.3.3 | `HigherOrderInputs` (quarter seed, D1–D3 `SeedRange`s, `M1Scale`, `M2Shaping`, `UnfinishedSide`, M3/completion facts, weekly seed/path for handoff); `evaluate(...)`. L3 destination prior typed as direction + basis fact with evidence refs (never a percentage field); unfinished-side completion ⇒ conditional destination evidence state; `LayerConflict` facts pass through as facts (no score field exists); missing statistical parameters ⇒ state `UNRESOLVED`, never invented |
| `xau_game.py` | III.3.4 | `XauGameInputs` (L3 destination state ref, L2 route/pace/clock measurements incl. Tuesday pace + delivery clocks + range-left, L1 Asian tier/spatial band + relative consumption, elapsed-since-state via `elapsed_since`, parked flag, quality); `evaluate(...)`. Promotion rules as pure typed functions: band `68` + elapsed ≥ 8h ⇒ `ELIGIBLE_80` (evidence ref `EV.XAU.PROMOTION.68_80.V1`); band `120` + elapsed ≥ 8h ⇒ `RESEARCH_SMALL_N_132` (flag preserved; evidence ref `EV.XAU.PROMOTION.120_132.V1`); **132 state has no transition to 168** (absence by construction + test); `parked` input can never be cleared by any promotion path (parked ⇒ output stays parked / `NO_GO`); L2 fields contain no entry/execution vocabulary (no setup objects; quarter-zone doctrine is III.5); layer inputs are separately typed so L1 can never populate L3 |
| `btc_tracker.py` | III.3.5 | `BtcTrackerInputs` (19:00–03:00 NY source-frame `RangeMeasurement`, native tier/AU/threshold measurements, 03:00–19:00 slot × tier context, session/clock identities, optional weekly/monthly facts); `evaluate(...)`. Daily chain reproduces slot × tier range-left; >$3,000 ⇒ `ASIAN_RANGE_NO_GO`; weekly/monthly sub-states are `UNRESOLVED`/`NOT_MATERIALIZED` interfaces unless a canonical anchor/rekey definition exists (§10 GAP-8); registered only under `BTC.TRACKER.DWM.V1` — any Game-like request fails `MODEL_VERSION_UNAVAILABLE`; static import discipline keeps `xau_game.py`/`jpy_carry.py` out of this module; output contains no setup/Game object (structural field scan + fixture) |
| `fib_range_birth.py` | III.3.6 | `FibRangeBirthInputs` (anchor `AnchorEligibility`, A/B range refs, sequence-family fact, coordinate projections, rekey facts); `evaluate(...)`. Chain: eligibility → A/B → Alpha/Beta/Gamma/Delta → coordinates/path → rekey/new range. Gate: anchor rule must be `CANONICAL` materialization — with the registry empty (R15 unmaterialized) the output is research/explanation state with `RuleNotMaterializedError` refusal for any eligibility-bearing request; `production_authorization = RESEARCH_ONLY`/`NOT_AUTHORIZED` always at this stage; no anchor generator, no automatic anchor invention; a request with coordinates available but unmaterialized rule still refuses (coordinate availability ≠ structural eligibility); rekey = structural remapping (prior → successor mapping recorded) |
| `jpy_carry.py` | III.3.7 | `JpyCarryInputs` (per-pair: tier/no-go state, local path/geometry facts, session/clock identity — three explicit roles); `evaluate(...)`. Output carries `master_state` (USDJPY), `expression_state` (AUDJPY), `confirmation_state` (EURJPY: CONFIRMED / VETO / ABSENT), plus per-pair local states — **separately, never merged**: no aggregate score/majority field exists in the output structure (equal-vote impossible by construction); confirmation never populates a local-entry field (confirmation ≠ entry); native tier no-go per executed pair; DT `12–4 PM` coordinate set and structures are not consumed unless the request explicitly references the DT family (no silent merge); `production_authorization = MANUAL_OPERATOR` (manual classification in force until parity approved) |
| `versions.py` | final record | `MODEL_RUNTIME_VERSION = "MODEL_RUNTIME_V1"` (Book III final-record field) |
| `__init__.py` | — | bounded public surface re-exporting the contract, registry, replay and family evaluators |

Cross-cutting rules for the future implementation: pure functions +
frozen dataclasses; `Decimal` in asset-native units (never float,
never cross-unit without III.1 `convert_native`); injected calculation
clock (no wall time); no network; no file I/O; no imports from `qa/`,
`retrieval/`, `app/forge/provenance.py`, `canonical.py`, `policy.py`,
`service/`, `providers/`, `persistence/`, `observability/`,
`backfill/`, or any frozen/ratified file; the only absolute `app.*`
imports are `app.forge.market_data` and `app.forge.measurements`;
`ForgeServiceContainer` never appears; outputs immutable; every output
carries model key + runtime version + input identity versions
(`market_data_schema_version`, `clock_registry_version`,
`session_registry_version`, `measurement_engine_version` — cross-model
invariant #1: data clock is part of model identity).

### 7.2 Common model contract (frozen field set)

`ModelRequest` (inputs):

1. `model_id` + `model_version` — explicit, both required, **no
   defaults** (III.3.8).
2. `instrument_id` — scope-checked against the family's market scope
   (cross-asset leakage refuses).
3. Family-typed measurement bundle (`EurDailyInputs`, …) — III.2
   measurement objects only; a required measurement that is absent is
   never synthesized.
4. `prior_state: ModelOutput | None` — previous model state where
   applicable (stateful families), version-checked (III.3.9).
5. `calculation_timestamp` — injected, never wall time.
6. `calibration_key` — instrument + asset-native calibration lineage,
   bound exactly as registered (§5.2); cross-instrument transfer
   refuses.
7. Identity versions: `market_data_schema_version`,
   `clock_registry_version`, `session_registry_version`,
   `measurement_engine_version`, `model_runtime_version` — all
   asserted, not inferred.
8. `clock_id` / `session_id` where the family's grammar is clock-bound;
   unresolvable ⇒ `NO_CALCULATION`.

`ModelOutput` (outputs):

1. `model_id`, `model_version`, `model_runtime_version`,
   `output_hash` (canonical replay hash).
2. `model_state` — family-bounded enum value (no free text).
3. `layer` — declared layer of this state (`L1`/`L2`/`L3`/
   `CROSS_LAYER`), with per-layer sub-states where the family is
   layered (XAU, JPY).
4. `direction_bias` — typed side + basis fact **only where canonically
   defined**; otherwise explicit `NONE_DECLARED` (EUR Daily is not a
   direction oracle).
5. `active_ranges` / `active_anchor_states` — references to III.2
   outputs (anchor status verbatim: UNRESOLVED/ELIGIBLE/ACTIVE/
   INVALIDATED/REKEYED).
6. `levels` — typed levels/coordinates with source refs and
   active/inactive state (projection authority stays in III.2).
7. `range_left` / distribution fields — where source-supported;
   explicit `UNRESOLVED` otherwise; always conditioned on consumed
   states (invariant #10).
8. `no_go` (bounded reason codes) + `warnings` (bounded codes).
9. `claim_refs` / `evidence_refs` — canonical IDs, read-only.
10. `quality_state` — frozen III.1 vocabulary.
11. `production_authorization` — classification fact
    (`RESEARCH_ONLY` / `MANUAL_OPERATOR` / `NOT_AUTHORIZED` /
    `NOT_APPLICABLE`), **structurally distinct from** `model_state`
    (descriptive state ≠ production authorization).
12. `explanation_facts` — structured `ExplanationFact`s (rule id +
    version + source ref + typed payload), never generated prose.
13. Input-identity envelope (fields 5–8 of the request, echoed).

Structurally excluded (no field can carry them): probabilities,
confidence/confluence scores, win rates, expectancy/RR, predictions,
signals, prose, entry/trigger/invalidation/target objects.

### 7.3 Family dependency map (what each family consumes)

| Family | III.2 inputs | III.1 inputs | Prior state? | Key protection |
|---|---|---|---|---|
| EUR Daily | `RangeMeasurement`, `TierClassification`, `PathMeasurement`, `EventFeatures`/`EventBudget`, `AnchorEligibility`/rekey, `SessionPhase`/checkpoints | Asian-range session def, research-day lineage, `QualityPolicy` | yes (rekey/consumed chain within day) | >45p no-go; ladder identity; news modifies, never replaces; slot × tier/range-left |
| EUR Weekly | `SeedRange(WEEK)`, `TierClassification`, `WeeklyPath`/`WeeklyOuterNodeTable`, `SessionPhase`/`PeriodPhase` | weekly-seed session, period phases, clock versions | yes (completion/freeze) | outer-node promotion only; frozen after completion; no destination laundering |
| EUR Higher Order | `SeedRange(QUARTER/MONTH)`, `D1D3State`, `M1Scale`, `M2Shaping`, `UnfinishedSide`, `WeeklyPath`, `LayerConflict`, HO checkpoints | quarter/month boundary sessions, weekly seed session | yes (M3 resolution across calls) | L3 authority; stats via evidence refs only; no invented parameters |
| XAU | `SpatialBandClassification`, `TierClassification`, `RangeMeasurement`, `PathMeasurement`, `ElapsedSinceEvent`, higher-order refs | Asian range, 03:00 boundary, delivery-clock sessions | yes (promotion aging, parked flag) | 68+8h/120+8h rules verbatim; no 132→168; parked stays parked; L2 ≠ entry |
| BTC Tracker | `RangeMeasurement`, `TierClassification`, `AuScale`/`ThresholdLevels`/`DensityZone`, slot context, `AnchorEligibility` (weekly/monthly, when canonical) | 19:00–03:00 NY frame, 03:00–19:00 slots, weekly/monthly boundaries | limited (daily chain) | Tracker ≠ Game; >$3k no-go; no Gold setup import; weekly/monthly unresolved until canonical |
| Fib Range Birth | `AnchorEligibility`, `RangeMeasurement`, `CoordinateProjection`, `rekey_anchor` outputs | any registered instrument clock/session | yes (rekey/remapping chain) | R15 gate; no pivot fallback; coordinates ≠ eligibility; production blocked |
| JPY Carry | per-pair `TierClassification`, path/geometry facts, `SessionPhase` | three pair clocks/sessions; DT window only if referenced | no (stateless per call + prior optional) | roles separate; no equal vote; no DT auto-merge; MANUAL_OPERATOR |

## 8. Proposed executable test matrix (summary; full clause→test map in ACCEPTANCE.md)

Proposed file: `tests/test_forge_model_runtime.py` (golden fixtures
under `implementation/forge/book_iii/bloc_iii_3/fixtures/`). All
deterministic, offline, network-free.

| Group | Frozen driver | Representative proposed tests |
|---|---|---|
| T1 Common contract | common contract; invariants #1/#12/#13 | frozen request/output field sets; explicit model/version with no default; descriptive state vs `production_authorization` distinct fields; no probability/confidence/WR/expectancy field exists on any output (AST + field scan); structured `ExplanationFact` with rule id/version (no prose, no generated narrative); direction explicit `NONE_DECLARED` where canonically undefined; quality state + input identity versions on every output; outputs immutable |
| T2 Registry/dispatch | III.3.8 | exact `model_id + version` resolution for all 7 families; unknown id **and** unknown version ⇒ `MODEL_VERSION_UNAVAILABLE` (fail closed); no `latest`/default-version API exists anywhere; version-pinned historical generation returns the registered historical entry (never silently upgraded); wrong calibration binding for a version refuses; `MODEL_RUNTIME_V1` recorded on outputs |
| T3 EUR Daily | III.3.1 | seed → tier → distance/asymmetry → consumed → event → rekey → remaining-distribution chain reproduces fixtures; **>45p source no-go** (boundary edges); 100/125/132/168/185 states distinct (never collapsed); news conditioning changes only the conditional field, geometry fields byte-identical (**news never replaces geometry**); slot × tier range-left semantics; subtractive event budget consumed; no statistic fields without evidence ref |
| T4 EUR Weekly | III.3.2 | Monday seed → weekly tier → route/range-left → hour × tier timing → outer-node state chain; **outer-node promotion only** (inner node cannot promote); completion/freeze ⇒ frozen/static flag stable across re-evaluation; `destination_evidence` stays `NOT_THIS_LAYER` (**weekly path never laundered into destination**); `RESEARCH` calibration status travels; no weekly route statistics emitted as win rates |
| T5 EUR Higher Order | III.3.3 | quarter seed → D3 prior → M1 scale → M2 shaping → M3 resolution → weekly handoff chain; **L3 destination authority** (destination field populated only from L3 inputs); unfinished-side ⇒ conditional destination evidence; D3 agreement/completion statistics absent as fields (evidence IDs only — **not trade WR**); M1 correlation not probability (no probability field); layer conflict ⇒ `LayerConflictFact` list, **no confluence score possible**; missing statistical parameter ⇒ `UNRESOLVED`, never invented |
| T6 XAU Game | III.3.4 | L3/L2/L1 sub-states typed separately (L1 input cannot populate L3 field — **authority leakage**); 68 + 8h ⇒ eligible-promotion-to-80 state (elapsed injected); 120 + 8h ⇒ 132 **research/small-N** state with flag; **132 state never yields 168** (assert absence); **parked input ⇒ parked output under every promotion path**; L2 state contains no entry/execution fields (**L2 ≠ direct entry**); no quarter-zone execution object exists |
| T7 BTC Tracker | III.3.5 | 19:00–03:00 source frame → three native tiers (each boundary edge) → 03:00–19:00 slot × tier range-left; **>$3,000 no-go** for the recovered calibration; output contains no Game/setup object (**BTC Game contamination** request ⇒ `MODEL_VERSION_UNAVAILABLE`; static import check: no XAU/JPY setup source reachable; output field scan clean); weekly/monthly ⇒ `UNRESOLVED` interface with no invented anchors; **cross-asset contamination**: BTC calibration refuses a foreign instrument (and vice versa) |
| T8 Fib Range Birth | III.3.6 | born range (ELIGIBLE/ACTIVE anchor) ⇒ A/B → sequence → coordinates → path chain; **unresolved R15** ⇒ `RULE_NOT_MATERIALIZED` refusal / research-explanation state; production authorization stays `RESEARCH_ONLY`/`NOT_AUTHORIZED` (**production setup generation blocked**); **arbitrary local pivot rejected**; coordinates available but rule unmaterialized ⇒ still blocked (coordinate availability ≠ structural eligibility); rekey transition = structural remapping with prior→successor mapping |
| T9 JPY Carry | III.3.7 | three role states returned separately (master/expression/confirmation) with pair-native calibration; agree + confirm case; **confirm absent ⇒ veto state**; native-tier no-go per pair; **equal-vote violation impossible**: no aggregate/majority/score field exists in the output structure and a three-pair-vote request refuses; confirmation never populates local state (**confirmation ≠ entry**); DT 12–4 PM geometry absent from carry outputs unless explicitly referenced; `MANUAL_OPERATOR` authorization preserved |
| T10 Golden fixtures + replay | III.3.9 + golden program + Acceptance III.3 (b)(e) | all golden state fixtures reproduce (EUR daily/rekey/event; weekly outer-node; HO D3/M1/M2/M3 handoff; XAU all five cases; BTC four cases; Fib four cases; **JPY basket four cases incl. agree+confirm / confirm-absent / no-equal-vote** — claimed here per III.2 J8 deferral); fixture manifest hashes recorded (LF-normalized); synthetic labels honored; **identical input + identical version ⇒ identical hash** (repeat runs); ordered transitions (state-chain order changes hash/state — replays are order-sensitive); **version drift**: same input under a different registered version ⇒ different pinned output; unregistered version ⇒ fail closed (replay never substitutes current rules); prior-state version mismatch ⇒ `PRIOR_STATE_MISMATCH`; **clock identity** participates in the hash (same instants under different clock identity ⇒ different identity/hash); **evidence-link stability** across repeat runs; **nondeterministic replay** attempt (mutated timestamp/prior state) ⇒ hash mismatch detected |
| T11 Label/serialization/authority discipline | Acceptance III.3 (c)(d); invariants #3/#11/#12/#16/#18 | no prediction/signal/probability vocabulary in enums, fields or serialized payloads; structured facts survive serialization round-trip; **cross-asset contamination** of inputs refuses (`INSTRUMENT_SCOPE_MISMATCH`); **incorrect model versions** fail closed (T2 cross-ref); **missing evidence** ⇒ state may exist, no unsupported statistic; **nonfinal source data** (blocking quality flag on input) ⇒ `DATA_QUALITY_BLOCKED`; L3/L2/L1 leakage structurally impossible; model state ≠ trade eligibility (no setup/eligibility fields anywhere); status labels factual only (no deterministic rhetoric); negative/unresolved states remain visible (no default-empty success) |
| T12 Boundaries | §3 exclusions; Book gate | no network (socket refusal guard); import discipline (only `market_data` + `measurements` absolute app imports; no Book I/II authority modules; no container); no corpus writes (Book I manifest vs HEAD + `git status corpus/` clean); fixtures labeled historical; `discover_migrations() == [1, 2, 3, 4]` (no `005_*`); readiness seam `market_data: NOT_CONFIGURED` identical; Book II 50 hashes + 23 pins + Book I manifest + III.1 11-module hashes + III.2 12-module hashes unchanged after the suite; deterministic repeat runs; no credentials/PII; no trading/game concepts (disclosed canonical literal-data exceptions only); diff scope limited to `book_iii/bloc_iii_3/`, `app/forge/model_runtime/`, `tests/test_forge_model_runtime.py` |

Golden-fixture plan (frozen program → III.3 claim):

| Fixture file | Frozen program cases claimed here |
|---|---|
| `eur_daily_states.json` | T1/T2/T3/no-go daily seed states; rekey/extension states (100/125/132/168/185); event-conditioned states (budget subtractive; geometry unchanged) |
| `eur_weekly_states.json` | Weekly outer-node path; frozen-after-completion case; not-destination-evidence case |
| `eur_higher_order_states.json` | D3/M1/M2/M3 handoff; unfinished-side completion; layer-conflict-no-score case |
| `xau_promotion_states.json` | normal state; 68+8h promotion; 120+8h small-N promotion; 132 state proving no automatic 168; parked-stays-parked; L2-not-entry context (touch-only cannot reach confirmation state) |
| `btc_tracker_states.json` | all three native Asian tiers; >$3,000 no-go; slot × tier range-left; proof Tracker output contains no invented Game setup |
| `fib_range_birth_states.json` | valid born range; unresolved anchor (R15); rekey transition; arbitrary local pivot rejected |
| `jpy_carry_states.json` | USDJPY/AUDJPY agree + EURJPY confirm; confirm absent (veto); no-go native tier; proof no equal-vote aggregation |
| `registry_dispatch_cases.json` | known versions resolve; unknown version fails closed; version-pinned historical generation |
| `replay_hashes.json` | expected canonical output hashes per case (golden hash reproduction + drift cases) |
| `generate_fixtures.py`, `FIXTURE_MANIFEST.json`, `README.md` | deterministic generator; LF-normalized sha256 manifest (EOL-independent); provenance labels — bar windows reuse committed III.1/III.2 fixture slices read-only where possible; any new bars are `SYNTHETIC_FIXTURE` from creation |

Historical/manual program cases (**ST manual explanation + automation
flag false; P90 version identity**) are **not** runtime-representable —
no canonical MODEL objects exist for ST/P90 (they are lineages inside
cards and belong to chapters III.5.9/III.5.10). III.3 re-discloses
III.2's J8 deferral as *deferred to III.5*; neither bloc claims them.

Synthetic fixtures are contract tests, not empirical performance
evidence.

## 9. Failure and security matrix

| Condition (frozen) | Required behavior | Test |
|---|---|---|
| Incomplete/nonfinal input data | `DATA_QUALITY_BLOCKED` (or model-declared degraded state via III.1 `QualityPolicy`) — never a fabricated or default state | T11, T1 |
| Clock/session cannot be resolved | `NO_CALCULATION` — explicit, not empty-success | T1, T3 |
| Model version missing/unknown | `MODEL_VERSION_UNAVAILABLE` — fail closed, no fallback, no "latest" | T2, T11 |
| Required measurement absent | `INPUT_MEASUREMENT_MISSING` — never synthesized from nothing | T1, T11 |
| Instrument outside family scope / cross-asset calibration | `INSTRUMENT_SCOPE_MISMATCH` (calibration transfer refuses — invariant #2) | T7, T11 |
| Prior state incompatible (version/identity drift) | `PRIOR_STATE_MISMATCH` — never silent adoption of a foreign state | T10 |
| Evidence missing for a statistic | state may exist when its rule is canonical, but **no unsupported statistic is attached** (no statistical fields exist) | T1, T11 |
| Higher/lower layers conflict | conflict/state facts only — never an invented confluence score | T5, T1 |
| Rule not materialized (R15 Range Birth) | `RULE_NOT_MATERIALIZED` / research-explanation state; production authorization stays blocked | T8 |
| Replay hash mismatch | `REPLAY_HASH_MISMATCH` — replay never substitutes current rules for historical versions | T10 |
| Inconsistent contract construction | `MODEL_CONTRACT` — bounded refusal | T1 |
| Provider/feed failure | runtime consumes only III.1/III.2 contract objects — no feed path exists here; stale *serving* is III.6 product policy — review: recorded in EVIDENCE | review |
| Frozen-surface drift (Book I/II **and** III.1/III.2) | manifest-hash tests over 50 Book II hashes + 23 planning pins + Book I manifest + 11 III.1 + 12 III.2 module hashes — unchanged after the suite | T12 |
| Secrets/PII in the data path | none: no credentials, bounded enums, no free-text payload | T11, T12 |

## 10. Known gaps and stop conditions

Known gaps (recorded, not hidden):

- **III.3-GAP-1 (carries III.2-GAP-1 / III.1 lineage)** — Canonical
  Fib **R15 Range Birth eligibility rule is not materialized**
  (`ANCHOR_RULE_REGISTRY` is empty at this head). III.3.6 implements the
  full state chain *behind the gate*: research/explanation states are
  produced when supported; every eligibility-bearing request refuses
  with `RULE_NOT_MATERIALIZED`; production setup generation stays
  blocked. **Affects:** III.3.6 (partial: interface + research states
  only). **Closes when:** governance materializes the exact R15 rule
  (canonical source + evidence) and registers the anchor rule.
  **Blocks:** Fib production classification and downstream automation —
  *not* III.3 ratification (the frozen plan explicitly allows
  explanation/research state meanwhile).
- **III.3-GAP-2 (carries III.2-GAP-2)** — JPY pair-native daily/weekly
  tier tables only partially canonical; latest Pine/manual parity not
  established (manual classification in force). **Affects:** III.3.7
  (role states + basket gating fully implementable; per-pair tier
  interpretation only where canonical). **Closes when:** operator
  supplies canonical per-pair tier/AU tables **and** approves parity.
  **Blocks:** JPY automation parity claims — not III.3 ratification;
  `MANUAL_OPERATOR` stands.
- **III.3-GAP-3 (carries III.2-GAP-3)** — XAU calibration is spatial
  bands + promoted examples + doctrine, not an EUR-style tier table;
  promotions 68+8h→80 (`VALIDATED_SMALL_N`) and 120+8h→132
  (`RESEARCH_FLAG_SMALL_N`, N=25) are evidence-linked states. **Affects:**
  III.3.4 (fully implementable as evidence-linked, flag-preserving
  states; never as guarantees). **Closes when:** a canonical frozen XAU
  tier table (if ever) is ratified. **Blocks:** presenting promotions as
  universal rules — never III.3 ratification.
- **III.3-GAP-4 (carries III.2-GAP-4)** — No event/news historical
  calendar in-repo. **Affects:** III.3.1 event-conditioning states over
  synthetic labeled events only. **Closes when:** operator supplies
  canonical EUR event-history slices. **Blocks:** real-history news
  conditioning claims — not III.3 ratification (contract tests only).
- **III.3-GAP-5 (carries III.2-GAP-6)** — Higher-order statistical
  parameters are evidence-bound ("definitions must travel with
  evidence"). **Affects:** III.3.3 — structure/hierarchy fully
  implementable; statistics referenced by evidence ID only, emitted
  nowhere as values. **Closes when:** exact D3/unfinished-side/
  completion definitions + evidence attachments are materialized.
  **Blocks:** researcher-mode numerical display (Book IV concern) — not
  III.3 ratification.
- **III.3-GAP-6 (carries III.1 GAP-1 / III.2-GAP-5)** — No real
  historical bar slices in-repo; golden state fixtures build on
  synthetic-labeled committed slices + canonical constants cited by ID.
  **Affects:** all families' fixtures (contract tests, never
  performance evidence). **Closes when:** operator supplies canonical
  bar slices. **Blocks:** any empirical/performance claim — not III.3
  ratification.
- **III.3-GAP-7 (carries III.1 GAP-2/GAP-3/GAP-4/GAP-5)** — Sessions
  only where canonically defined; final-bar rules beyond the canonical
  M5 example scoped to source lineage; provider seam
  `NOT_CONFIGURED`; scripted-streaming parity only. **Affects:** clock/
  session-bound family inputs (degrade to `NO_CALCULATION` explicitly).
  **Closes with** the same upstream operator decisions as III.1.
  **Blocks:** live-feed behavior claims — not III.3 ratification.
- **III.3-GAP-8 (new)** — BTC **Weekly/Monthly** canonical anchor/rekey
  definitions are not materialized (card: "exact promoted setup status
  remains evidence-dependent"). **Affects:** III.3.5 — daily lineage
  fully implementable; weekly/monthly only as explicit
  `UNRESOLVED`/`NOT_MATERIALIZED` interfaces (no invented anchors).
  **Closes when:** canonical weekly/monthly anchor/rekey definitions +
  evidence are ratified. **Blocks:** BTC weekly/monthly state
  classification — not III.3 ratification; never an invitation to
  import BTC Game.
- **III.3-GAP-9 (new)** — XAU "parked" and quarter-zone confirmation
  semantics originate in III.5 setup doctrine; at III.3 they exist only
  as bounded input flags + L1 context states that the runtime must
  respect but never clear. **Affects:** III.3.4. **Closes when:** III.5
  materializes the setup-card implementation. **Blocks:** setup
  eligibility emission (already out of scope) — not III.3 ratification.
- **III.3-GAP-10 (disclosure; re-states III.2 J8)** — ST manual /
  P90 version-identity golden cases are not runtime-representable
  (no canonical MODEL objects); **deferred to III.5.9/III.5.10**.
  Neither III.2 nor III.3 claims them.

Carried upstream: III.1 GAP-1…GAP-5 and III.2-GAP-1…GAP-6, dispositioned
family-by-family in §5.2/§10 — none is a prerequisite for planning or
for III.3 ratification; each blocks only the specific downstream claim
named above. **No missing research is promoted into runtime rules.**

Stop conditions (report, do not improvise):

1. Any frozen clause that cannot be implemented without contradicting a
   Book I/II frozen contract, the III.1/III.2 ratified interfaces, or by
   inventing a non-canonical rule/calibration/session/anchor → stop and
   report.
2. Any need to modify a frozen Book I/II file, any III.1/III.2 module,
   the container readiness seam, or add a migration → stop; governed
   packet required first.
3. Conflicting canonical sources (e.g., two rule definitions for the
   same family+version, or a fixture number contradicting a canonical
   constant) → operator/governance ruling required; never pick silently.
4. Any requirement to emit a probability, confluence score, confidence
   score, prediction, expectancy or performance metric from this layer →
   stop; that is a different Bloc's violation of the frozen plan.
5. Any runtime action requiring III.4 transition ownership or III.5
   setup authorization → bounded state/interface proposal only, never
   an unauthorized implementation.
6. Being blocked on III.3 does **not** authorize starting III.4 or any
   other Bloc without a new operator handoff — and this packet
   authorizes **planning only**: **STOP AFTER PLANNING.**

## 11. Acceptance / ratification requirements (this Bloc)

Per the frozen Book III gate §Evidence pack: `PLAN.md` (this file),
`ACCEPTANCE.md`, implementation commit ladder (later, separate
authorization), test output, `EVIDENCE.md`, known-gaps list, and a
ratification record — produced at implementation time. Clause→test
mapping is frozen now in `ACCEPTANCE.md`; any implementation must
satisfy it or report a deviation, never weaken it. The EVIDENCE at
implementation time must also re-verify **both** interface baselines
from §6 (11 III.1 + 12 III.2 module hashes), the Book II/Book I frozen
manifests, and disclose which golden-program cases are claimed here
versus deferred (§8: ST/P90 → III.5). The final record must publish
`model_runtime_version` (`MODEL_RUNTIME_V1`), the III.3 fixture
manifest hashes and the III.3 test counts.

## 12. Handoffs

- **To III.4 (next in frozen order):** model outputs are *facts* —
  immutable, versioned per-call states. Anything resembling a
  transition (rekey chains, promotion aging, completion/freeze) is
  currently computed within a call over `prior_state`; III.4 owns
  persistent transition vocabulary, history and snapshot semantics.
  The runtime's `no_go` reasons, `production_authorization`,
  `explanation_facts` and layer-typed states are the bounded
  **interface proposal** III.4/III.5 build on — nothing more is
  pre-authorized here.
- **To III.5:** `production_authorization` values are classification
  facts only; setup eligibility, triggers, invalidations and targets
  remain III.5's. Automation approval stays blocked for Fib (GAP-1) and
  unparity-approved for JPY (GAP-2).
- **To III.6:** outputs are deterministic functions of (request,
  version, prior state) — snapshot identity, caching and stale-serving
  policy are III.6 concerns; this bloc adds no serving.
- **To Book IV/V:** unchanged — facts not prose; this Bloc adds no
  prose generation, no API, no rendering, no advice. Ask CEREBUS
  consumes these facts under the answer contract and never recomputes
  model state inside the LLM.
