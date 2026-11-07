# BOOK III / BLOC III.2 — MEASUREMENT & FEATURE ENGINE — PLAN.md

Status: **PLANNING ONLY — committed before any implementation** (frozen
Book II/III.1 order rule reused: PLAN + ACCEPTANCE are committed first;
no implementation authorized by this packet).
Date: 2026-10-13
Branch: `forge` · Planning head: `2aafef984d71777bf8ee7f25c37f7a3e26773e4a`
Frozen source: `planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(pinned in `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` line 35) —
sections `# BLOC III.2` (Ch III.2.1–III.2.10 + Acceptance III.2),
`# BOOK III CROSS-MODEL INVARIANTS`, `# BOOK III GOLDEN FIXTURE PROGRAM`,
`# BOOK III FAILURE BEHAVIOR`, `# BOOK III ACCEPTANCE / RATIFICATION GATE`
§Measurements + final-record fields, `# BOOK III EXCLUSIONS`, and
`# RECOMMENDED IMPLEMENTATION ORDER` step 2.

Scope here is exactly the frozen Bloc III.2 chapters — no Book III scope
is inferred from the Book title, and no measurement becomes a prediction
by being useful. Cross-checked against
`planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` (§5 graph:
`I.3-I.5 -> III.1-III.3 -> III.4-III.6`; Phase C order) and
`planning/forge/AGENT_EXECUTION_HANDOFF_V1.md` (`III.1 -> III.2 -> …`;
"later phase may start early only when its required contracts are
already frozen and the work does not create a circular dependency" —
both hold; III.1 is ratified).

---

## 1. Governing authority model (mandatory, restated — Phase 3)

These distinctions govern every design decision in this Bloc and are
re-verified in ACCEPTANCE.md:

- **Model ≠ Claim ≠ Evidence ≠ Setup ≠ Artifact.** III.2 produces
  *measurements*: deterministic transformations of observations with an
  explicit formula, units, input frame and clock/session definition
  (`CEREBUS_CANONICAL_TAXONOMY_V1.md` class 2 MEASUREMENT). A
  measurement is neither a model output, nor a claim, nor evidence.
  Numerical calibrations cite Book I evidence IDs read-only; III.2 never
  grants itself evidence authority.
- **A measurement is not a prediction.** No III.2 value may be labeled,
  typed or serialized as a prediction, signal, call, expectancy or
  win-rate. Time quantities measure elapsed/scheduled facts only.
- **Historical observation ≠ current market state.** Golden fixtures and
  research calibrations are historical and labeled; nothing here serves
  current state (III.6 owns serving).
- **Simulation ≠ empirical performance.** Golden-fixture reproduction is
  a deterministic contract test over (mostly synthetic) committed bars —
  never empirical or performance evidence.
- **Provider output ≠ canonical truth.** Inputs arrive via III.1's
  normalized contract only; raw feed state is never copied forward.
- **Semantic similarity ≠ evidence authority.** No retrieval/vector code
  exists in this Bloc (Book I owns it; frozen).
- **No trading/execution concepts.** No entry, order, position, sizing,
  stop, game or setup objects exist at this layer; touch/acceptance/
  rejection are measurement vocabulary with strict typed semantics.
- **BTC Tracker ≠ BTC Game.** III.2 measures Tracker-side geometry; no
  Game rule may be inferred from measurement output.

## 2. Scope (frozen chapters, in)

| Ch | Frozen requirement (compressed; frozen plan is authority) |
|---|---|
| III.2.1 | Range engine: versioned high/low, size, midpoint, direction/close location, consumed fraction, range-left, breakout/return state. |
| III.2.2 | Asset/model-native tier/AU calibration tables; fixed frozen calibrations and versioned research calibrations. Known launch examples: EUR Daily Phase1 T1 <20p / T2 20–30p / T3 30–45p / >45p no-go for its source generation; BTC native $ tiers / AU / triggers; JPY pair-native daily/weekly tiers. Never expose a global universal tier constant. |
| III.2.3 | Coordinate engine: coordinates are projections from an earned active range/anchor; families 50/61.8/68/72/80/82/100/120/125/132/168/185 and extension families only where a model declares them. No arbitrary fib projection without valid anchor. |
| III.2.4 | Range Birth/anchor interface: anchor eligibility is a first-class output with states UNRESOLVED, ELIGIBLE, ACTIVE, INVALIDATED, REKEYED. Fib R15/Range Birth must attach its exact canonical rule before automation approval; R11 generic-pivot fallback is forbidden for production setup generation. |
| III.2.5 | Clock/state-age engine: elapsed since event/state, checkpoint reached, acceptance duration, failure age, time-to-delivery, session/weekly/monthly phase. Time weights state; it does not manufacture state. |
| III.2.6 | Path measurements: MAE, MFE, first delivery, target order, excursion, rejection, acceptance, close-beyond, re-entry, remaining distribution. Touch ≠ acceptance. Reach ≠ target-before-stop. Terminal outcome ≠ path. |
| III.2.7 | Event/news features: normalized event object with currency/asset relevance, event family, scheduled/actual time, historical band/size fields where available, consumed/residual budget. News modifies conditional state; it does not replace geometry. |
| III.2.8 | Higher-order measurements: month/quarter seed ranges, D1–D3 states, M1 scale, M2 shaping, unfinished side, weekly seed/path, model-specific checkpoints. |
| III.2.9 | Measurement provenance: every computed measurement carries definition/version, source data window, clock/session ID, instrument, calculation timestamp, quality state. |
| III.2.10 | Golden measurement fixtures: frozen examples for EUR, XAU, BTC, JPY and Fib geometry per the frozen `# BOOK III GOLDEN FIXTURE PROGRAM`. |

Plus the applicable cross-model invariants (#2 asset calibration local;
#3 range/anchor before coordinates; #4 tier is compression not causal
force; #5 time weights state; #6 touch ≠ acceptance; #7 reach ≠ trade
win; #8 first delivery/path can dominate terminal; #9 rekey is a
remapping transition; #10 range-left updates conditional opportunity;
#17 news conditions, never replaces geometry; #18 no deterministic
rhetoric in runtime status labels), the failure-behavior clauses that
land on this layer, gate §Measurements, and the final-record fields III.2
owns (**measurement engine version**, plus III.2's **golden fixture
manifest hashes** feeding the book-level golden fixture hashes).

## 3. Scope exclusions (out — never in this Bloc)

- No model runtimes, state machines, snapshots (III.3/III.4). Higher-order
  *measurements* (III.2.8) are containers/facts; model semantics and
  state transitions belong downstream.
- No setups, eligibility gates or triggers as trading objects (III.5).
  Anchor eligibility (III.2.4) is a measurement-layer interface, not an
  entry gate.
- No API/endpoints/caching/serving (III.6).
- No live provider network calls, credentials or SDKs (III.1 boundary
  carries). Inputs come from III.1 normalized bars over committed
  fixtures only.
- No new persistence migration; the container readiness seam
  `market_data: NOT_CONFIGURED` (`app/forge/service/container.py`) is not
  modified (Book II D4 boundary; III.1 carried it unchanged).
- No Book I corpus writes, no exposure/policy changes, no HTTP surface,
  no trading/advice/execution/automation concepts (Book III exclusions
  restated).
- No modification of any frozen Book I/II file (50-file Book II freeze
  manifest + 23 planning pins + Book I freeze manifest) **and no
  modification of any III.1 ratified file** (`app/forge/market_data/`,
  11 modules — hashes recorded in §6 of this plan as the III.1 interface
  integrity baseline).
- No statistical model fitting, no probability/confluence outputs, no
  performance metrics (win rate, expectancy, RR) anywhere in the package.

## 4. Phase 0 foundation (verified at this head; summary)

`HEAD == origin/forge == 2aafef9…73e4a`, tracked tree clean; planning
freeze `60e0675` ancestor; Book I I.5 **RATIFIED (CLOSED)**
(`686faa7`); Book II **RATIFIED — CONTRACTS FROZEN** (G-F7
`e45d23371b14cca6b6dc1085dc56d8b9f2fe03aa`, 50-file manifest);
Bloc III.1 **RATIFIED — PASS (CLOSED)** at `2aafef9` (BA-17: focused
suite 65/65, full suite 1081 passed / 29 pre-existing skips, final-head
CI runs `38446736874` + `38447754247` success, 50/50 Book II hashes and
23/23 planning pins verified in-suite, migrations `[1, 2, 3, 4]`,
readiness seam byte-identical). III.1's five carried gaps (GAP-1…GAP-5:
synthetic fixtures only; sessions only where canonically defined; M5
final-bar rule scoped to its source lineage; provider wiring
`NOT_CONFIGURED`; scripted-streaming parity only) are inherited here as
upstream dependency disclosures, not re-litigated. Phase-order
governance disposition resolved (Book III phase C in progress; no
circular dependency). Downstream gap register: none is a Book III.2
prerequisite.

## 5. Dependency and ownership matrix

| # | Upstream contract | Owner | Frozen status | How III.2 uses it | Ready? |
|---|---|---|---|---|---|
| D1 | III.1 `app/forge/market_data/` (instruments, bars, clocks, research_day, sessions, quality, normalize, parity, versions, errors) | Book III.1 (BA-17) | Ratified PASS — CLOSED at `2aafef9`; 11-module hashes in §6 | Consumed **read-only**: normalized final bars, native-unit prices, clock/session identities, research-day ownership, frozen quality vocabulary and outcomes. Core law: downstream may consume, never silently redefine — III.2 adds no monkeypatching, no wrapper reinterpretation, no new bar semantics | ✅ |
| D2 | Canonical corpus (taxonomy/crosswalk, model cards, evidence cards) | Book I | Frozen (23 pins) | Read-only citations by ID; calibration constants and session/checkpoint definitions come from canonical sources only; taxonomy class-2 MEASUREMENT requirements (formula/units/frame/clock) drive the provenance envelope; **no corpus writes** | ✅ |
| D3 | Book II platform patterns (frozen dataclasses, bounded typed errors, versioned records, redaction discipline) | Book II | Frozen (50-file manifest) | Structural precedent only — same record/refusal style; no Book II surface exercised (no HTTP/persistence/policy touch) | ✅ (N/A directly) |
| D4 | Python stdlib (`Decimal`, dataclasses, `enum`; `zoneinfo` reached via III.1 clocks) | stdlib/platform | Available | Pure deterministic computation; **no new pip dependency** | ✅ |
| D5 | III.1 fixture/manifest discipline (`FIXTURE_MANIFEST.json`, generator script, `SYNTHETIC_FIXTURE` labels, LF-normalized content hashes) | Book III.1 | Ratified | Pattern reused verbatim for III.2 golden fixtures (including the EOL-independence lesson from BA-17 repairs `5127fa7`→`8b43cb4`) | ✅ |

**Missing prerequisites: none.** Verdict: dependency-ready.

## 6. Existing implementation reuse (actual repository state)

- `app/forge/` has **zero** measurement/coordinate/range/tier code
  (verified: only unrelated alias hit in frozen
  `app/forge/retrieval/aliases.py`). III.2 is greenfield; no parallel
  abstraction risk.
- III.1 delivers every consumed primitive: `Bar` (frozen, Decimal OHLC,
  finality, quality flags, `market_data_schema_version`), `NativePrice` /
  `add_native` / `convert_native`, `ClockIdentity` (+ `CLOCK_REGISTRY_V1`),
  `SessionDefinition` / `SessionRegistry` / `SessionResolution` (+
  `SESSION_REGISTRY_V1`), `assign_research_day`, `QualityFlag` /
  `QualityPolicy` / `DataOutcome`, `MARKET_DATA_SCHEMA_V1`, and the
  bounded `MarketDataError` refusal pattern.
- **III.1 interface integrity baseline** (planning-time `sha256sum` of
  the checked-out ratified modules; same reading as the Book II
  manifest — raw hashes bind the committed blobs as checked out on this
  Windows `core.autocrlf=true` checkout, EOL-normalized comparison for
  cross-platform verification):

  `__init__.py 94c88cd7…15f0f` · `bars.py 97fc99e4…66366` ·
  `clocks.py 2698d527…f172` · `errors.py 52f10816…6c88c` ·
  `instruments.py 8c6d6ad0…d94d` · `normalize.py 9b7ea855…19c24` ·
  `parity.py 0bb765af…ce8c` · `quality.py 6b77c6df…58687` ·
  `research_day.py b5c82e40…5307` · `sessions.py 037dbaaa…77e5` ·
  `versions.py 9e502d7f…842e` (full 64-hex values re-derivable with
  `sha256sum app/forge/market_data/*.py`; recorded here so the III.2
  implementation rung can assert III.1 files unchanged — same mechanism
  as the Book II freeze manifest, no new governance gate).

- Reusable *patterns*: frozen dataclasses + bounded refusal codes
  (III.1 `errors.py`), versioned registry objects (`sessions.py`),
  fixture manifest + generator + provenance README (III.1 `fixtures/`),
  and the honesty-disclosure vocabulary (`NOT_CONFIGURED`, `GAP-n`).
- Legacy Signal Guard code (`app/state_engine.py`, etc.) remains
  naive-timezone, not reusable, deliberately untouched.
- **Implementation-compatible clarification (recorded per
  planning-manifest change control, no semantic change):** the canonical
  BTC calibration nomenclature preserves the term `trigger_levels`
  (canonical card: "Triggers 246/654/1392"). These are threshold
  constants from `BTC.TRACKER.DWM.V1`, not execution triggers; the
  trading-concept boundary test names this canonical field explicitly so
  canonical vocabulary is preserved rather than renamed.

## 7. Proposed design (planning intent — implementation needs its own authorization)

Proposed package (new; touches no frozen file): `app/forge/measurements/`

| Module | Ch | Contents |
|---|---|---|
| `contracts.py` | III.2.9 | `Measurement` envelope (frozen dataclass): `definition_id`, `definition_version`, `instrument_id`, source window (UTC open/close + input-bar content digest), clock/session IDs + registry versions, injected `calculation_timestamp`, quality state (frozen III.1 vocabulary), native unit where applicable, `measurement_engine_version`; `DefinitionSpec` table mapping definition_id → formula text + unit + input frame |
| `ranges.py` | III.2.1 | `RangeMeasurement` over final III.1 bars: high/low (`NativePrice`), size, midpoint, direction, close location, consumed fraction, range-left, `BreakoutReturnState` |
| `calibration.py` | III.2.2 | `TierTable`, `AuScale`, `TriggerLevels`, `DensityZone` frozen records keyed `(model_id, model_version, calibration_id, calibration_version)` with calibration status (`FROZEN_LAUNCH` / `RESEARCH`); `classify_tier()`; canonical launch/research tables as data (EUR Daily Phase1; BTC native; EUR Weekly research; JPY partial; XAU spatial bands); cross-asset or global lookup **refuses** |
| `coordinates.py` | III.2.3 | `CoordinateFamily` (declared per model/calibration version; canonical families + declared extensions); `project_coordinates(anchor, family)` — refuses any anchor not ELIGIBLE/ACTIVE |
| `anchors.py` | III.2.4 | `AnchorStatus` (UNRESOLVED/ELIGIBLE/ACTIVE/INVALIDATED/REKEYED); `AnchorEligibility` first-class output (status, earned-range reference, rule id/version, refusal code); **no generic-pivot/anchor generator exists in the package** (R11 fallback impossible by construction) |
| `state_age.py` | III.2.5 | `elapsed_since`, `checkpoint_reached`, `acceptance_duration`, `failure_age`, `time_to_delivery` (elapsed vs a *scheduled* canonical checkpoint/session boundary — never a price forecast), session/weekly/monthly phase from III.1 session registry |
| `path_metrics.py` | III.2.6 | `PathMeasurement`: MAE, MFE, first delivery (bar + order), target order, excursion, rejection, acceptance, close-beyond, re-entry, remaining distribution; typed `TouchState` vs `AcceptanceState` (distinct enums — touch never coerces to acceptance) |
| `events.py` | III.2.7 | `NormalizedEvent`: relevance currencies/assets, event family, scheduled/actual times, band/size fields optional-but-explicit, consumed/residual budget arithmetic (subtractive budget per EUR Daily canonical doctrine) |
| `higher_order.py` | III.2.8 | month/quarter seed ranges, `D1D3State`, M1 scale, M2 shaping, unfinished side, weekly seed/path, model-specific checkpoints; layer-conflict facts structurally incapable of emitting a confluence score |
| `versions.py` | final record | `MEASUREMENT_ENGINE_VERSION = "MEASUREMENT_ENGINE_V1"` |

Cross-cutting rules for the future implementation: pure functions +
frozen dataclasses; `Decimal` arithmetic in asset-native units (never
float for prices, never cross-unit without III.1 `convert_native`);
injected calculation clock (no wall time); no network; no imports from
`qa/`, `retrieval/`, `app/forge/provenance.py`, `canonical.py`,
`policy.py`, or any frozen file; deterministic serialization where every
emitted measurement carries `measurement_engine_version` and — via its
inputs — `market_data_schema_version`, clock-registry and
session-registry versions (Book III final-record fields).

## 8. Proposed executable test matrix (summary; full clause→test map in ACCEPTANCE.md)

Proposed file: `tests/test_forge_measurements.py` (plus golden fixtures
under `implementation/forge/book_iii/bloc_iii_2/fixtures/`). All
deterministic, offline, network-free.

| Group | Frozen driver | Representative proposed tests |
|---|---|---|
| T1 Range | III.2.1 | frozen fields; size/midpoint in native units; close location + direction; consumed fraction bounded; range-left never invents remaining movement and updates after consumption; breakout/return state explicit; quality-blocked input refuses |
| T2 Calibration | III.2.2 | tables keyed by model+version; EUR Phase1 boundary reproduction (20/30/45p edges incl. no-go); BTC native $ boundary reproduction; AU = native atomic distance; **no global tier constant**; cross-asset transfer refuses; research status labeled; tier is compression, not force; unknown tier → explicit unclassified; missing calibration version → `MODEL_VERSION_UNAVAILABLE` |
| T3 Coordinates | III.2.3 | families bounded to canonical + declared extensions; projection requires ELIGIBLE/ACTIVE anchor; arbitrary pivot rejected; no coordinate without earned range; 132/168/185 ladder does not auto-extend |
| T4 Anchors | III.2.4 | five-state vocabulary exact; eligibility is first-class output; REKEYED is a remapping transition; INVALIDATED blocks projection; no generic-pivot fallback exists |
| T5 State-age | III.2.5 | elapsed since event; checkpoint reached; acceptance duration; failure age; time-to-delivery is scheduled elapsed (never price-forecast); session/weekly/monthly phase; unresolvable clock/session → `NO_CALCULATION` |
| T6 Path | III.2.6 | MAE/MFE; first-delivery order; target order; **touch ≠ acceptance**; reach ≠ target-before-stop; excursion/rejection/acceptance typed; close-beyond; re-entry; remaining distribution never synthesized; distinctions survive serialization round-trip; reach carries no win/expectancy fields |
| T7 Events | III.2.7 | relevance + family; scheduled vs actual times; band/size fields explicit-when-absent; consumed/residual budget subtractive; news never replaces geometry |
| T8 Higher-order | III.2.8 | seed ranges; D1–D3 states; M1 scale/M2 shaping; unfinished side; weekly seed/path; layer conflict returns facts, never a confluence score |
| T9 Provenance | III.2.9 | every measurement carries definition/version + source window + clock/session ID + instrument + injected timestamp + quality state + engine version; no unsupported statistic fields without evidence ref |
| T10 Golden fixtures | III.2.10 + Acceptance a | EUR/XAU/BTC/JPY/Fib fixture reproduction (per frozen fixture program, measurement-layer subset — later-bloc cases disclosed); manifest hashes recorded; synthetic bars labeled; canonical constants cited by evidence ID |
| T11 Label/serialization discipline | Acceptance b, d; invariant #18 | no prediction/signal vocabulary in enums or serialized output; status labels factual only; touch/acceptance/path distinctions survive serialization round-trip; bounded enums, no free text; measurements immutable (core law) |
| T12 Boundaries | §3 exclusions; Book gate | no network (socket refusal guard); import discipline (no Book I authority modules, no frozen files); no corpus writes; fixtures labeled historical; `discover_migrations() == [1, 2, 3, 4]`; readiness seam unchanged; Book II 50 hashes + 23 pins + Book I manifest + III.1 11-module hashes unchanged after the suite; deterministic repeat runs; no credentials/PII in data path; no trading/game concepts (with the disclosed canonical `trigger_levels` exception) |

## 9. Failure and security matrix

| Condition (frozen) | Required behavior | Test |
|---|---|---|
| Incomplete/missing input data | `DATA_QUALITY_BLOCKED` or model-declared degraded state via III.1 `QualityPolicy` — never a fabricated measurement | T1, T9 |
| Clock/session cannot be resolved | `NO_CALCULATION` (explicit, not empty-success) | T5 |
| Anchor unresolved / invalidated | coordinates blocked with explicit refusal code; no projection | T3, T4 |
| Model or calibration version missing | `MODEL_VERSION_UNAVAILABLE` — never silent fallback to another version | T2 |
| Evidence missing for a statistic | measurement may still exist when its rule is canonical, but attaches **no unsupported statistic** (no statistical/probability fields without an evidence ref) | T9 |
| Higher/lower layer conflict | return conflict/state facts; never an invented confluence score | T8 |
| Unknown tier / out-of-band value | explicit unclassified refusal — never nearest-bucket guessing, never silent no-go inflation | T2 |
| Unknown measurement definition/version | refusal; version drift requires a new definition_version (core law) | T9, T11 |
| Secrets/PII in the data path | none exist: no credentials, bounded enums, no free-text payload; any emitted events would go through Book II redaction discipline | T11, T12 |
| Frozen-surface drift (Book I/II **and** III.1) | manifest-hash test over 50 Book II hashes + 23 planning pins + Book I manifest + 11 III.1 module hashes — all unchanged after implementation/tests | T12 |

## 10. Known gaps and stop conditions

Known gaps (recorded, not hidden):

- **III.2-GAP-1** — The canonical Fib R15 Range Birth eligibility rule is
  not materialized in the corpus (model card: "must be materialized from
  R15 before autonomous signal generation"). III.2 implements the
  eligibility *interface* (states + first-class output) and rules only
  where a canonical rule exists; the production anchor rule requires a
  governance materialization before automation approval (III.5 boundary).
  R11 generic-pivot fallback remains forbidden and is absent by
  construction.
- **III.2-GAP-2** — JPY pair-native daily/weekly tier tables are only
  partially canonical: the 12–4PM DT structures (132/168/187.5) exist in
  the JPY card; complete per-pair tier/AU tables do not. Implemented only
  where canonical; the remainder is a disclosed gap, never invented.
- **III.2-GAP-3** — XAU calibration exists as spatial bands (25–50
  normal / 50–68 failure / 68+ repair / 100–110 snap) plus promoted
  examples (68+8h→80, 120+8h→132) and quarter-zone doctrine — not an
  EUR-style tier table. Encoded with explicit calibration status
  (`RESEARCH`/doctrine, cited to evidence IDs); no invented XAU tier
  constants.
- **III.2-GAP-4** — No event/news historical calendar exists in-repo.
  Event objects and consumed/residual budget arithmetic are implemented
  over synthetic labeled events; real event history requires
  operator-supplied canonical slices.
- **III.2-GAP-5** — Golden measurement fixtures build on synthetic bar
  slices (III.1 GAP-1 carries) plus canonical constant tables cited by
  ID. Real bar slices replace synthetic bars when the operator supplies
  them; fixture reproduction is a contract test, never performance
  evidence.
- **III.2-GAP-6** — Higher-order measurement definitions (D3 prior,
  unfinished side, completion, M1/M2 semantics) are evidence-bound per
  the EUR Higher Order card ("exact definitions … must travel with
  evidence"). Structure and hierarchy are implemented; statistical
  parameters are referenced by evidence ID, never hardcoded as engine
  constants.

Carried upstream: III.1 GAP-1…GAP-5 (synthetic fixtures; sessions only
where canonically defined; M5 final-bar scoped to its source lineage;
provider seam `NOT_CONFIGURED`; scripted-streaming parity only).

Stop conditions (report, do not improvise):

- Any frozen clause that cannot be implemented without contradicting a
  Book I/II frozen contract, the III.1 ratified interfaces, or by
  inventing a non-canonical calibration/session/anchor rule → stop and
  report.
- Any need to modify a frozen Book I/II file, any III.1 module, the
  container readiness seam, or add a migration → stop; governed packet
  required first.
- Conflicting canonical sources (e.g., two calibration tables for the
  same model+calibration version, or a golden-fixture number that
  contradicts a canonical constant) → operator/governance ruling
  required; never pick silently.
- Any pressure to emit a probability, confluence score, prediction,
  expectancy or performance metric from this layer → stop; that is a
  different Bloc's violation of the frozen plan.
- Being blocked on III.2 does **not** authorize starting III.3 or any
  other Bloc without a new operator handoff.

## 11. Acceptance / ratification requirements (this Bloc)

Per the frozen Book III gate §Evidence pack: `PLAN.md` (this file),
`ACCEPTANCE.md`, implementation commit ladder (later, separate
authorization), test output, `EVIDENCE.md`, known-gaps list, and a
ratification record — produced at implementation time. Clause→test
mapping is frozen now in `ACCEPTANCE.md`; any implementation must
satisfy it or report a deviation, never weaken it. The EVIDENCE at
implementation time must also re-verify the III.1 interface hashes
recorded in §6 and disclose which golden-fixture-program cases are
deferred to III.3+ (basket-role and ST/P90 cases) versus reproduced here.

## 12. Handoffs

- **To III.3 (next in frozen order):** measurements, calibration tables
  and anchor-eligibility outputs are *facts* — model runtimes consume
  them and may not redefine them (core law). `measurement_engine_version`
  enters model identity inputs together with the III.1 clock/session
  registry versions (cross-model invariant #1).
- **To III.4/III.5:** first-delivery order, range-left, rekey
  coordinates and anchor status feed the state/path engine and the setup
  gate; automation approval remains blocked until III.2-GAP-1's R15 rule
  is materialized by governance.
- **To Book IV/V:** unchanged — facts not prose; this Bloc adds no
  prose, no API, no rendering, no advice.
