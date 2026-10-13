# BOOK III / BLOC III.1 — MARKET DATA & CLOCK CONTRACTS — PLAN.md

Status: **PLANNING ONLY — committed before any implementation** (frozen
Book II order rule reused for Book III: PLAN + ACCEPTANCE are committed
first; no implementation authorized by this packet).
Date: 2026-10-12
Branch: `forge` · Planning head: `9b343b6c8f3d62084ff1d995e40dc9d91a60a0ed`
Frozen source: `planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(pinned in `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` line 35) —
sections `# BLOC III.1` (Ch III.1.1–III.1.9 + Acceptance III.1),
`# BOOK III CROSS-MODEL INVARIANTS`, `# BOOK III FAILURE BEHAVIOR`,
`# BOOK III ACCEPTANCE / RATIFICATION GATE` §Data/clock, and
`# RECOMMENDED IMPLEMENTATION ORDER` step 1.

Scope here is exactly the frozen Bloc III.1 chapters — no Book III scope is
inferred from the Book title. Cross-checked against
`planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` (§5 graph:
`I.3-I.5 -> III.1-III.3 -> III.4-III.6`; Phase C order) and
`planning/forge/AGENT_EXECUTION_HANDOFF_V1.md` (`III.1 -> III.2 -> …`;
"later phase may start early only when its required contracts are already
frozen and the work does not create a circular dependency" — both hold).

---

## 1. Governing authority model (mandatory, restated — Phase 3)

These distinctions govern every design decision in this Bloc and are
re-verified in ACCEPTANCE.md:

- **Model ≠ Claim ≠ Evidence ≠ Setup ≠ Artifact.** III.1 produces
  *normalized data facts* (instruments, bars, sessions, quality states).
  It never produces claims, evidence, setups, or model outputs. Evidence
  references point to Book I's frozen corpus; III.1 never grants itself
  evidence authority.
- **Historical observation ≠ current market state.** Replay fixtures and
  fixed-offset research artifacts are historical. They are labeled as
  such and can never be served as current state (the III.6 boundary).
- **Simulation ≠ empirical performance.** Any synthetic fixture bar is
  labeled `SYNTHETIC_FIXTURE` at creation and is never citable as evidence.
- **Provider output ≠ canonical truth.** Raw provider feeds are
  observations to normalize and quality-flag — never canonical status.
- **Semantic similarity ≠ evidence authority.** No retrieval/vector logic
  exists in this Bloc (Book I owns that authority; frozen).
- **Target touch ≠ trade win rate; L3 ≠ L2 ≠ L1; manual ≠ automated
  parity; ST manual vs P90 lineage** — no trading/path/automation
  concepts exist at this layer at all; the Bloc must not introduce any.
- **BTC Tracker ≠ BTC Game.** III.1 defines clocks/sessions for
  instruments generically; it imports no Game setups and none may be
  inferred from session naming.

## 2. Scope (frozen chapters, in)

| Ch | Frozen requirement (compressed; plan is authority) |
|---|---|
| III.1.1 | Canonical instrument schema: instrument_id, symbol/provider aliases, asset class, quote/base conventions, tick/pip/point unit, price precision, supported clocks/timeframes, provider mappings. **Asset-native units mandatory — EUR pips / Gold points / BTC dollars are not interchangeable.** |
| III.1.2 | Normalized bar: instrument, timeframe, open/close time, OHLC, volume when available, provider, finality, source timestamp, quality flags. Rules: no future/incomplete bar treated as final; duplicates deterministic; revisions explicit; missing bars visible. |
| III.1.3 | Named-timezone semantics (IANA) for live/session calc; research artifacts that used fixed EST/no-DST **retain their original clock identity** (never silently converted). DST spring/fall + fixed-offset tests. |
| III.1.4 | Explicit research-day assignment; known EUR/BTC lineage assigns evening bars to the following research day where the canonical source specifies it; **no calendar-date assumption**. |
| III.1.5 | Versioned session objects: Asian range, London/MLR, daily checkpoints, weekly seed windows, model-specific DT windows, month/quarter boundaries. **Session definitions belong to model/calibration versions.** |
| III.1.6 | Exact inclusive/exclusive boundaries and final-bar semantics (canonical example: M5 `02:55` final bar for a 19:00–03:00 construction where the source specifies it). |
| III.1.7 | Quality flags: `COMPLETE, GAP, DUPLICATE, REVISED, STALE, NONFINAL, OUTLIER_SOURCE, UNSUPPORTED_CLOCK`; models declare which flags block vs warn. |
| III.1.8 | Provider adapters map raw feeds into the normalized contract; **provider-specific timestamps/symbols never enter model logic directly**. |
| III.1.9 | Historical/live parity fixtures: identical normalized session ownership in replay and live-style streaming. |

Plus the applicable cross-model invariants (#1 data clock is part of
model identity; #2 asset calibration local unless transfer validated;
#18 no deterministic rhetoric in runtime status labels) and the
`# BOOK III FAILURE BEHAVIOR` clauses that land on this layer
(incomplete data → `DATA_QUALITY_BLOCKED`/degraded per contract;
unresolvable clock/session → `NO_CALCULATION`; feed failure → explicit
state, never invented bars).

## 3. Scope exclusions (out — never in this Bloc)

- No measurements/tiers/coordinates/path metrics (III.2).
- No model runtimes, state machines, snapshots (III.3/III.4).
- No setups, eligibility, triggers (III.5); no API/endpoints/caching (III.6).
- No live market-data provider network calls, credentials, or concrete
  provider SDKs. Normalization is proven over committed fixtures and
  scripted fake raw feeds only. The container readiness seam
  `market_data: NOT_CONFIGURED` (`app/forge/service/container.py`) is
  **not modified** — wiring is composition-root work under a later
  authorized packet (Book II D4 boundary respected).
- No new persistence migration. III.1 holds fixtures/state in process;
  any future `005_*.sql` for market-data tables requires its own governed
  packet (Book II freeze manifest §Enforcement; frozen files untouched).
- No Book I corpus writes, no exposure/policy changes, no HTTP surface,
  no trading/advice/execution concepts (Book III exclusions restated).
- No modification of any frozen Book I/II file (50-file Book II freeze
  manifest + 23 planning pins + Book I freeze manifest).

## 4. Phase 0 foundation (verified at this head; summary)

`HEAD == origin/forge == 9b343b6…0a0ed`, tracked tree clean; planning
freeze `60e0675` ancestor; 23/23 pins identical; Book I I.5
**RATIFIED (CLOSED)**; Book II **RATIFIED — CONTRACTS FROZEN** with G-F7
commit `e45d23371b14cca6b6dc1085dc56d8b9f2fe03aa` on ancestry; Book II
50-file freeze manifest re-verified (0 hash mismatches); final-head CI
run 38329583650 success both jobs (test 1016/29, postgres 1045/0);
phase-order governance disposition resolved (Book III phase C may start;
no circular dependency); downstream gap register: B-class empty,
D-class items (GAP-03/06/10/11/13/14, Book-VI share of GAP-05) owned by
later Books — **none is a Book III.1 prerequisite**.

## 5. Dependency and ownership matrix

| # | Upstream contract | Owner | Frozen status | How III.1 uses it | Ready? |
|---|---|---|---|---|---|
| D1 | Canonical corpus schemas / taxonomy (`RETRIEVAL_OBJECT_SCHEMA_V1`, `CEREBUS_CANONICAL_TAXONOMY_V1`) | Book I | Frozen, I.1–I.5 ratified | Cross-reference vocabulary only; instrument/session IDs align with canonical IDs; **no corpus writes** | ✅ |
| D2 | Evidence/Claim registry (`CLAIM_REGISTRY_V1`, provenance schema) | Book I | Frozen | Fixtures cite evidence IDs where a canonical source defines a session rule; III.1 never creates evidence | ✅ |
| D3 | Canonical model cards (BTC `19:00–03:00` NY research frame, EUR research-day lineage, session rules) | Book I corpus | Frozen | Source of truth for research-day/session definitions implemented in III.1.4/III.1.5 | ✅ |
| D4 | Persistence port + records + SQL gateway (`persistence/port.py`, `records.py`, `sql/gateway.py`, migrations 001–004) | Book II | Frozen (50-file manifest) | Structural pattern only in III.1 (explicit port injection if storage is added later); **no new migration now** | ✅ |
| D5 | Observability (correlation, bounded events, redaction, frozen audit streams) | Book II | Frozen | Reuse correlation ID propagation + redaction for any emitted quality/telemetry events; **no new audit stream or event field** (frozen vocabulary) | ✅ |
| D6 | Provider-port architecture (registry/factory/resilience/fallback patterns) | Book II | Frozen | Structural precedent for III.1.8 normalization adapters; the market-data port itself is a **Book III artifact** (seam reserved in container readiness) | ✅ |
| D7 | Policy/exposure + identity | Book II | Frozen | Not exercised: III.1 has no HTTP/resource surface; policy applies at III.6 before response (frozen plan Ch III.6.5/III.6.12) | ✅ (N/A at this layer) |
| D8 | Runtime: Python `zoneinfo` (IANA) + `tzdata` | stdlib/platform | Available (verified: `ZoneInfo('America/New_York')` resolves) | Named-timezone engine for III.1.3; **no new pip dependency** | ✅ |
| D9 | Provider raw-feed fixtures | Book III (this Bloc) | To be authored | Committed fixture slices + scripted fake raw feeds; synthetic bars labeled `SYNTHETIC_FIXTURE`; real-slice fixtures cite their canonical evidence ref | ✅ (authored pre-implementation rung) |

**Missing prerequisites: none.** Verdict: dependency-ready.

## 6. Existing implementation reuse (actual repository state)

- `app/forge/` has **zero** market-data/OHLC/session/clock code — this is
  greenfield; no parallel abstraction risk. Grep hits for
  `timezone/session` in identity/auth/retrieval are unrelated concerns.
- Container readiness already discloses the honest seam
  (`market_data: NOT_CONFIGURED`, `required=False`, note "belong to Book
  III") — to be reused unchanged, not rewired.
- Legacy Signal Guard code (`app/state_engine.py`, `app/validator.py`)
  uses naive `datetime.now(timezone.utc)` with no DST/session semantics —
  **not reusable** for III.1 and deliberately not touched.
- `app/adapters/{matchtrader,tradovate}.py` are 5-line stubs with no bar
  parsing — no reuse; concrete provider adapters are out of scope anyway.
- Reusable *patterns*: Book II's explicit-injection port style, bounded
  typed records (`records.py`), quality/README honesty vocabulary
  (`NOT_CONFIGURED` disclosure pattern), and Book I's fixture/manifest
  discipline (frozen fixtures + recorded hashes).

## 7. Proposed design (planning intent — implementation needs its own authorization)

Proposed package (new; touches no frozen file): `app/forge/market_data/`

| Module | Ch | Contents |
|---|---|---|
| `instruments.py` | III.1.1 | frozen dataclass/schema `Instrument`; native-unit enum (PIP/POINT/DOLLAR_PER_TICK…); alias table; per-instrument supported clocks; cross-unit arithmetic **refuses** |
| `bars.py` | III.1.2, III.1.6 | `Bar` normalized object; finality gate (future/incomplete ⇒ `NONFINAL`); deterministic dedup; explicit `REVISED` replacement; boundary helper for inclusive/exclusive final-bar rules |
| `clocks.py` | III.1.3 | IANA named-zone session math; `ClockIdentity` = (timezone rule, DST policy, epoch of rule) so fixed-offset artifacts keep `EST_NO_DST`-style identities instead of being converted |
| `research_day.py` | III.1.4 | explicit assignment function (instrument, lineage, bar close time) → research day; lineage-declared evening-shift rule; never `date()`-based |
| `sessions.py` | III.1.5 | versioned `SessionDefinition` registry keyed by (model_id, model_version, session_id); definitions loaded from canonical sources only |
| `quality.py` | III.1.7 | the 8 frozen flags; per-model blocking-vs-warning declaration table; `DATA_QUALITY_BLOCKED` / `NO_CALCULATION` outcomes |
| `normalize.py` | III.1.8 | raw-feed → normalized contract mapping; provider fields quarantined (never leak into downstream objects) |
| `parity.py` | III.1.9 | replay path vs streaming path runner over identical fixture slices; parity assertion helper |

Cross-cutting rules for the future implementation: pure functions +
frozen dataclasses; no network; no imports from `qa/`, `retrieval/`,
`provenance/` (Book I authority), `policy.py` changes, or frozen files;
deterministic serialization with explicit schema version fields
(`market_data_schema_version`, `session_registry_version` — required by
the Book III final record).

## 8. Proposed executable test matrix (summary; full clause→test map in ACCEPTANCE.md)

Proposed file: `tests/test_forge_market_data.py` (plus fixtures under
`implementation/forge/book_iii/bloc_iii_1/fixtures/`). All deterministic,
offline, SQLite/network-free.

| Group | Frozen driver | Representative proposed tests |
|---|---|---|
| T1 Instrument | III.1.1 | schema completeness; alias→canonical resolution; **cross-native-unit arithmetic refuses** (EUR pip vs Gold point vs BTC $) |
| T2 Bar contract | III.1.2 | future/incomplete bar never final; duplicate → deterministic single result; revision explicit `REVISED`; missing bar ⇒ `GAP` (never synthesized) |
| T3 DST/clock | III.1.3 | spring-forward and fall-back session boundaries; fixed-offset artifact retains original clock identity (no silent conversion) |
| T4 Research day | III.1.4 | evening-bar→following-day lineage rule deterministic; **differs from naive UTC/calendar date** (proves no calendar assumption); same input ⇒ same day (pure) |
| T5 Sessions | III.1.5 | registry versioned; session bound to model/calibration version; unknown session ⇒ fail-closed |
| T6 Final bar | III.1.6 | canonical `M5 02:55` final-bar of 19:00–03:00 construction; inclusive/exclusive edges each asserted |
| T7 Quality | III.1.7 | 8 flags exist; blocking-vs-warning honored (`DATA_QUALITY_BLOCKED` vs degraded); `UNSUPPORTED_CLOCK` never silently remaps |
| T8 Provider norm | III.1.8 | alias normalization to canonical ID; provider timestamps/symbols **absent** from normalized output; scripted fake raw feeds normalize identically |
| T9 Parity | III.1.9 | replay ≡ streaming on session ownership + quality state for every fixture slice |
| T10 Invariants | Cross-model #1/#2/#18 | clock identity travels with any downstream-facing state; no cross-asset unit leakage; status labels are factual enums (no rhetoric) |
| T11 Boundaries | Scope exclusions | no network calls; import discipline; no Book I/II frozen file mutated (manifest hashes unchanged after test run) |

## 9. Failure and security matrix

| Condition (frozen) | Required behavior | Test |
|---|---|---|
| Incomplete data | `DATA_QUALITY_BLOCKED` or model-declared degraded state — never fabricated bars | T2, T7 |
| Clock/session unresolvable | `NO_CALCULATION` (explicit, not empty-success) | T5, T7 |
| Unsupported clock for instrument | `UNSUPPORTED_CLOCK`, fail closed — never silent remap | T7 |
| Provider/feed fails or fixture feed ends | explicit `GAP`/`STALE` state; no invented bars (stale *serving* is an III.6 concern, labeled with data cutoff) | T2, T8 |
| Duplicate/revised source rows | deterministic dedup / explicit `REVISED` — no silent overwrite | T2 |
| Ambiguous research-day lineage | fail closed to explicit unresolved state; **no default calendar guess** | T4 |
| Secrets/PII in feeds | none exist: no credentials in the data path; any emitted events go through Book II redaction; quality flags are bounded enums (no free text payload) | T7, T11 |
| Protected corpus leakage | impossible by construction: no corpus reads in this Bloc; import discipline enforced by test | T11 |
| Frozen-surface drift | manifest-hash test: all 50 Book II freeze hashes + 23 planning pins unchanged after implementation/tests | T11 |

## 10. Known gaps and stop conditions

Known gaps (recorded, not hidden):
- **G1** — No real historical bar slices exist in the repository. Fixture
  strategy: (a) canonical numbers from frozen evidence/model cards cited
  by evidence ID where they define sessions; (b) synthetic fixture bars
  labeled `SYNTHETIC_FIXTURE`, never citable as evidence. If the operator
  provides real source slices later, they replace (b) with evidence refs.
- **G2** — Session definitions exist canonically only for some models
  (EUR/BTC lineage explicitly referenced by the frozen plan). Sessions
  are implemented **only where a canonical definition exists**; others
  are gaps listed in EVIDENCE, never invented.
- **G3** — The `M5 02:55` final-bar example is plan-canonical; other
  models' final-bar rules must be read from their canonical sources at
  implementation time or left as disclosed gaps.
- **G4** — Concrete market-data provider selection/wiring is undetermined
  (Book III scope, later packet); readiness seam stays `NOT_CONFIGURED`.
- **G5** — Live-vs-replay parity (III.1.9 "live-style streaming") is
  proven against a scripted streaming runner over fixtures; true
  live-feed parity requires G4's provider and is explicitly deferred.

Stop conditions (report, do not improvise):
- Any frozen clause that cannot be implemented without contradicting
  Book I/II frozen contracts or inventing non-canonical session rules →
  stop and report (never start a different Bloc without authorization).
- Any need to modify a frozen Book I/II file, the container readiness
  seam, or add a migration → stop; governed packet required first.
- Any ambiguity between canonical sources (e.g., conflicting session
  definitions) → surface as a gap for operator/governance ruling.

## 11. Acceptance / ratification requirements (this Bloc)

Per the frozen Book III gate §Evidence pack: `PLAN.md` (this file),
`ACCEPTANCE.md`, implementation commit ladder (later, separate
authorization), test output, `EVIDENCE.md`, known-gaps list, ratification
record — produced at implementation time. Clause→test mapping frozen now
in `ACCEPTANCE.md`; any implementation must satisfy it or report a
deviation, never weaken it.

## 12. Handoffs

- **To III.2 (next in frozen order):** normalized bars with finality +
  quality flags, session ownership, clock identities, native-unit
  instruments — measurements consume these facts and may not redefine
  them (core law: downstream may consume upstream state, never silently
  redefine it).
- **To III.3+:** `ClockIdentity` and `SessionDefinition` versions become
  part of model identity (cross-model invariant #1).
- **To Book IV/V:** unchanged — facts not prose; this Bloc adds no
  prose, no API, no rendering.
