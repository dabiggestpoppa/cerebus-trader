# BOOK III PLAN — CEREBUS MARKET INTELLIGENCE

Status: DETAILED PLANNING V1
Date: 2026-10-05
Parent: GLX_FORGE_MASTER_BUILD_PLAN_V1
Depends on: Book I canonical contracts; Book II persistence/identity/policy/observability
Feeds: Books IV, V, VII, VIII

## Book objective
Turn canonical CEREBUS knowledge into deterministic market-intelligence services that calculate measurements, model state, path, levels and setup eligibility without allowing implementation convenience to rewrite research definitions.

Book III is the executable market brain beneath Ask CEREBUS and the Operator Interface.

It is NOT an autonomous trade executor.

## Core law
SOURCE BARS/EVENTS
-> NORMALIZED MARKET DATA
-> MEASUREMENTS
-> MODEL STATE
-> PATH/TRANSITION STATE
-> SETUP ELIGIBILITY
-> INTELLIGENCE SNAPSHOT/API

Every stage is inspectable and versioned.

A downstream layer may consume an upstream state; it may not silently redefine it.

---

# BLOC III.1 — MARKET DATA & CLOCK CONTRACTS

## Objective
Create one exact definition of what data CEREBUS received and which research day/session each observation belongs to.

### Ch III.1.1 Instrument identity
Canonical instrument schema:
- instrument_id
- symbol/provider aliases
- asset class
- quote/base conventions
- tick/pip/point unit
- price precision
- supported clocks/timeframes
- provider mappings.

Asset-native units are mandatory. EUR pips, Gold points and BTC dollars are not interchangeable.

### Ch III.1.2 Bar contract
Normalized OHLCV/bar object:
instrument, timeframe, open_time, close_time, OHLC, volume when available, provider, finality, source timestamp, quality flags.

Rules:
- no future/incomplete bar treated as final
- duplicate bars deterministic
- revisions explicit
- missing bars visible.

### Ch III.1.3 Timezone/DST engine
Use named timezone semantics for live/session calculations.
Research artifacts that used fixed EST/no-DST retain their original clock identity rather than being silently converted.

Tests cover spring/fall DST boundaries and fixed-offset historical datasets.

### Ch III.1.4 Research-day ownership
Implement explicit session-day assignment.
Known EUR/BTC research lineage includes evening bars assigned to following research day where specified.

No calendar-date assumption.

### Ch III.1.5 Session definitions
Versioned session objects for:
- Asian range
- London/MLR
- daily checkpoints
- weekly seed windows
- model-specific DT windows
- higher-order month/quarter boundaries.

Session definitions belong to model/calibration versions.

### Ch III.1.6 Final-bar semantics
Encode exact inclusive/exclusive boundaries and final bar, e.g. M5 02:55 final bar for a 19:00-03:00 construction where canonical source specifies it.

### Ch III.1.7 Data quality
Flags:
COMPLETE, GAP, DUPLICATE, REVISED, STALE, NONFINAL, OUTLIER_SOURCE, UNSUPPORTED_CLOCK.

Models declare which flags block calculation vs warn.

### Ch III.1.8 Provider normalization
Provider adapters map raw feeds into the normalized contract.
Provider-specific timestamps/symbols never enter model logic directly.

### Ch III.1.9 Historical/live parity fixtures
Take known source slices and prove identical normalized session ownership/measurements in replay and live-style streaming.

Acceptance III.1:
- DST/session adversarial suite passes
- research-day ownership deterministic
- nonfinal bars cannot contaminate final-state calculations
- provider aliases normalize to canonical instrument IDs
- missing/ambiguous data produces explicit quality state, not invented bars.

---

# BLOC III.2 — MEASUREMENT & FEATURE ENGINE

## Objective
Implement reusable measured quantities without turning measurements into predictions.

### Ch III.2.1 Range engine
Calculate versioned:
- high/low
- size
- midpoint
- direction/close location
- consumed fraction
- range-left
- breakout/return state.

### Ch III.2.2 Tier/AU calibration
Asset/model-native calibration tables.
Support fixed frozen calibrations and versioned research calibrations.

Known launch examples:
- EUR Daily T1 <20p, T2 20-30p, T3 30-45p, >45 no-go for its source generation
- BTC native $ tiers/AU/triggers
- JPY pair-native daily/weekly tiers.

Never expose a global universal tier constant.

### Ch III.2.3 Coordinate engine
Coordinates are projections from an earned active range/anchor:
50/61.8/68/72/80/82/100/120/125/132/168/185 and extension families only where a model declares them.

No arbitrary fib projection without valid anchor.

### Ch III.2.4 Range Birth/anchor interface
Define anchor eligibility as a first-class output:
UNRESOLVED, ELIGIBLE, ACTIVE, INVALIDATED, REKEYED.

Fib R15/Range Birth implementation must attach its exact canonical rule before automation approval.
R11 generic-pivot fallback is forbidden for production setup generation.

### Ch III.2.5 Clock/state-age engine
Measure:
- elapsed since event/state
- checkpoint reached
- acceptance duration
- failure age
- time-to-delivery
- session/weekly/monthly phase.

Time weights state; it does not manufacture state.

### Ch III.2.6 Path measurements
MAE, MFE, first delivery, target order, excursion, rejection, acceptance, close-beyond, re-entry and remaining distribution.

Touch != acceptance.
Reach != target-before-stop.
Terminal outcome != path.

### Ch III.2.7 Event/news features
Normalized event object with:
currency/asset relevance, event family, scheduled/actual time, historical band/size fields where available, consumed/residual budget.

News modifies conditional state; it does not replace geometry.

### Ch III.2.8 Higher-order measurements
Month/quarter seed ranges, D1-D3 states, M1 scale, M2 shaping, unfinished side, weekly seed/path, and model-specific checkpoints.

### Ch III.2.9 Measurement provenance
Every computed measurement carries:
definition/version, source data window, clock/session ID, instrument, calculation timestamp, quality state.

### Ch III.2.10 Golden measurement fixtures
Build frozen examples for EUR, XAU, BTC, JPY and Fib geometry.

Acceptance III.2:
- measurements reproduce frozen fixtures
- no measurement API labels a value as prediction/trade signal
- coordinate generation requires eligible anchor/range
- touch/acceptance/path distinctions survive serialization
- measurement provenance is complete.

---

# BLOC III.3 — MODEL RUNTIME

## Objective
Run each launch CEREBUS family as an explicit versioned state machine/service over measurements.

## Common model contract
Input:
- canonical model/version
- normalized measurements
- prior model state if stateful
- calculation timestamp.

Output:
- model_state
- layer
- direction/bias if model defines one
- active ranges/anchors
- levels
- range-left/distribution fields
- no-go/warnings
- evidence/claim references
- data quality
- model version/hash
- explanation facts, not generated prose.

### Ch III.3.1 EUR Daily News + Rekey runtime
Implement:
Asian seed -> tier -> distance/asymmetry -> consumed states -> event/news conditioning -> rekey/extension -> remaining distribution.

Protect:
- >45p source no-go
- 100/125/132/168/185 state identity
- news as modifier
- slot x tier/range-left semantics.

### Ch III.3.2 EUR Weekly Engine V1.1
Implement:
Monday seed/range -> weekly tier -> route/range-left -> hour x tier timing -> outer-node state.

Protect:
- static/frozen after defined completion where canonical implementation requires
- outer-node promotion only
- weekly path not promoted into higher-order destination evidence.

### Ch III.3.3 EUR Higher Order runtime
Quarter seed -> D3 prior -> M1 scale -> M2 shaping -> M3 resolution -> weekly/local handoff.

Protect:
- L3 destination semantics
- D3 agreement statistics not trade WR
- M1 correlation not probability
- unfinished-side completion as conditional destination evidence.

### Ch III.3.4 XAU Game runtime
L3 higher-order destination/scale.
L2 route/state, Tuesday pace/location/range-left/delivery clocks.
L1 Asian tier/relative consumption/execution state.

Protect frozen rules:
- 68+8h ->80 eligible promotion
- 120+8h ->132 research/small-N promotion
- 132->168 NOT automatic
- L2 state != direct entry
- parked setups remain parked.

### Ch III.3.5 BTC Tracker runtime
Daily/Weekly/Monthly Tracker only.

Daily:
19:00-03:00 NY source frame, native tiers/AU/triggers, 03:00-19:00 slot x tier range-left.

Weekly/monthly:
versioned anchor/rekey/tracker fields only where canonical definitions exist.

Protect:
BTC Tracker != BTC Game.
No Gold Game setup import.
>3000 Asian range no-go for recovered native calibration.

### Ch III.3.6 Fib / Range Birth runtime
State:
range-birth eligibility -> A/B active range -> Alpha/Beta/Gamma/Delta sequence -> coordinate/path -> rekey/new range.

Until R15 exact eligibility is canonicalized sufficiently:
- explanation/research state allowed
- production setup generation remains gated
- no generic pivot fallback.

### Ch III.3.7 JPY Carry Game runtime
Basket role state:
USDJPY carry master
AUDJPY risk/execution expression
EURJPY confirmation/veto.

Pair-native daily/weekly tiers.
Return role agreement and local state separately.

Protect:
- no equal-vote majority
- confirmation != entry
- historical 12-4 DT geometry not auto-merged
- manual operator classification until parity approved.

### Ch III.3.8 Model registry/dispatch
Resolve model_id + version explicitly.
No "latest" without version policy.
Historical requests can pin historical generation.

### Ch III.3.9 Deterministic replay
Given identical normalized inputs and model version, output hash must match.

Acceptance III.3:
- all launch runtimes conform to common contract
- model-specific golden fixtures pass
- cross-asset calibration leakage tests fail
- parked/noncanonical behavior cannot activate
- deterministic replay hashes match.

---

# BLOC III.4 — STATE, PATH & TRANSITION ENGINE

## Objective
Represent how CEREBUS moves through states, not merely where price ended.

### Ch III.4.1 State snapshot
Immutable/versioned snapshot:
model, layer, timestamp, active state, measurements, active levels, quality, claim/evidence refs.

### Ch III.4.2 Transition vocabulary
At minimum:
ENTER_STATE
ACCEPT
REJECT
FAIL
REPAIR
PROMOTE
DELIVER
REKEY
INVALIDATE
COMPRESS
RELEASE
STAND_DOWN.

Models may restrict vocabulary.

### Ch III.4.3 First-delivery engine
Track ordered target/state delivery.
Both-side hit without order is insufficient when model depends on first delivery.

### Ch III.4.4 Failure/repair grammar
Support canonical failure paths such as historical P90/structural:
valid acceptance -> failure -> midpoint repair -> compression/reacceptance/opposite acceptance
only for models/generations that declare it.

### Ch III.4.5 Rekey
Rekey is a structural remapping/state transition, not merely "price touched132".

Store:
prior range/state -> rekey event -> new active mapping/eligibility.

### Ch III.4.6 Layer handoff
Formal handoff:
L3 destination context
-> L2 path/opportunity
-> L1 execution eligibility.

No upward probability laundering.

### Ch III.4.7 Range-left
Represent remaining distribution conditioned on what has already occurred.
Do not keep quoting unconditional target reach after states are consumed.

### Ch III.4.8 No-go/stand-down
No-go is a stateful output with reason:
range too large, data bad, anchor unresolved, conflicting model rule, exhausted/parked state, insufficient evidence where required.

### Ch III.4.9 Transition history
Persist transition sequence enough for:
- operator explanation
- replay
- research analysis
- Ask CEREBUS historical state question.

### Ch III.4.10 Path invariants
Tests:
- terminal outcome cannot erase path
- target order stable
- rekey closes/replaces mapping according to model
- no-go prevents setup eligibility
- L1 cannot mutate L3 state.

Acceptance III.4:
- path replay reconstructs current state
- first-delivery order is preserved
- rekey is explicit transition
- layer boundaries enforced
- no-go reasons machine-readable.

---

# BLOC III.5 — OPERATOR SETUP ENGINE

## Objective
Convert model context into bounded setup eligibility without pretending every model state is a trade.

## Common setup contract
Output:
- setup_id/version
- execution_class
- eligibility: ELIGIBLE / WATCH / BLOCKED / UNRESOLVED
- side if defined
- location/zone
- trigger requirements
- invalidation
- ordered targets
- no-go reasons
- parent model states
- evidence refs
- manual/automation status
- explanation facts.

### Ch III.5.1 Setup registry
Load only canonical/promoted Setup Cards.
Unknown/research-only setup cannot appear as production signal.

### Ch III.5.2 Eligibility engine
All required:
state + range/anchor + tier + clock + higher-layer constraints + data quality.

### Ch III.5.3 Trigger semantics
Explicit types:
TOUCH
EXCURSION
REJECTION
ACCEPTANCE
CLOSE
SR_FLIP
OCC
and combinations.

A setup specifies which is required.

### Ch III.5.4 Invalidation
Price, structural and temporal invalidation are separate fields.

### Ch III.5.5 Target/promotions
Ordered targets with conditions.
Path promotion cannot be assumed because a deeper coordinate exists.

### Ch III.5.6 XAU Quarter-Zone operator
Implement current canonical operator card as MANUAL_OPERATOR:
after03:00, active direction/state, excursion into quarter +/- zone, rejection/close/flip confirmation, next-quarter doctrine, exact active invalidation from implementation.

No blind touch.

### Ch III.5.7 Fib Rekey operator
RESEARCH_ONLY until Range Birth eligibility evidence/implementation is approved.
132/168/185 lineage may be explained but not emitted as automation-approved signal.

### Ch III.5.8 JPY Role-Gated operator
MANUAL_OPERATOR:
USDJPY master + AUDJPY expression + EURJPY confirmation/veto -> selected pair local setup.

No equal vote.

### Ch III.5.9 Historical/manual ST representation
ST/Tier->AU->Tier may be explained as valid manual operator framework.
Do not approve autonomous ST execution.
Automation/perception gap remains unresolved.

### Ch III.5.10 P90 automation lineage
Represent P90 as automation-capable lineage only to the extent implementation/version is verified.
Historical performance claims remain evidence-gated.

### Ch III.5.11 Setup result vs setup statistics
Runtime eligibility never fabricates WR.
Statistics come only through Claim/Evidence IDs.

### Ch III.5.12 Setup adversarial tests
- level touched but no trigger
- correct trigger but no-go
- L3 direction without L1 eligibility
- stale/nonfinal data
- unresolved Range Birth
- wrong asset tier
- parked setup
- research-only setup requested as production.

Acceptance III.5:
- model state alone cannot manufacture entry
- every emitted production/operator setup maps to canonical Setup Card
- trigger/invalidation/target semantics explicit
- manual/research/automation class preserved
- unsupported WR never emitted.

---

# BLOC III.6 — MARKET INTELLIGENCE API & SNAPSHOT SERVICE

## Objective
Expose deterministic intelligence to Ask CEREBUS, dashboards and internal research without leaking implementation internals.

### Ch III.6.1 Snapshot identity
Snapshot key includes:
instrument, model_id/version, layer, as_of, data cutoff, calculation version.

### Ch III.6.2 Current state endpoint/service
Returns authorized:
state, layer, direction/bias where defined, active range/tier, clocks, quality, no-go.

### Ch III.6.3 Levels endpoint
Return typed levels:
measurement, decision, target, invalidation, rekey, promotion, zone.
Each includes source model/version and active/inactive state.

### Ch III.6.4 Path endpoint
Current path, consumed states, first-delivery history, range-left, transition sequence summary.

### Ch III.6.5 Setup-context endpoint
Returns eligibility facts and canonical setup payload.
Policy from Book II applies before response.

### Ch III.6.6 Evidence link endpoint
Returns Claim/Evidence IDs/status for model outputs.
Does not duplicate entire corpus.

### Ch III.6.7 Historical snapshot/replay
Request prior as-of state using pinned data/model version where retained.
If exact reconstruction unavailable, say unavailable rather than use current rules silently.

### Ch III.6.8 Multi-model instrument view
Compose L3/L2/L1 without creating monolithic confluence score.

Example EUR:
Higher Order destination
Weekly path
Daily execution context.

### Ch III.6.9 Basket view
JPY role-aware multi-instrument payload.
Do not flatten to average score.

### Ch III.6.10 Response schemas
Stable machine-readable contracts with schema_version and model_version.

### Ch III.6.11 Caching
Cache by snapshot identity.
Invalidate on:
new final bar/event, model version change, calibration change, corrected data, entitlement/exposure change where response filtering differs.

### Ch III.6.12 API security/observability
Use Book II identity/policy/audit.
Do not expose internal feature engineering or source code.

Acceptance III.6:
- same snapshot identity returns deterministic payload
- current/historical distinction explicit
- L3/L2/L1 composition preserves layer ownership
- evidence/status accompanies statistical/model claims
- policy filters protected outputs
- no monolithic confidence score appears unless a future canonical model explicitly defines one.

---

# BOOK III CROSS-MODEL INVARIANTS

1. Data clock is part of model identity.
2. Asset calibration is local unless transfer is explicitly validated.
3. Range/anchor must exist before coordinates.
4. Tier is a compression of continuous behavior, not a causal force.
5. Time weights/ages state; time alone does not call the play.
6. Touch != acceptance.
7. Reach != trade win.
8. First delivery/path can matter more than terminal both-side reach.
9. Rekey is a remapping transition.
10. Range-left updates conditional opportunity after states are consumed.
11. L3 destination != L2 path != L1 entry.
12. Model state != setup.
13. Setup != automation approval.
14. Manual valid strategy can coexist with failed automation parity.
15. Negative evidence remains queryable.
16. Historical high-performance claims are never silently treated as current verified performance.
17. News is a measurable perturbation/conditioner, not a geometry replacement.
18. No deterministic rhetoric in runtime status labels.

---

# BOOK III GOLDEN FIXTURE PROGRAM

Create a compact but representative frozen fixture set.

## EUR
- T1/T2/T3/no-go daily seed
- rekey/extension state
- event-conditioned state
- Weekly outer-node path
- Higher-Order D3/M1/M2/M3 handoff.

## XAU
- normal state
- 68+8h promotion
- 120+8h small-N promotion
- 132 state proving no automatic168
- quarter-zone eligible vs blind-touch blocked.

## BTC
- all three native Asian tiers
- >3000 no-go
- slot x tier range-left
- proof Tracker output contains no invented Game setup.

## Fib
- valid born range
- unresolved anchor
- rekey transition
- arbitrary local pivot rejected.

## JPY
- USDJPY/AUDJPY agree + EURJPY confirm
- confirm absent
- no-go native tier
- proof no equal-vote aggregation.

## Historical/manual
- ST manual explanation available but automation flag false
- P90 version identity and evidence separation.

---

# BOOK III FAILURE BEHAVIOR

If data is incomplete:
DATA_QUALITY_BLOCKED or degraded state per model contract.

If clock/session cannot be resolved:
NO_CALCULATION.

If anchor unresolved:
coordinates/setup blocked where anchor required.

If model version missing:
MODEL_VERSION_UNAVAILABLE.

If evidence missing:
model state may still exist if rule is canonical, but no unsupported statistic is attached.

If higher/lower layers conflict:
return conflict/state facts; do not invent confluence score.

If provider/feed fails:
serve explicitly stale cached snapshot only if product policy allows and label STALE with data cutoff; otherwise unavailable.

---

# BOOK III ACCEPTANCE / RATIFICATION GATE

Book III is DONE only when:

## Data/clock
- session/DST/research-day tests pass
- nonfinal/missing bars handled explicitly
- provider-normalization parity passes.

## Measurements
- golden ranges/tiers/AU/coordinates/clocks/path metrics reproduce
- provenance accompanies measurements
- no arbitrary anchor coordinate generation.

## Models
- seven launch family runtimes conform to versioned contract
- deterministic replay passes
- cross-asset calibration leakage fails
- BTC Tracker/Game separation passes
- XAU frozen/parked rules pass
- JPY role hierarchy passes.

## State/path
- first-delivery order retained
- rekey transition explicit
- range-left updates correctly
- layer handoff does not probability-launder.

## Setups
- model state cannot create unsupported entry
- manual/research/automation flags enforced
- XAU blind-touch test blocked
- Fib unresolved Range Birth blocked
- JPY equal-vote path impossible
- unsupported setup WR absent.

## API
- deterministic snapshot schemas
- historical/current distinction
- evidence links
- Book II policy/audit integration
- protected/internal implementation fields absent.

## Evidence pack
Each Bloc:
PLAN.md
ACCEPTANCE.md
implementation commits
tests/results
EVIDENCE.md
known gaps
ratification.

Final Book III record:
- market-data schema version
- session/clock registry version
- measurement engine version
- model runtime versions/hashes
- setup registry version
- golden fixture hashes
- test counts
- unresolved research gates
- ratification commit.

---

# BOOK III EXCLUSIONS

Do NOT build:
- brokerage/order execution
- automated position sizing
- personalized trade advice
- portfolio allocation
- monolithic AI confidence score
- unvalidated BTC Game
- autonomous ST engine
- arbitrary Fib anchor generator
- UI/dashboard presentation beyond API contracts
- Ask CEREBUS prose generation
- Whop logic.

---

# RECOMMENDED IMPLEMENTATION ORDER

1. III.1 Market Data & Clocks
2. III.2 Measurement Engine
3. common runtime/state contracts
4. III.3 models in order:
   a EUR Daily
   b EUR Weekly
   c EUR Higher Order
   d XAU
   e BTC Tracker
   f JPY Carry
   g Fib/Range Birth gated runtime
5. III.4 State/Path
6. III.5 Setup Engine
7. III.6 Intelligence API
8. full replay/adversarial matrix
9. evidence pack
10. Book III ratification/freeze.

EUR first gives a complete L3->L2->L1 vertical stack. XAU then tests Game architecture, BTC tests crypto/native calibration, JPY tests basket roles and Fib tests earned-anchor gating.

# HANDOFF TO BOOK IV

Book IV may assume Book III returns facts, not prose:
- exact model/version
- current state
- active ranges/levels
- path/range-left
- setup eligibility
- no-go
- data quality
- claim/evidence IDs
- transition history.

Ask CEREBUS is responsible for interpreting and explaining those facts under the answer contract; it must not recompute market state inside the LLM.

# HANDOFF TO BOOK V

Book V may render Book III state/levels/setups but cannot create new model logic in the frontend.
A chart/dashboard is a view of intelligence, not a second intelligence engine.
