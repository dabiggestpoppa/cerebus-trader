# BOOK III — END-TO-END INTEGRATION PLAN

**Book:** III — CEREBUS Market Intelligence
**Packet:** BA-23 Rung 1 (planning + release-gate audit only)
**Status:** PLANNING — frozen on commit; implementation NOT authorized by this document
**Starting head:** `ecb97ee2f5b8ba7adfd407997be379fee49ffc7d`
**Branch:** `forge`
**Governing plans:** `planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`,
`planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md`,
`planning/forge/AGENT_EXECUTION_HANDOFF_V1.md`,
`planning/forge/PLANNING_FREEZE_MANIFEST_V1.md`

This plan adds no acceptance standard. It resolves the frozen Book III gate into an
executable cross-bloc program and names every dependency that is still missing.

---

## 1. Scope

### In scope

- The six ratified Book III blocs as one deterministic pipeline.
- Cross-bloc contracts at every boundary.
- The Book III end-to-end acceptance program (`tests/test_forge_book_iii_integration.py`).
- Market-data provider prerequisites (design only).
- Snapshot/transition durability contract (design only).
- Router registration governance (options only).
- Book I Setup Card ADR recommendation (decision-ready, no schema change).
- Book IV/V consumer handoff and a readiness decision.
- Gap ownership, beta/production classification and dependency order.

### Out of scope

- Any code, test, adapter, route, migration, fixture or consumer implementation.
- Book IV, V, VI, VII or VIII planning or build.
- Provider selection, credentials or live-data claims.
- Book I schema modification.
- Deployment, exposure or production GO.

### Law

A ratified component is a verified part. A ratified integration is a verified system.
No stage inherits authority from an unfinished downstream gate.

---

## 2. Verified foundation at `ecb97ee`

| Item | Verified state |
|---|---|
| `HEAD` == `origin/forge` | `ecb97ee2f5b8ba7adfd407997be379fee49ffc7d` |
| Book III modules | 11 + 12 + 13 + 13 + 16 + 14 = **79** |
| Book I | frozen manifest present; corpus unmodified |
| Book II | 50 frozen contract hashes; 23 planning pins |
| Migrations | SQL `001`–`004` present; no new migration |
| Provider readiness | `market_data` seam discloses `NOT_CONFIGURED`; no adapter |
| Routes | `/forge/v1/health`, `/ready`, `/meta` only; `routes.py` frozen (`145757e0…`) |
| III.6 gateway | `IntelligenceGateway.read / read_guarded`; adapter contract tested, unregistered |
| CI | run `42062114363` at `ecb97ee`, `test` + `postgres` green |

All six blocs hold `PASS/CLOSED` ratification. Their combined interfaces are the
input to this integration; none may be modified by it.

---

## 3. Integration architecture

### 3.1 The pipeline

```
raw provider feed (NOT_CONFIGURED)
  -> III.1 normalized observation (Bar, clock, session ownership, quality)
  -> III.2 Measurement (immutable, provenance-complete)
  -> III.3 ModelOutput (pinned model_id + version, layer, levels, no-go)
  -> III.4 StateSnapshot / TransitionLedger / DeliveryPath (ordered history)
  -> III.5 SetupEvaluation (four-valued eligibility, surface, evidence refs)
  -> III.6 Snapshot / InstrumentView / BasketView / SetupContext (policy-gated)
  -> Book IV explanation, Book V rendering
```

Each arrow is a **data** edge, never a re-derivation edge. A consumer receives
immutable facts; it may not recompute, average, promote or authorize them.

### 3.2 Interface matrix

| Edge | Producer API | Consumer API | Identity / version | Quality / availability | Refusal | Evidence | Determinism | Open gaps |
|---|---|---|---|---|---|---|---|---|
| P→III.1 | none (seam) | `assess_finality`, `final_state_input`, `dedupe`, `reconcile` | `MARKET_DATA_SCHEMA_V1`, `CLOCK_REGISTRY_V1`, `SESSION_REGISTRY_V1` | 8-flag vocabulary; nonfinal never final | `NonFinalError`, `UnsupportedClockError`, `UnknownAliasError` | source timestamp + provider + bar digest | `content_digest`, canonical key | III.1-GAP-1/3/4/5, III.6-GAP-2 |
| III.1→III.2 | `Bar`, `Finality`, quality flags | `Measurement` constructors + engines | `MEASUREMENT_ENGINE_V1`, definition id/version | quality state on every measurement | `DataQualityBlockedError`, `QualityVocabularyError` | window digest, clock/session ids | `Measurement.content_hash` | III.1-GAP-2, III.2-GAP-1/2/3/4 |
| III.2→III.3 | `Measurement` facts | `ModelRequest.measurements`, `resolve()` | `(model_id, model_version)` registry | `DataOutcome`, no-go reasons | `ModelVersionUnavailableError`, `InputMeasurementMissingError`, `RuleNotMaterializedError` | `claim_refs` empty; measurement ids carried | `ModelOutput.payload_hash` | III.2-GAP-1/2/3, III.3-GAP-1/2/3/8 |
| III.3→III.4 | `ModelOutput` | `StateSnapshot`, `build_path`, `open_ledger` | model + state engine version | quality carried verbatim; stand-down lock | `StateContractError`, `AmbiguousPathError`, `EligibilityWithoutAuthorityError` | snapshot/transition refs | `snapshot_hash`, `history_hash`, `path_hash` | III.3-GAP-1/2/8, III.4-GAP-3/10/12 |
| III.4→III.5 | `StateSnapshot`, `StandDownRecord`, `DeliveryPath` | `SetupEvaluationRequest`, `evaluate_setup` | setup id/version + parent model ids | stand-down blocks eligibility; quality gate | `SetupRefusalCode` (`BLOCKED`/`UNRESOLVED`) | `EvidenceReference` with status | `payload_hash` on record | III.4-GAP-1/2/8, III.5-GAP-1…7 |
| III.5→III.6 | `SetupEvaluation`, `SetupRecord` | `CompositionInputs.setup`, `setup_payload` | setup id/version verbatim | eligibility verbatim, never upgraded | `SCHEMA_INCOMPATIBLE`, surface refusals | claim/evidence links, population key | snapshot component hashes | III.5-DEFECT-1, III.6-GAP-3 |
| III.6→Book II | `IntelligenceGateway.read` | `ForgePolicyEnforcementService.authorize/guard` | policy fingerprint | denial before load | uniform `EXPOSURE_FORBIDDEN` | audit record per decision | cache key by identity + principal scope | III.6-GAP-6 |
| III.6→Book IV/V | `Snapshot.payload()`, `InstrumentView`, `BasketView` | consumer DTO (not built) | `INTELLIGENCE_API_VERSION`, schema hash | quality/freshness facts | 18 refusal codes | `EvidenceLink` list | canonical JSON, `bounded_json` | III.6-GAP-7/8 |

### 3.3 Required invariants

| # | Invariant | Enforced by | Proposed test |
|---|---|---|---|
| I1 | Data quality survives every boundary | quality carried in `Measurement`, `ModelOutput`, `StateSnapshot`, setup `data_quality`, III.6 `QualityFacts` | IN-T2-1…9 |
| I2 | Model generations stay pinned | `resolve(model_id, version)`; snapshot key includes version | IN-T8-1…8 |
| I3 | Range/anchor identity survives model and transition | `AnchorEligibility` → `ModelOutput.active_ranges` → snapshot levels | IN-T1-1, IN-T3-4 |
| I4 | First-delivery ordering cannot be lost | `build_path` ordering + `DeliveryPath.delivery_order` | IN-T4-1…8 |
| I5 | No-go locks survive into setup eligibility | `StandDownRecord.eligibility_locked` → `evaluate_setup` gate | IN-T5-1…9 |
| I6 | Setup classification survives into snapshots unchanged | `setup_payload` copies verbatim; no promotion path | IN-T5-6, IN-T10-3 |
| I7 | Book II policy applies before protected composition | `IntelligenceGateway.read` authorizes before `loader()` | IN-T6-1…7 |
| I8 | Historical reconstruction uses pinned versions | `HistoryStore.reconstruct` + hash verification | IN-T8-1…8 |
| I9 | Missing provider cannot create a current-live snapshot | `PROVIDER_NOT_CONFIGURED` short-circuit; `is_live_claim_permitted` false | IN-T2-1, IN-T12-4 |
| I10 | Synthetic fixture proof cannot become empirical evidence | fixture labels + evidence-ref refusal | IN-T9-5, IN-T12-5 |
| I11 | Cache reuse cannot widen exposure | `ResponseKey` exposure + policy fingerprint + principal scope | IN-T11-1…7 |
| I12 | Valid setup cannot manufacture execution authority | no order/size/allocation field exists; `automation_permitted` false | IN-T5-7, IN-T10-4 |

No new invariant is introduced: I1–I12 restate the frozen cross-model invariants
(Book III plan) and the institutional law.

---

## 4. End-to-end lineage plan

One canonical traversal must be provable end to end:

1. **Observation.** Build a `Bar` with `MARKET_DATA_SCHEMA_V1`, named clock,
   session ownership and `Finality.FINAL`; compute `content_digest`.
2. **Measurement.** Derive a range measurement with definition id/version and
   the bar digest as its window; assert `quality` and provenance.
3. **Model.** Resolve `EUR.DAILY.NEWS_REKEY.V1 / PHASE1`, pass the measurement and
   the prior state; receive `ModelOutput` with layer, levels and empty
   `claim_refs`.
4. **Transition.** Build a `StateSnapshot` from the output, `build_path` over
   declared targets and observations, append transitions to a ledger, verify
   `history_hash`.
5. **Setup.** Evaluate `SETUP.XAU.QUARTER_ZONE.V1` or the EUR card with the
   parent output, anchor eligibility, stand-down and quality facts; receive a
   four-valued verdict and a `SetupRecord`.
6. **Snapshot.** Compose `CompositionInputs`, obtain a `Snapshot` with derived
   id, component hashes and sections; pass it through `IntelligenceGateway.read`
   as an authorized principal.
7. **Consumption.** Serialize with `canonical_json`; re-parse; assert the
   payload hash and every refusal/enum survives.

Each step is separately unit-proven today. What is **not** proven is that the
seven steps compose over one object graph with one clock and one model version.
That is the purpose of the integration suite.

---

## 5. Market-data provider integration prerequisites

Design only — no provider selected, no credentials, no readiness claim.

### 5.1 Required coverage

| Class | Instruments | Timeframes | Status |
|---|---|---|---|
| Launch-model | EURUSD, XAUUSD, USDJPY, AUDJPY, EURJPY, BTCUSD | M5 for session geometry; H1/H4/D1/W1/MN as each model declares | required for beta |
| Research-only | Fib/Range Birth inputs; historical ST/P90 slices | as canonical source declares | not launch-blocking |

No instrument outside the canonical registry may be served; aliases normalize
through III.1 only.

### 5.2 Contract requirements

- **Bars:** open/close UTC, OHLC, volume where available, provider id, source
  timestamp, finality, revision marker, quality flags.
- **Granularity:** exact declared bars per model; no resampling inside III.2.
- **Clock/session:** named IANA clocks; research-day ownership by lineage;
  fixed-offset historical artifacts retain `EST_NO_DST` identity.
- **Finalization:** provider final flag plus III.1 `assess_finality`; late
  corrections enter as `REVISED`, never silent overwrite.
- **Gaps/duplicates:** explicit `GapMarker`/dedupe; missing bars never invented.
- **Reconnect/replay parity:** a reconnect replay must reproduce the same
  normalized bars and the same measurement hashes (III.1 parity runners).
- **Rate limits/failure:** bounded retry, explicit `STALE`/`UNAVAILABLE`,
  no fallback to last-known as "current".
- **Monitoring:** freshness, gap rate, revision rate, finality lag, parity drift.
- **Fixture validation:** every provider adapter must reproduce the committed
  golden slices before it can feed a live snapshot.

### 5.3 Required authorization

A dedicated provider packet must be separately authorized to: select a provider,
add an adapter behind the Book II provider port, set the readiness seam to
configured, add credentials outside the repo, and add replay-parity tests.
Until then `market_data: NOT_CONFIGURED` is binding and no current-live claim is
permitted.

---

## 6. Snapshot and transition durability

Minimal contract, using the existing Book II persistence framework. No
migration is created in this rung.

### 6.1 Record contract

| Field | Meaning |
|---|---|
| `record_id` | logical identity; `SNAP.` id for snapshots, ledger id for transitions |
| `snapshot_version` | III.6 API/schema version + model version |
| `sequence` | monotonic transition index within a ledger |
| `prior_hash` | previous record hash (genesis = null) |
| `source_cutoff` | data cutoff that produced the record |
| `replay_identity` | key payload hash enabling deterministic reconstruction |
| `payload` | canonical JSON of the immutable record |
| `retention_class` | operational / research / evidence-bound |
| `exposure` | Book I exposure carried verbatim |

### 6.2 Behaviour

- **Corrections:** a corrected input produces a *new* record with a new cutoff
  and a `supersedes` link; no in-place update.
- **Replay integrity:** reconstruct from retained inputs, recompute the hash, and
  refuse on mismatch (`REPLAY_HASH_MISMATCH` / `HISTORICAL_UNAVAILABLE`).
- **Retention:** transition history retained at least for the operational
  window the product promises; eviction is explicit (`HISTORICAL_NOT_RETAINED`).
- **Backup/recovery:** restore drill must reproduce the latest record hash and a
  replayed historical hash before the store is declared usable.
- **Access:** reads go through the same policy gate; records are exposure-tagged;
  no cross-principal query path.
- **Migration:** one additive migration owned by a Book II-authorized packet;
  existing tables and frozen contracts unchanged.

### 6.3 Beta vs durability

Valid without durability (in-memory retained inputs): single-session current
snapshots, fixture replay, deterministic identity and policy tests.

Requires durability: cross-session history, "what was the state at T" answers,
after-the-fact explanation, incident recovery, and any paid historical surface.

---

## 7. Router governance options

`app/forge/service/routes.py` is frozen (`145757e0…`). Three options, no change
made here.

| Option | Mechanism | Files touched | Integrity consequence | Tests | Deployment |
|---|---|---|---|---|---|
| **R1 authorized extension** (recommended) | Operator-authorized Book II amendment; add intelligence routes inside the existing `/forge/v1` router factory | `routes.py`, freeze manifest, new route module | Requires a new Book II freeze version and recorded hashes; old hash superseded by governance record, not silently | Router contract tests, auth 401/403, refusal envelope, correlation id | Normal service deploy |
| **R2 composition seam** | If a supported registration seam exists, register a sub-router from the composition root | `container.py` / composition root, new module | Still touches frozen Book II files; no seam exists today for domain routers — verified: only `create_forge_router` with three endpoints | Same plus seam-ownership test | Same |
| **R3 internal-only** (current state) | Keep `IntelligenceGateway` unregistered; callers are in-process only | none | No frozen file changes | Existing 258 III.6 tests | No external exposure |

Recommendation: **R3 now, R1 as the first Book II packet after beta data
readiness.** R2 is not available without inventing a seam, which the freeze
forbids. Any R1 work requires explicit operator authorization and a versioned
freeze update; no agent may edit the router opportunistically.

---

## 8. Book I Setup Card defect — ADR recommendation

Defect: all three canonical cards fail `SetupOperatorCard` validation with three
errors (`SETUP.*` vs `SET.*`, lifecycle vs `EvidenceStatus`, parent model ids).

| Option | Change | Blast radius | Frozen consequences | Migration | Tests | Rollback | Consumer impact |
|---|---|---|---|---|---|---|---|
| A — widen ID acceptance | Book I kernel accepts `SETUP.*` | `CanonicalId`, downstream parsers | Book I freeze hash changes; all Books re-verify | none | kernel + all bloc suites | revert kernel commit | low; IDs unchanged |
| B — correct card schema | new Setup identity/lifecycle/parent typing | Book I kernel + all three cards + Book II policy refs | largest; corpus rewrite; evidence links re-bound | data migration for cards | full-program re-ratification | restore corpus snapshot | high; ID churn |
| **C — govern a corpus-adapter schema** (recommended now) | Book I unchanged; an ADR defines a read-only adapter DTO and explicitly marks machine validation unavailable | Book I untouched; III.5/III.6 already implement it | no freeze change; defect recorded open | none | adapter conformance + refusal tests | delete adapter | low; strict ops still refuse `SCHEMA_INCOMPATIBLE` |

Recommendation: **C now, B as the V1.1 canonical repair.** A is a subset of B
with the same freeze cost but leaves the lifecycle mismatch unresolved. C keeps
the defect honest and does not pretend serialization is a repair. Any change
requires separate operator authorization; this rung modifies nothing.

---

## 9. Book IV/V consumer handoff

### 9.1 Stable consumer contract (III.6 DTO)

`snapshot_id`, `schema_version`, `view` (CURRENT/HISTORICAL), `instrument`,
`model_id/version`, `layer`, `as_of`, `data_cutoff`, quality/freshness facts,
typed levels, path + first-delivery order + range-left, setup eligibility and
surface, evidence links with status, no-go/stand-down, warnings, refusal codes,
exposure classification, and structured explanation facts.

### 9.2 Prohibitions carried to consumers

- Ask CEREBUS may explain only these facts; it may not compute state, levels,
  eligibility or statistics, and may not upgrade research to production.
- The UI may render only these facts; it may not derive signals, scores or
  trade instructions, and must display eligibility and exposure verbatim.
- No consumer may treat a synthetic fixture as market evidence.

### 9.3 Readiness decision

**Book IV planning and prototype implementation MAY begin against the internal
`IntelligenceGateway` adapter contract and committed DTO fixtures.** Reasons:
the DTO is frozen by 258 tests, the gateway is the only composition entry, and
consumer work cannot alter Book III truth. It may **not** be wired to a
production route, live data or paid exposure until R1 registration, provider
readiness and durability land. Book V may render the same DTOs with synthetic
data; it may not ship a production dashboard before those gates.

---

## 10. Work packets

| ID | Authority | Required upstream state | Deliverables | Tests | Gate | Parallel | Stop conditions |
|---|---|---|---|---|---|---|---|
| WP-1 | BA-23 R2 / Book III integration | this plan frozen | `tests/test_forge_book_iii_integration.py`, integration fixtures, `EVIDENCE.md` | 96 proposed names | integration ratification | no (critical path) | any bloc interface drift |
| WP-2 | Book II amendment | WP-1 green; operator authorization | route extension + freeze v1.1 | router/auth/refusal | Book II re-freeze | yes (after WP-1) | frozen hash conflict |
| WP-3 | Provider packet | WP-1; provider selection authorized | adapter, readiness seam, parity fixtures | parity/reconnect/finality | provider readiness | yes (after WP-1) | contract drift, credentials absent |
| WP-4 | Book II durability | WP-1; data model approved | additive migration + store + recovery drill | replay/backup/access | durability gate | yes (after WP-1) | destructive migration |
| WP-5 | Book I ADR | operator decision | ADR + (if B) schema v1.1 | kernel + corpus | Book I re-freeze | parallel | corpus freeze conflict |
| WP-6 | Book IV | WP-1 DTO frozen | interpreter/retrieval/validator against adapter | IV suite | Book IV gate | yes (after WP-1) | LLM recomputing state |
| WP-7 | Book V | WP-1 DTO + WP-2 | vault/dashboard/workspace | V suite | Book V gate | yes (after WP-2) | UI inventing signals |
| WP-8 | Book VI | II policy/ports | catalog/entitlement/ledger | VI suite | commerce gate | parallel | checkout treated as entitlement |
| WP-9 | Book VII | I schemas + II persistence | intake/evidence/promotion | VII suite | research gate | parallel | self-promotion |
| WP-10 | Book VIII | I–VII | security/launch evidence | VIII suite | launch GO | no (final) | any gate open |

Critical path: **WP-1 → WP-2/WP-4 → WP-3 → WP-6/WP-7 → WP-8 → WP-10**.
Permitted parallel: WP-5, WP-8, WP-9 after WP-1; WP-3 and WP-4 after WP-1.

---

## 11. Ratification criteria

Integration is ratified only when:

1. All 96 proposed tests pass, with 0 missing, 0 skipped, 0 xfail, 0 weakened.
2. The 79 module hashes match their bloc baselines; Book I/II freeze 50/50;
   migrations unchanged; provider seam unchanged.
3. One lineage traversal produces one identity through all six blocs.
4. Denial-before-composition is proven with a spy loader.
5. Historical replay reproduces a recorded hash; drift and missing retention are
   distinct refusals.
6. The Book I card defect is still reproduced and still open.
7. Full repository regression is green and CI passes on the published head.

Passing isolated bloc suites is not integration evidence, and integration
ratification is not production approval.
