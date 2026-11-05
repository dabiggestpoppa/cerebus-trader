# BOOK III / BLOC III.6 — INTELLIGENCE API & SNAPSHOT SERVICE — PLAN.md

**Bloc:** III.6 · **Book:** III
**Authority:** BA-22 Rung 1 — planning only (no implementation authorized)
**Base head:** `d74f10a503177a7fc6b3f8699c0781102125f6ce`
**Branch:** `forge` · **Mode:** institutional · append-only · evidence-first

**This document does not implement, persist, deploy or expose anything.**
It freezes the design and the acceptance contract for a later authorized
rung. `ACCEPTANCE.md` is authoritative on clause ids, test names and
counts; this file describes intent, ownership and limits.

---

## 1. Frozen requirement inventory (Ch III.6.1–III.6.12)

Read from
`planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(§ `BLOC III.6 — MARKET INTELLIGENCE API & SNAPSHOT SERVICE`).

| Ch | Frozen requirement | Planned contract |
|---|---|---|
| III.6.1 | Snapshot key = instrument, model_id/version, layer, as_of, data cutoff, calculation version | `SnapshotKey` (10 fields; adds clock/session per invariant #1) → `snapshot_id` + `snapshot_hash` |
| III.6.2 | Current state: state, layer, direction/bias where defined, active range/tier, clocks, quality, no-go | `CurrentStatePayload` inside the frozen envelope |
| III.6.3 | Typed levels: measurement, decision, target, invalidation, rekey, promotion, zone; source model/version + active state | `LevelView` over III.2/III.3 `TypedLevel`, kind never inferred |
| III.6.4 | Path: current path, consumed states, first-delivery history, range-left, transition sequence summary | `PathPayload` over III.4 `DeliveryPath`/`TransitionLedger` |
| III.6.5 | Setup context: eligibility facts + canonical setup payload; Book II policy before response | `SetupContextPayload` from `evaluate_setup` + policy gate |
| III.6.6 | Evidence links: Claim/Evidence ids + status; no corpus duplication | `EvidenceLink` (ids + status only) |
| III.6.7 | Historical snapshot/replay with pinned data/model version; unavailable rather than silently current | `HistoricalRequest` → reconstruction or `HISTORICAL_UNAVAILABLE` |
| III.6.8 | Multi-model instrument view composing L3/L2/L1 without a confluence score | `InstrumentView` with three owned sections |
| III.6.9 | Basket view, JPY role-aware, not flattened to an average | `BasketView` with per-pair roles |
| III.6.10 | Stable machine-readable contracts with `schema_version` and `model_version` | `SnapshotEnvelope` + canonical JSON |
| III.6.11 | Cache by snapshot identity; invalidate on new final bar/event, model version, calibration, corrected data, entitlement change | Two-tier cache + policy fingerprint |
| III.6.12 | Use Book II identity/policy/audit; expose no internals | `ForgePolicyEnforcementService.guard` + bounded audit |

**Acceptance III.6 (verbatim, 6 conditions):** deterministic payload per
identity; explicit current/historical distinction; L3/L2/L1 ownership
preserved; evidence/status with statistical claims; policy filters
protected outputs; no monolithic confidence score.

## 2. Exact chapter → contract mapping

| Frozen condition | Clauses | Primary contract | Owner of truth |
|---|---|---|---|
| III.6.1 key/hash | A1–A20 | `SnapshotKey`, `snapshot_id()`, `snapshot_hash()` | III.6 (identity only) |
| III.6.2 current state | B1–B16 | `CurrentStatePayload` | III.3/III.4 |
| III.6.3 levels | C1–C14 | `LevelView` | III.2/III.3 |
| III.6.4 path | D1–D14 | `PathPayload` | III.4 |
| III.6.5 setup | E1–E18 | `SetupContextPayload` | III.5 (+ II.4 policy) |
| III.6.6 evidence | F1–F12 | `EvidenceLink` | Book I corpus |
| III.6.7 history | G1–G16 | `HistoricalRequest`/`Reconstruction` | III.1–III.5 at pinned versions |
| III.6.8 multi-model | H1–H14 | `InstrumentView` | III.3/III.4 per layer |
| III.6.9 basket | I1–I12 | `BasketView` | III.3 JPY role map |
| III.6.10 schemas | J1–J16 | `SnapshotEnvelope`, canonical JSON | III.6 |
| III.6.11 caching | K1–K16 | `SnapshotCache` | III.6 (policy from II.4) |
| III.6.12 security | L1–L18 | `PolicyGate`, `AuditSink` | II.3/II.4/II.6 |
| Acceptance III.6 | M1–M6 | envelope-level drivers | — |
| Invariants #1–#18 | N1–N18 | payload assertions | — |
| Schema discontinuity | O1–O16 | `SCHEMA_INCOMPATIBLE` + ADR | Book I (repair) |
| Freshness/version | P1–P16 | `FreshnessPolicy` | III.1 quality + versions |
| Adversarial | Q1–Q16 | request validators | — |
| Boundaries | R1–R14 | package layout | — |
| Gaps/governance | S1–S14 | gap register §13 | — |
| Final Book III gate | T1–T14 | integration evidence | — |

## 3. Proposed architecture

New package `app/forge/intelligence_api/` — 14 modules. It touches no
ratified file and imports one-way from `market_data`, `measurements`,
`model_runtime`, `state_engine`, `setup_engine`, plus `canonical`,
`schemas`, `policy`, `identity` (read-only).

| Module | Responsibility | Must not |
|---|---|---|
| `__init__.py` | bounded public surface + version | re-export internals |
| `versions.py` | `INTELLIGENCE_API_V1`, `SNAPSHOT_SCHEMA_VERSION` | invent model versions |
| `errors.py` | closed refusal/error vocabulary | carry prose or payloads |
| `contracts.py` | immutable snapshot/request/payload types | hold floats or free text |
| `identity.py` | `SnapshotKey`, id and hash derivation | read a clock |
| `composition.py` | pure composer over III.1–III.5 | recompute any upstream truth |
| `requests.py` | typed request validation, version pinning | substitute `latest` |
| `freshness.py` | quality/version/cutoff semantics | invent a staleness threshold |
| `policy_gate.py` | adapter over II.4 `guard` (deny-before-compose) | decide policy itself |
| `history.py` | reconstruction from retained inputs | replay under current rules |
| `cache.py` | two-tier cache keyed by identity + policy fingerprint | cross principals |
| `serialization.py` | canonical JSON + schema hash | add serve-time timestamps |
| `refusals.py` | bounded outcomes incl. `SCHEMA_INCOMPATIBLE` | leak restricted fields |
| `views.py` | multi-model and basket composition | create confluence/average |

**Transport** is an extension of the existing FORGE router
(`app/forge/service/routes.py`, prefix `/forge/v1`), not a new framework:
`GET /forge/v1/intelligence/{instrument}/{model}/state|levels|path|setup|evidence`,
`GET /forge/v1/intelligence/{instrument}/view|basket`,
`GET /forge/v1/intelligence/{instrument}/{model}/history`. The router
only validates, authorizes, calls the composer and serialises; no
intelligence is computed there.

**Why this shape:** the repository already owns a service skeleton
(II.1), policy enforcement (II.4), observability (II.6) and health
(II.1). Adding a second framework would duplicate authorization and
telemetry paths — a governance defect, not a feature.

## 4. Snapshot field and source ownership

| Field group | Fields | Source (read-only) |
|---|---|---|
| Identity | `snapshot_id`, `snapshot_hash`, `schema_version` | III.6 |
| Instrument/model | `instrument_id`, `model_id`, `model_version`, `layer` | III.1 / III.3 registry |
| Time | `as_of`, `data_cutoff`, `calculation_timestamp`, `source_timestamps` | III.1 bars/clocks (caller-supplied, never wall clock) |
| Clock | `clock_id`, `session_id`, `research_day`, registry versions | III.1 |
| Quality | `quality_state`, flags, `source_window_digest` | III.1 |
| Measurements | `MeasurementRef` tuple (definition id/version/window digest/bar count/quality) | III.2 |
| Model state | `model_state`, `direction_bias`, `sub_states`, `production_authorization`, `no_go`, `warnings` | III.3 |
| Anchors/ranges | `active_ranges`, `active_anchor_states`, `range_left` | III.2/III.3 |
| Levels | typed levels with kind/active/source | III.2/III.3 |
| Path | consumed states, first delivery, transition refs, range-left | III.4 |
| Setup | `SetupContextPayload` (verdict, reasons, gates, card, record) | III.5 |
| Evidence | `claim_refs`, `evidence_refs` + status | Book I corpus |
| Classification | execution class, exposure, research/manual/automation | Book I card, verbatim |
| Explanation | structured `ExplanationFact` tuple | III.3 |
| Provenance | engine versions, registry versions, lineage ids | all Blocs |
| Unresolved | explicit unavailable sections + bounded reasons | III.6 |

Rules: every field is a reference or a verbatim copy; nothing is derived
twice; an unavailable field is `UNAVAILABLE` with a reason, never `[]`
or `null` ambiguity.

## 5. Request / response / error contracts

**Requests** (all frozen, `extra="forbid"`):

- `SnapshotRequest {instrument_id, model_id, model_version, layer, as_of, data_cutoff, surface}`
- `HistoricalRequest {… + pinned model_version + pinned data cutoff + retention acknowledgement}`
- `InstrumentViewRequest {instrument_id, layers: tuple[Layer] (default L3,L2,L1)}`
- `BasketRequest {basket_id: "JPY", pairs: tuple[str,...]}`
- `SetupContextRequest {setup_id, setup_version, surface}`

No request field can select a verdict, exposure, class, or "flatten".

**Response envelope** (single shape, all surfaces):

```
schema_version, snapshot_id, snapshot_hash, view ("CURRENT"|"HISTORICAL"|"UNAVAILABLE"),
identity{...}, time{...}, lineage{...}, quality{...},
sections{state?, levels?, path?, setup?, evidence?},
classifications{execution_class?, exposure?, research_only, manual_only, automation_permitted=false},
provenance{engine_versions{}, registry_versions{}, component_hashes{}},
explanation_facts[], warnings[], unresolved[], refusals[]
```

**Refusal vocabulary (closed, 18):** `UNKNOWN_MODEL`, `UNKNOWN_VERSION`,
`PROVIDER_NOT_CONFIGURED`, `DATA_QUALITY_BLOCKED`, `NONFINAL_BAR`,
`STALE_DATA`, `CLOCK_UNRESOLVED`, `MIXED_CUTOFF`, `VERSION_DRIFT`,
`HISTORICAL_UNAVAILABLE`, `HISTORICAL_NOT_RETAINED`, `SETUP_UNRESOLVED`,
`SCHEMA_INCOMPATIBLE`, `EXPOSURE_FORBIDDEN`, `INSUFFICIENT_EVIDENCE`,
`UNSUPPORTED_STATISTIC`, `NO_GO_ACTIVE`, `MALFORMED_REQUEST`.

`NO_GO_ACTIVE` is a market fact, not an error; `DATA_QUALITY_BLOCKED` /
`PROVIDER_NOT_CONFIGURED` are unavailability. The two are never merged.

**Errors** reuse the existing `ForgeErrorDetail` envelope and codes
(`FORGE_CLIENT_ERROR`, `FORGE_NOT_FOUND`, `FORGE_DEPENDENCY_UNAVAILABLE`,
`FORGE_INTERNAL_ERROR`) — no second error dialect.

## 6. Policy and exposure boundaries

- Authorization is `ForgePolicyEnforcementService.guard(principal,
  context, action, resource, loader)`: **deny ⇒ composer never runs**.
- Exposure class is read from the Book I card and passed as
  `ResourcePolicyMetadata.exposure`; the API never assigns or widens it.
- Research content served to a research-authorized principal keeps
  `RESEARCH_LAB` status and `research_only=true`.
- `INTERNAL_METHOD`/`INTERNAL_CODE` snapshots require `forge.internal`;
  the machine card payload (with internal field detail) is never served
  to customer principals.
- Denials are uniform: same code, same shape, no ids, no existence
  signal. Error text never echoes a resource id or token.
- Audit is the II.4 bounded, content-free record plus the II.6 emitter;
  no new audit store is created (Book II owns it).

## 7. Freshness, quality and version semantics

| Situation | Outcome |
|---|---|
| provider seam `NOT_CONFIGURED` | `PROVIDER_NOT_CONFIGURED`; no live claim |
| nonfinal bar in window | `NONFINAL_BAR` (blocked) |
| stale input | labelled `STALE` + cutoff; served only if a versioned staleness policy allows |
| bad-quality source | `DATA_QUALITY_BLOCKED` with the frozen flag |
| unresolved clock/session | `CLOCK_UNRESOLVED` → `NO_CALCULATION` |
| mixed component cutoffs | `MIXED_CUTOFF` (refused, not reconciled) |
| version drift | `VERSION_DRIFT` |
| unknown version | `UNKNOWN_VERSION` (fail closed) |

**No staleness threshold is invented.** A threshold exists only if a
canonical, versioned policy object supplies it; otherwise staleness is
reported as a labelled fact, never as a pass/fail the API made up
(III.6-GAP-4).

Quality vocabulary is exactly `OK | DEGRADED | DATA_QUALITY_BLOCKED |
NO_CALCULATION` (III.1 `DataOutcome`), flags exactly the eight frozen
`QualityFlag` values.

## 8. Historical reconstruction and cache policy

**Identity layers are separate:** logical snapshot identity
(`snapshot_id`), history lineage (`prior_snapshot_id`, transition refs),
durable storage (none at this Bloc), cache state, transport encoding.

Reconstruction: replay retained III.1 inputs under the **pinned**
III.2/III.3/III.4/III.5 versions; compare to the recorded `snapshot_hash`.
No retained inputs ⇒ `HISTORICAL_UNAVAILABLE`; outside retention ⇒
`HISTORICAL_NOT_RETAINED`. Current rules are never applied to a
historical request.

Cache: two tiers.
1. **Composition cache** — keyed by `snapshot_id`; holds the unfiltered
   canonical snapshot; never served directly; internal only.
2. **Response cache** — keyed by `(snapshot_id, exposure, policy_fingerprint,
   principal_scope)`; served only after a fresh policy decision.

Invalidation: new final bar/event, model version change, calibration
change, corrected data, exposure change. A cache hit never bypasses
policy; a stale entry is never labelled current; entries never cross
principals.

## 9. Canonical Setup Card schema discontinuity — assessment

**Reproduced at this head** (`d74f10a`) against the three canonical
cards; each fails with exactly three validation errors:

| Field | Failure |
|---|---|
| `setup_id` | `invalid canonical id format` — `SETUP.*` does not satisfy `CanonicalId`'s prefix rule (`SET.`) |
| `status` | not in `EvidenceStatus` (`CANONICALIZATION_CANDIDATE`, `RESEARCH_OPERATOR_CANDIDATE`) |
| `parent_model_ids` | `invalid canonical id format` — `XAU.GAME.L1_L2_L3.V1` is not `MODEL.`-prefixed |

Consequences for III.6:

1. The API serves card identity, status and parent ids **verbatim**; it
   never renames, never promotes, never coerces.
2. Operations that require a **machine-valid** card (e.g. a strict card
   DTO endpoint) return the governed refusal `SCHEMA_INCOMPATIBLE`
   (clause O5), with no field leakage.
3. A lossless read-only DTO **is** safe for serving: identity, class,
   exposure, status and claim/evidence ids are strings or enums already
   carried by III.5's `CanonicalSetupCard`; nothing requires the Book I
   model. A green DTO test therefore proves transport fidelity, not
   schema resolution — stated in the acceptance text.
4. **Repair is out of scope.** It requires a separate Book I
   authorization and a new ADR.

**Proposed ADR (future authorization item, not created here):**
`ADR-BOOK-I-001 — Setup Card machine-schema reconciliation`.
Content: (a) context and reproduced failures; (b) option A — widen
`CanonicalId` prefix map to admit `SETUP`; (c) option B — add a `SETUP`
object type plus a card-lifecycle status enum and model-scoped parent id
rule; (d) option C — keep Book I untouched and define a card-corpus
adapter schema owned by III.5; (e) recommendation: **B + adapter**, with
explicit migration of `SET.*` expectations; (f) blast radius (canonical
registry, provenance edges, retrieval objects, QA gates); (g) rollback;
(h) required tests. No option is selected by this packet.

## 10. Proposed executable suite

`tests/test_forge_intelligence_api.py` — **258 tests** in 14 groups
(T1–T14), bound by `ACCEPTANCE.md` §A–§T (300 clauses). Zero skipped,
zero xfailed; every frozen condition has an executed driver. The suite
must include the 16-class adversarial matrix (§Q), the schema
discontinuity drivers (§O), freshness/version drivers (§P) and the
frozen-hash boundary driver (R14).

## 11. Golden fixture design

Directory `implementation/forge/book_iii/bloc_iii_6/fixtures/` with
`_builders.py`, `generate.py`, `README.md`, `FIXTURE_MANIFEST.json`
(LF-normalised SHA-256), `FROZEN_BASELINE.json` (III.1–III.5 module
hashes), and 12 cases:

| # | Case | Expectation |
|---|---|---|
| 1 | consistent synthetic snapshot (EUR L1) | deterministic id/hash, all sections present |
| 2 | model-only snapshot, no eligible setup | `setup` section `UNAVAILABLE` with reason |
| 3 | active stand-down lock | lock preserved; setup `BLOCKED` |
| 4 | missing provider | `PROVIDER_NOT_CONFIGURED`, no live claim |
| 5 | data-quality failure | `DATA_QUALITY_BLOCKED` |
| 6 | research-only Fib | `RESEARCH_ONLY`, production refused |
| 7 | manual JPY | `MANUAL_OPERATOR`, automation refused |
| 8 | XAU WATCH ceiling | `WATCH`, never `ELIGIBLE` |
| 9 | historical model version mismatch | `VERSION_DRIFT` |
| 10 | canonical card schema incompatibility | `SCHEMA_INCOMPATIBLE`, verbatim identity |
| 11 | restricted exposure | denial with no protected fields |
| 12 | deterministic reconstruction | replay reproduces `snapshot_hash` |

Provenance labels: `SYNTHETIC_FIXTURE`, `CANONICAL_SOURCE_SLICE`.
Fixtures reuse III.5 builders and committed III.1–III.4 inputs; none
carries a performance figure. **Fixture reproduction proves determinism,
not market accuracy, historical performance or production readiness.**

## 12. Upstream interface-hash baselines (verified at this head)

| Surface | Count | Aggregate sha256 |
|---|---|---|
| III.1 `market_data` | 11/11 | `c78084bf8d60fb536d8cccda806568f03ba1e625e769b50526ddf3c000901c03` |
| III.2 `measurements` | 12/12 | `1912207e39bd94cee25aae65d108d4f783cc458c81dfb15513f7424cfd631d44` |
| III.3 `model_runtime` | 13/13 | `27ac88c4df446a589b3785a591128b712bb12091bdda8f58c2cf39bfa96c5644` |
| III.4 `state_engine` | 13/13 | `9b89454b6521f6320997ccd4218a934f8fc4f7a4f308684fd652ead3159bb0f5` |
| III.5 `setup_engine` | 16/16 | `0fc19919b5ef74548506a6ea7ebb0c7a475f8af0eae473f73813f7a3e1912a33` |

Aggregate = sha256 over `name + "\n" + bytes` for each module in sorted
order. Re-derived in this session.

Book II contract freeze: **50/50** manifest hashes verified, 0
mismatches. Planning freeze: **23/23** pinned files content-identical
(EOL-normalised). Migrations: `001`–`004` only. `market_data:
NOT_CONFIGURED` unchanged. III.5: RATIFIED — PASS (CLOSED), 162/162 at
this head; CI run `42029671655` success.

## 13. Carried and new gaps

**Carried (unchanged):** III.5-DEFECT-1, III.5-REC-1, III.5-REC-2,
III.5-GAP-1…7, III.4-GAP-1…12, III.3-GAP-1…10, III.2-GAP-1…6,
III.1 GAP-1…5.

**New at III.6:**

| Id | Gap | Blocks |
|---|---|---|
| III.6-GAP-1 | No durable snapshot/history store (inherits III.4-GAP-10, III.5-GAP-6) | exact historical reconstruction beyond retained in-memory inputs; private beta history |
| III.6-GAP-2 | Market-data provider `NOT_CONFIGURED` | any live snapshot; live product |
| III.6-GAP-3 | Setup Card machine schema incompatible (III.5-DEFECT-1) | strict card DTO; machine validation; Book IV card rendering |
| III.6-GAP-4 | No canonical versioned staleness policy | staleness verdicts; only labelled facts |
| III.6-GAP-5 | No canonical confluence/aggregate model | any composite score (deliberately absent) |
| III.6-GAP-6 | No stable Book VI entitlement fingerprint | cross-principal response sharing; cache scoped per principal |
| III.6-GAP-7 | Book IV/V consumer contracts not implemented | handoff verification; end-to-end product |
| III.6-GAP-8 | Transport hardening (TLS, edge auth, rate limits) owned by Book VIII | production deployment |

**No gap closes because a DTO can represent its absence.**

## 14. Stop conditions

Implementation stops and returns to the operator if:

1. a ratified upstream contract must change to serve a payload;
2. the card schema must be coerced (prefix, status, parent id) to pass a
   validator;
3. a staleness threshold, confluence score, probability or performance
   figure would have to be invented;
4. satisfying a clause requires persistence or a migration;
5. policy would have to run after composition to satisfy a test;
6. any upstream gap would have to be quietly marked closed.

## 15. Book III final ratification requirements

III.6 PASS/CLOSED is **not** Book III closure. The final record requires
end-to-end evidence for: observation→snapshot integrity; policy-aware
exposure; cross-model coherence (EUR L3/L2/L1, XAU, BTC, JPY, Fib);
replay consistency; data-quality behaviour; provider-not-configured
behaviour; setup/no-go preservation; consumer contract compatibility; and
an explicit deployment-readiness limitation statement. It must also
record: market-data schema version, clock/session registry versions,
measurement engine version, model runtime versions/hashes, setup registry
version, fixture hashes, test counts and ratification commits.

## 16. Book IV / V handoff contracts

Book IV (Ask CEREBUS) may consume **facts only**: exact model/version,
current state, active ranges/levels, path/range-left, setup eligibility,
no-go, quality, claim/evidence ids with status, transition history. It
must not recompute market state inside the LLM.

Book V may render Book III state/levels/setups but cannot create model
logic, eligibility or exposure decisions in the frontend.

Both consume the same frozen envelope; neither receives a score,
probability or execution instruction, because none exists in the
contract.

---

## 17. Phase 0 verification at this head

| # | Check | Result |
|---|---|---|
| 1 | HEAD == `origin/forge` == `d74f10a…` | PASS |
| 2 | `5fa2502` and `d74f10a` ancestry (append-only) | PASS |
| 3 | Book I corpus + freeze manifest present and untouched | PASS |
| 4 | Book II 50/50 contract hashes | PASS (0 mismatches) |
| 5 | 23/23 planning pins | PASS (content-identical, EOL-normalised) |
| 6 | III.1 11 modules | PASS |
| 7 | III.2 12 modules | PASS |
| 8 | III.3 13 modules | PASS |
| 9 | III.4 13 modules | PASS |
| 10 | III.5 16 modules | PASS |
| 11 | III.5 RATIFIED PASS (CLOSED), 162/162 | PASS |
| 12 | Migrations `[1,2,3,4]` | PASS |
| 13 | `market_data: NOT_CONFIGURED` unchanged | PASS |
| 14 | Service/identity/policy/provenance/health inspected | PASS |
| 15 | Starting-head CI green | PASS (run `42029671655`) |
| 16 | Working tree | only `?? .bu_tmp/` |

**Schema discontinuity reproduction:** all three cards, 3 errors each —
`setup_id` format, `status` vocabulary, `parent_model_ids` format.
Recorded in §9 and carried as III.6-GAP-3 / III.5-DEFECT-1.

## 18. Scope exclusions

No API implementation, router registration, fixtures, tests, migrations,
provider adapters, cache storage, network calls, Book IV/V work,
UI/dashboard, Ask CEREBUS prose, Whop logic, brokerage/order/sizing, or
Book I schema repair is authorized by this rung.

## 19. CI record

| Head | Workflow run | Result |
|---|---|---|
| `d74f10a` — starting head (III.5 ratified) | `42029671655` | success |
| `6d76ea7` — III.6 PLAN + ACCEPTANCE | `42043276253` | success |
| final head — this CI-record commit | recorded by the run following this commit | — |

Local verification at the planning head: 300 clauses, 258 unique test
names, zero clauses without a driver, 50/50 Book II hashes, 23/23
planning pins, III.1–III.5 baselines 11/12/13/13/16, migrations
`001`–`004`, and the three-card schema failure reproduced (3 errors
each). A CI receipt is not a substitute for those checks and does not
authorize implementation.
