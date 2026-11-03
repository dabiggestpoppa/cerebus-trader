# BOOK III / BLOC III.5 — OPERATOR SETUP ENGINE — PLAN.md

**Bloc:** III.5 (Operator Setup Engine) · **Book:** III
**Authority:** BA-21 Rung 1 — operator-directed planning
**Branch:** `forge` · **Planning head:** `825c24075249f631043b4cc36f479bffeef86532`
**Status:** FROZEN PLANNING PACKET — implementation requires BA-21 Rung 2
**Mode:** Institutional · Append-only · Evidence-first
**Scope:** Bloc III.5 only. III.6 is **not** authorized by this document.

---

## 1. Governing authority model (mandatory, restated)

**Observation → Measurement → Model interpretation → State transition →
Governed setup eligibility.**

Four laws bind every line of this Bloc:

1. **A valid model state is not a valid setup.** A model may be in
   `ROUTE_OPEN` and still produce no setup, a `WATCH`, or a `BLOCKED`
   evaluation.
2. **A valid setup is not an approval for automated execution.**
   Eligibility and authorization are structurally separate fields with
   separate owners.
3. **A successful calculation is not trading authority.** Nothing in
   this Bloc emits an order, size, allocation, account instruction or
   brokerage intent.
4. **A refusal is a first-class result.** `BLOCKED` and `UNRESOLVED` are
   recorded states with bounded reason codes — never exceptions, never
   empty results, never silently-replaced positives.

Downstream may **consume** an upstream fact; it may never **redefine**
it. Book I owns canonical Setup Card identity and status. Book II owns
authorization policy and exposure enforcement. Book III.1–III.4 own
market data, measurement, model interpretation and state/path. III.5
evaluates **runtime setup eligibility** only, and III.6 owns transport.

---

## 2. Scope (frozen chapters, in)

| Ch | Requirement | Planned module |
|---|---|---|
| III.5 common contract | Immutable, versioned setup record with the frozen field set | `contracts.py` |
| III.5.1 | Setup registry: canonical/promoted cards only | `registry.py` |
| III.5.2 | Eligibility engine: state + range/anchor + tier + clock + higher layer + quality + III.4 lock | `eligibility.py` |
| III.5.3 | Trigger semantics: `TOUCH`, `EXCURSION`, `REJECTION`, `ACCEPTANCE`, `CLOSE`, `SR_FLIP`, `OCC` + declared combinations | `triggers.py` |
| III.5.4 | Separate price / structural / temporal invalidation | `invalidation.py` |
| III.5.5 | Ordered targets with canonical promotion conditions | `targets.py` |
| III.5.6 | XAU Quarter-Zone operator (`MANUAL_OPERATOR`) | `xau_quarter_zone.py` |
| III.5.7 | Fib Rekey operator (`RESEARCH_ONLY`) | `fib_rekey.py` |
| III.5.8 | JPY Role-Gated operator (`MANUAL_OPERATOR`) | `jpy_role_gate.py` |
| III.5.9 | Historical / manual ST representation | `st_manual.py` |
| III.5.10 | P90 automation lineage | `p90_lineage.py` |
| III.5.11 | Setup result vs setup statistics | `statistics.py` |
| III.5.12 | Adversarial setup tests | `invariants.py` + suite |
| — | Version stamping, bounded codes, public surface | `versions.py`, `errors.py`, `__init__.py` |

Every chapter is planned, sourced and test-mapped. No chapter is
deferred.

---

## 3. Scope exclusions (out — never in this Bloc)

Brokerage/order routing, position sizing, account or portfolio risk,
personalised advice, live trading, web API/routes, UI/dashboard, LLM
prose generation, Whop/commerce logic, new market-data normalisation, new
measurement formulae, new model interpretation, new state-transition
semantics, new persistence, new migration, provider wiring, background
jobs, caching layer.

III.5 may **read** a III.4 stand-down lock; it may not clear it, relax
it, or re-derive the no-go that produced it.

---

## 4. Phase 0 foundation verification (verified at this head)

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Local HEAD == `origin/forge` == expected `825c240…` | **PASS** | `git rev-parse HEAD` = `git rev-parse origin/forge` = `825c24075249f631043b4cc36f479bffeef86532` |
| 2 | Append-only ancestry (no rewrite) | **PASS** | `merge-base --is-ancestor cff2a59 HEAD` → true; ladder `7ff2385 → be12a61 → 080671a → c6c7f25 → cff2a59 → 825c240` |
| 3 | Book I canonical corpus + Setup Cards + freeze manifest | **PASS** | `corpus/canonical/`, `SETUP_OPERATOR_CARD_SCHEMA_V1.md`, 3 setup cards, `BOOK_I_FREEZE_MANIFEST_V1.md` present and unmodified |
| 4 | Book II 50 frozen hashes + 23 planning pins | **PASS** | 50/50 re-derived, 0 mismatches; 23/23 pins present |
| 5 | III.1 baseline | **PASS** | `app/forge/market_data/` — **11 modules** |
| 6 | III.2 baseline | **PASS** | `app/forge/measurements/` — **12 modules** |
| 7 | III.3 baseline | **PASS** | `app/forge/model_runtime/` — **13 modules**, matches `bloc_iii_3/RATIFICATION.md` §3 |
| 8 | III.4 baseline + PASS/CLOSED | **PASS** | `app/forge/state_engine/` — **13 modules**, hashes match `bloc_iii_4/EVIDENCE.md` §9; `RATIFICATION.md` = `RATIFIED — PASS (CLOSED)` at `cff2a59` |
| 9 | Upstream Python inspected (not summaries) | **PASS** | `canonical.py`, `schemas.py`, `policy.py`, `contract.py`, `anchors.py`, `stand_down.py`, `xau_game.py`, `jpy_carry.py`, `coordinates.py`, `canonicalizer.py` read directly |
| 10 | Migrations `[1,2,3,4]`, no new migration | **PASS** | `app/forge/persistence/sql/{001_initial_schema,002_identity_session,003_vector_projection,004_audit_ledger}.sql`; no `005_*` |
| 11 | `market_data: NOT_CONFIGURED` readiness seam | **PASS** | `service/health.py` frozen non-healthy vocabulary with `required=False` |
| 12 | Starting-head CI | **PASS** | run `41711750320` on `825c240` — `test` + `postgres` success |
| 13 | Pre-existing untracked file preserved | **PASS** | `.bu_tmp/` untouched and untracked |

No branch drift was found; no reconciliation was required.

---

## 5. Dependency, ownership and canonical-source matrix

### 5.1 Upstream contracts consumed read-only (never redefined)

| Source | Symbol | Use in III.5 |
|---|---|---|
| `app.forge.canonical` | `SetupClass` (`MANUAL_OPERATOR`/`AUTOMATION_APPROVED`/`RESEARCH_ONLY`) | the only execution-class vocabulary |
| `app.forge.canonical` | `EvidenceStatus` (14 values) | card status verbatim; gates promotion |
| `app.forge.canonical` | `ProductExposure` (6 values) | exposure carried for Book II, never widened |
| `app.forge.canonical` | `CanonicalId` (`SET.` prefix), `CanonicalObject`, `CanonicalRegistry` | setup identity + content hash |
| `app.forge.schemas` | `SetupOperatorCard` (27 fields) | the canonical card shape loaded by the registry |
| `app.forge.model_runtime` | `ModelOutput` (`model_state`, `layer`, `direction_bias`, `active_ranges`, `active_anchor_states`, `levels`, `range_left`, `no_go`, `warnings`, `quality_state`, `production_authorization`, `explanation_facts`, `sub_states`) | the only model facts a setup may read |
| `app.forge.model_runtime` | `TypedLevel` (`level_kind`, `family`, `level`, `price`, `active`, `source_ref`) | location/zone and target sources |
| `app.forge.model_runtime` | `AnchorStateRef`, `SubState`, `RangeLeftField`, `NoGoReason`, `WarningCode`, `ProductionAuthorization` | anchor status, role/layer sub-states, conditional remaining, no-go codes |
| `app.forge.measurements` | `AnchorEligibility`, `AnchorStatus`, `RuleMaterialization`, `AnchorRefusalCode` | anchor gate (R15 unresolved ⇒ Fib blocked) |
| `app.forge.state_engine` | `StateSnapshot`, `StandDownRecord`, `assert_setup_eligibility_allowed`, `CAPABILITIES_LOCKED`, `DeliveryPath`, `ConditionalRangeLeft`, `DeliveryObservation` | lock enforcement, first-delivery order, conditional range-left |
| `app.forge.policy` | `PolicyAction`, `ProductExposure` matrix, `PolicyDecision` | authorization is *referenced*, never re-implemented |

`model_output` consumption is **read-only by construction**: III.5 will
not subclass `ModelOutput`, will not recompute a measurement, and will
not import a model runtime's private helpers.

### 5.2 Canonical setup source matrix

| Setup id | Source (frozen) | Execution class | Card status | Exposure | Parent model | Evidence refs |
|---|---|---|---|---|---|---|
| `SETUP.XAU.QUARTER_ZONE.V1` | `corpus/canonical/setups/XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md` | `MANUAL_OPERATOR` | `CANONICALIZATION_CANDIDATE` | `OPERATOR_ONLY` | `XAU.GAME.L1_L2_L3.V1` | `EV.XAU.PROMOTION.68_80.V1`, `EV.XAU.PROMOTION.120_132.V1` |
| `SETUP.FIB.REKEY.V1` | `corpus/canonical/setups/FIB_REKEY_OPERATOR_CARD_V1.md` | `RESEARCH_ONLY` | `RESEARCH_OPERATOR_CANDIDATE` | `RESEARCH_LAB` | `CROSSASSET.FIB.RANGE_BIRTH.V1` | `EV.FIB.R11.ANCHOR_OVERGEN.V1` (negative) |
| `SETUP.JPY.CARRY_ROLE_GATE.V1` | `corpus/canonical/setups/JPY_CARRY_ROLE_GATED_OPERATOR_CARD_V1.md` | `MANUAL_OPERATOR` | `CANONICALIZATION_CANDIDATE` | `OPERATOR_ONLY` | `JPY.CARRY_GAME.L1_L3.V1` | `EV.JPY.CARRY.BASKET_RELATION.V1` |
| ST / Tier→AU→Tier | Book I corpus (historical/manual), **no canonical Setup Card exists** | manual framework, **not** a card class | — | — | historical ST lineage | evidence-gated only |
| P90 automation lineage | Book I corpus + `EUR_DAILY_P90_FAILURE_REPAIR` grammar (III.4) | lineage record, **not** an approved automation card | — | — | `EUR.DAILY.NEWS_REKEY.V1@PHASE1` | evidence-gated only |

**Three** canonical setup cards exist. ST and P90 have **no** canonical
Setup Card; III.5 therefore represents them as bounded frameworks and
lineages, and **must not invent a `SETUP.*` identity** for them
(III.5-GAP-2). Claimed setup ids are never fabricated; `SET.` identity
requires a corpus artifact.

### 5.3 Execution-class ≠ eligibility ≠ authorization

| Dimension | Vocabulary | Owner | III.5 behaviour |
|---|---|---|---|
| Execution class | `MANUAL_OPERATOR` / `AUTOMATION_APPROVED` / `RESEARCH_ONLY` | Book I card | carried verbatim; never upgraded |
| Eligibility | `ELIGIBLE` / `WATCH` / `BLOCKED` / `UNRESOLVED` | III.5 runtime | computed per evaluation, never persisted as authority |
| Authorization | Book II `PolicyDecision` + card exposure | Book II | referenced only; III.5 emits no allow/deny of its own |

At this head **no card is `AUTOMATION_APPROVED`**, so
`automation_permitted` is `False` for the entire registry — a property
the suite asserts over the whole registry, not per example.

---

## 6. Existing implementation reuse + interface-integrity baselines

III.5 adds exactly one package and no edits to ratified modules. Reuse is
maximal where the logic already exists:

* anchoring/eligibility vocabulary → III.2 `anchors.py`;
* model state, levels, range-left, no-go → III.3 `contract.py`;
* lift of no-go into a binding lock → III.4 `stand_down.py`;
* ordered path and conditional remaining → III.4 `delivery.py` /
  `range_left.py`;
* canonical ids, card shape, status lifecycle → Book I `canonical.py` /
  `schemas.py`;
* exposure matrix → Book II `policy.py`.

### 6.1 III.1 baseline — 11 modules (verified 11/11)

`app/forge/market_data/` — not modified by this Bloc.

### 6.2 III.2 baseline — 12 modules (verified 12/12)

`app/forge/measurements/` — not modified. `ANCHOR_RULE_REGISTRY` is
**empty** and `AnchorEligibility.automation_ready` is **always False**;
III.5 must not work around either fact.

### 6.3 III.3 baseline — 13 modules (verified 13/13)

`app/forge/model_runtime/` — not modified; hashes match
`bloc_iii_3/RATIFICATION.md` §3.

### 6.4 III.4 baseline — 13 modules (verified 13/13)

`app/forge/state_engine/` — not modified; hashes match
`bloc_iii_4/EVIDENCE.md` §9:

```
__init__.py 6c009b03…aed1fd9 · delivery.py ae912568…bf2c34e5
errors.py 91f14ea7…2ef94d6 · failure_repair.py 776de84f…a4161f
handoff.py b8e404ed…0f0ba1f · history.py acf2b518…daf6f2b25
invariants.py 89148182…ac0d96a6b · range_left.py 61d0789e…e10126af
rekey.py 2a9ac377…1c43aecd7 · snapshot.py 5e6d8c02…15b4c96c7
stand_down.py 31ed18dc…4ca2571d23 · versions.py af648a64…d669499ace
vocabulary.py c5a559d4…8c344752d
```

Any modification of these 36 upstream modules requires its own
authorization and a new recorded hash set.

---

## 7. Proposed design (planning intent — implementation needs its own authorization)

### 7.1 Package layout (new; touches no ratified file)

```
app/forge/setup_engine/
    __init__.py          public surface + version
    versions.py          SETUP_ENGINE_V1, SETUP_CONTRACT_VERSION
    errors.py            bounded refusal codes (no free text)
    contracts.py         immutable setup types + evaluation record
    registry.py          canonical card load, identity/version resolution
    eligibility.py       the eligibility resolver (single authority)
    triggers.py          trigger requirement + observation matching
    invalidation.py      price / structural / temporal trichotomy
    targets.py           ordered targets + promotion conditions
    xau_quarter_zone.py  Ch III.5.6 operator
    fib_rekey.py         Ch III.5.7 research operator
    jpy_role_gate.py     Ch III.5.8 role-gated operator
    st_manual.py         Ch III.5.9 manual framework
    p90_lineage.py       Ch III.5.10 automation lineage
    statistics.py        Ch III.5.11 result/statistics separation
    invariants.py        path/setup assertions used by the suite
```

**16 modules.** Import discipline is one-directional:
`setup_engine → {market_data, measurements, model_runtime, state_engine,
canonical, policy, schemas}`, never the reverse, and no sibling Bloc's
private module. No module in III.5 imports `app.state_engine` (legacy),
`app.forge.service`, `app.forge.providers` or any I/O surface.

### 7.2 Setup contract (frozen field set for the future implementation)

`SetupRecord` (immutable, `setup_contract_version` stamped):

| Field | Type | Rule |
|---|---|---|
| `setup_id` | canonical `SET.*` | must resolve in the registry; never synthesised |
| `setup_version` | str | card version verbatim |
| `source_card_ref` | str | corpus path of the card |
| `execution_class` | `SetupClass` | verbatim |
| `product_exposure` | `ProductExposure` | verbatim |
| `eligibility` | `SetupEligibility` | computed |
| `eligibility_reasons` | tuple of bounded codes | non-empty unless `ELIGIBLE`/`WATCH` |
| `side` | typed side or explicit `NONE_DECLARED` | only where the card declares a direction |
| `location` | typed zone/level ref or `UNRESOLVED` | from a III.2/III.3 typed level |
| `trigger_requirement` | `TriggerRequirement` | declared combination only |
| `invalidation_price` | `PriceInvalidation` or `UNRESOLVED` | separate |
| `invalidation_structural` | `StructuralInvalidation` or `UNRESOLVED` | separate |
| `invalidation_temporal` | `TemporalInvalidation` or `UNRESOLVED` | separate |
| `targets` | ordered `SetupTarget` tuple | order is canonical, never sorted |
| `promotion_conditions` | tuple of `PromotionCondition` | per target |
| `no_go_refs` | tuple of III.3 `NoGoReason` | verbatim |
| `parent_states` | tuple of `ParentStateRef` (model id, version, state, layer, snapshot hash) | verbatim |
| `transition_refs` | tuple of III.4 event/history refs | verbatim |
| `evidence_refs` | tuple of `CL.*`/`EV.*` with status | never a bare number |
| `manual_status` | `MANUAL_OPERATOR`/`RESEARCH_ONLY`/`AUTOMATION_APPROVED` projection | derived, never upgraded |
| `automation_permitted` | bool | `False` unless every automation gate passes |
| `explanation_facts` | tuple of III.3 `ExplanationFact` | structured, never prose |
| `evaluation_hash` | sha256 | over the canonical payload |

No field exists for probability, confidence, confluence, win rate,
expectancy, risk/reward, position size or order intent. The suite asserts
the **absence** of those names, not merely their unusedness.

### 7.3 Eligibility resolution order (single authority, fail-closed)

Resolution is an ordered gate chain; the **first** affirmative refusal
wins and is recorded, and no later gate may override it:

1. **Registry gate** — card resolvable, version bound, status permitted
   for the requested surface. Unknown/quarantined/`PARKED`/
   `IMPLEMENTATION_NOT_PARITY_SAFE` ⇒ `BLOCKED`; unresolvable id ⇒
   `UNRESOLVED`.
2. **III.4 lock gate** — `assert_setup_eligibility_allowed(stand_down)`
   is invoked first-class; any active lock ⇒ `BLOCKED` with the lock's
   bounded reason. A lock is never downgraded to a warning.
3. **Model-state gate** — parent `ModelOutput` present, version-matched,
   layer-correct, and in a state the card declares. Missing/`UNRESOLVED`
   state ⇒ `UNRESOLVED`; wrong layer or a state the card forbids ⇒
   `BLOCKED`.
4. **Anchor gate** — for anchor-dependent setups, III.2
   `AnchorEligibility.status` must be `ELIGIBLE`/`ACTIVE` with
   `rule_materialization = CANONICAL`. `UNRESOLVED`/`INVALIDATED` ⇒
   `BLOCKED`; `DECLARED`/`NOT_MATERIALIZED` ⇒ `UNRESOLVED` (R15).
5. **Tier gate** — the tier must be asset-native, declared by the model
   generation, and not a no-go tier. Cross-asset tier reuse ⇒ `BLOCKED`.
6. **Clock/session gate** — the required session/checkpoint must be
   resolved and reached (e.g. XAU after-03:00 context). Unresolved clock
   ⇒ `UNRESOLVED`; not reached ⇒ `WATCH` (armed, not entered).
7. **Higher-layer gate** — L3/L2 context must not be in explicit no-go or
   stand-down, and must not *substitute* for L1. Conflict ⇒ `BLOCKED`
   with conflict facts; never a confluence score.
8. **Data-quality gate** — `DataOutcome` must be acceptable for the
   model's declared policy. `NONFINAL`/`STALE`/`GAP` ⇒ `BLOCKED` with
   `DATA_QUALITY_BLOCKED`; never a silent recompute.
9. **Parameter-materialisation gate** — every numeric parameter the card
   uses (zone offsets, ladder invalidation, tolerance) must be
   `CANONICAL`; `DECLARED` caps the verdict at `WATCH`; absent ⇒
   `UNRESOLVED`. This is the honest treatment of "exact active
   invalidation must come from current setup implementation".
10. **Trigger gate** — the declared trigger requirement must be satisfied
    by observed path facts. Satisfied ⇒ `ELIGIBLE` (if gates 1–9 pass and
    no invalidation fired); not satisfied ⇒ `WATCH`.
11. **Invalidation gate** — an active price/structural/temporal
    invalidation ⇒ `BLOCKED` (`SETUP_INVALIDATED`), and it dominates a
    satisfied trigger.

Precedence is total and documented: `BLOCKED` > `UNRESOLVED` > `WATCH` >
`ELIGIBLE`. `ELIGIBLE` is therefore reachable **only** when every gate
passes affirmatively.

### 7.4 Trigger semantics

Exactly seven types: `TOUCH`, `EXCURSION`, `REJECTION`, `ACCEPTANCE`,
`CLOSE`, `SR_FLIP`, `OCC`.

`TriggerRequirement` holds an ordered tuple of `TriggerLiteral`
(`type`, optional tolerance, optional bar ref) plus an explicit
`combination` (`ALL` or `ANY`) — the card's declared combination, never
inferred. Structural rules:

* a `TOUCH` observation satisfies **only** `TOUCH`;
* `CLOSE` requires a final bar close beyond the level, per the model's
  clock; a nonfinal bar can never satisfy it;
* `ACCEPTANCE` requires the III.4 acceptance state, not proximity;
* `REJECTION` requires an excursion **followed by** a return, in that
  order, on the recorded path;
* `SR_FLIP` requires a declared flip fact, not a retest;
* `OCC` requires the declared occurrence fact (132-touch + OCC recovery
  lineage in `measurements/coordinates.py` is the only current source).

No trigger type may be promoted into another; there is no
"close-or-touch" fallback anywhere.

### 7.5 Invalidation trichotomy

Three independent typed records, each carrying its own value/source:

* `PriceInvalidation` — a typed level or native magnitude with source;
* `StructuralInvalidation` — the model/state condition that voids the setup;
* `TemporalInvalidation` — session/checkpoint/expiry bound.

Rules: an absent kind is `UNRESOLVED`, never substituted by another kind;
a price invalidation never stands in for a temporal expiry; and until a
card's exact ladder invalidation is canonically materialised, the price
invalidation is `DECLARED` and the verdict caps at `WATCH`.

### 7.6 Targets and promotions

Ordered `SetupTarget` tuple preserving the card's canonical order
(primary doctrine before confirmation states). Each target carries a
`PromotionCondition` (which transition/observation promotes it), a
canonical source ref and an `active` flag. A deeper coordinate is **never**
auto-active: promotion requires its declared condition, and III.4's
first-delivery order + conditional range-left are consumed verbatim.
`target_order()` in III.4 is the ordering authority; III.5 never re-sorts.

### 7.7 Statistics separation

`statistics.py` exposes `EvidenceReference(claim_id, evidence_id, status,
population_key)` and **no numeric result type**. Attaching a numeric
performance figure requires a `CL.*` id whose `ClaimIdentity` matches the
population being described; otherwise `UNSUPPORTED_STATISTIC` refuses.
Relationship evidence (e.g. JPY basket role agreement 115/168 and
EURJPY confirmation 103/115) may be quoted **only** as a state
relationship with its evidence id and `VALIDATED_RELATIONSHIP` status —
never as setup win rate. Historical P90 performance stays `HISTORICAL`
and never becomes current.

### 7.8 Cross-cutting rules

* Injected `evaluation_time`; no wall clock, no `datetime.now()`.
* Decimal only — no float anywhere in payloads or arithmetic.
* Deterministic canonical serialization + `evaluation_hash`; two runs and
  both platforms must agree.
* Bounded codes only; a free-text field would be a contract violation.
* `explanation_facts` are III.3 `ExplanationFact` objects — ordered,
  bounded, prose-impossible.
* Fail closed on unknown enum, unknown version, unknown card, unknown
  surface.

---

## 8. Operator families (Ch III.5.6–III.5.10)

### 8.1 XAU Quarter-Zone — `SETUP.XAU.QUARTER_ZONE.V1` (`MANUAL_OPERATOR`)

Requirements from the card: after-03:00 NY context; active Asian range and
local direction; active quarter zone; excursion **into** the quarter
+10…+15 (bearish) / −10…−15 (bullish) zone; push/rejection back with a
5-minute close outside the zone **or** a valid S/R flip as confirmation;
next-quarter doctrine as the primary target (~25 points or the next
quarter discount/premium zone with source tolerance); invalidation from
the active implementation (≈5-point ladder step historically; 80-family
structural coordinate).

Planned behaviour: `BLOCKED` on blind touch, on L3-destination-only
entry, on parked/no-go context, and on `132→168` promotion assumptions;
`WATCH` at most while the zone mapping and ladder invalidation are
`DECLARED` rather than `CANONICAL`; `ELIGIBLE` only with a canonically
versioned quarter mapping and invalidation (III.5-GAP-1). Targets are
ordered next-quarter first; $5/$10 moves are explicitly confirmation/
evidence states, never the core doctrine.

### 8.2 Fib Rekey — `SETUP.FIB.REKEY.V1` (`RESEARCH_ONLY`)

Requirements: a valid active A–B Range Birth; identified
Alpha/Beta/Gamma/Delta family; asset-native calibration and clock active;
no arbitrary local pivot. 132% is the primary rekey location; 168% is
historical dual-entry research; 50–72% is a **separate** family that must
not be conflated. Invalidation/targets: 132→168 invalidation, midpoint/−25
targets; 168→185; −25 conditional on rekey triggering first.

Planned behaviour: `RESEARCH_ONLY` is preserved end to end; production
surface requests are `BLOCKED` (`RESEARCH_ONLY_NOT_PRODUCTION`); with R15
unmaterialised the anchor gate yields `UNRESOLVED`; the 132/168/185
lineage may be **explained** as bounded facts; no generic-pivot fallback,
no invented anchor, no automated signal. R11 frequency is never
transferred into R15.

### 8.3 JPY Role-Gated — `SETUP.JPY.CARRY_ROLE_GATE.V1` (`MANUAL_OPERATOR`)

Requirements: resolve USDJPY `CARRY_MASTER`, AUDJPY `RISK_EXPRESSION`,
EURJPY `CONFIRMATION_VETO`; primary agreement is USDJPY + AUDJPY; EURJPY
strengthens but is **not** an entry trigger; the executed pair must have
its own native tier and no-go state; local setup comes from that pair's L1
geometry.

Planned behaviour: role map consumed verbatim from
`model_runtime/jpy_carry.py` `ROLE_MAP`; equal-vote aggregation is
impossible by construction (no aggregate field exists); confirmation can
never be the entry; a pair in native-tier no-go is `BLOCKED`; `MANUAL_OPERATOR`
is preserved until parity approval.

### 8.4 Historical / manual ST (`MANUAL_HISTORICAL_FRAMEWORK`)

ST/Tier→AU→Tier is represented as a valid **manual** operator framework:
inputs, tier→AU mapping references and explanation facts, with
`automation_permitted = False` and `perception_gap = UNRESOLVED`. No
autonomous ST execution is approved, and no `SETUP.*` id is created
(III.5-GAP-2). The suite asserts the framework can be explained and can
never be requested as automation.

### 8.5 P90 automation lineage (`AutomationLineage`)

`AutomationLineage(version, implementation_ref, parity_status,
evidence_refs, status)` where `status ∈ {VERIFIED, UNVERIFIED,
HISTORICAL_ONLY}`. `automation_permitted` may be `True` only when status
is `VERIFIED`, parity is established, the version identity is bound, and
the card is `AUTOMATION_APPROVED`. At this head status is `UNVERIFIED` for
every lineage, so the whole surface stays manual/research. Historical P90
performance claims remain `HISTORICAL` and cannot be restated as current
verified performance.

---

## 9. Proposed executable test matrix (summary; full map in `ACCEPTANCE.md`)

`tests/test_forge_setup_engine.py`, **12 groups, 162 tests**:

| Group | Chapter(s) | Tests |
|---|---|---|
| T1 Setup contract + registry | common contract, III.5.1 | 16 |
| T2 Eligibility engine | III.5.2 | 18 |
| T3 Trigger semantics | III.5.3 | 14 |
| T4 Invalidation | III.5.4 | 10 |
| T5 Targets/promotions | III.5.5 | 12 |
| T6 XAU Quarter-Zone | III.5.6 | 14 |
| T7 Fib Rekey | III.5.7 | 12 |
| T8 JPY Role-Gated | III.5.8 | 14 |
| T9 ST manual + P90 lineage | III.5.9, III.5.10 | 12 |
| T10 Setup result vs statistics | III.5.11 | 10 |
| T11 Adversarial setup matrix | III.5.12 | 16 |
| T12 Boundaries, frozen integrity, security | Book III gate, §3 | 14 |

The suite must **refuse** rather than produce positive eligibility in
every adversarial case, and must prove absence (not merely disuse) of
probability/automation/order fields.

---

## 10. Golden fixture program (proposed; fixtures are NOT created in this rung)

### 10.1 Proposed fixture set (12 + manifest)

`implementation/forge/book_iii/bloc_iii_5/fixtures/`:
`setup_registry_cases.json` (`BLOC_III_5.SETUP_REGISTRY.V1`),
`setup_contract_cases.json`, `eligibility_cases.json`,
`trigger_cases.json`, `invalidation_cases.json`,
`target_promotion_cases.json`, `xau_quarter_zone_cases.json`,
`fib_rekey_cases.json`, `jpy_role_gate_cases.json`,
`st_p90_cases.json`, `statistics_cases.json`,
`setup_authority_matrix.json`, plus `FIXTURE_MANIFEST.json` (LF-normalized
sha256) and a provenance `README.md`. Built by shared `_builders.py` that
the suite also uses, so fixtures cannot drift from reproduction.

### 10.2 Required adversarial classes (all 15 from the authorization)

touch without required rejection · valid trigger under a no-go lock ·
L3 direction without L1 eligibility · unresolved R15 requested as
production · JPY equal-vote/automation request · ST automation request ·
unsupported P90 performance claim · stale/nonfinal data · wrong asset
tier · parked XAU setup · missing Setup Card · historical/current version
drift · unauthorized target promotion · ambiguous intrabar first
delivery · model state serialised as a trade signal. (The authorization
lists 14 bullet lines; the list above carries 15 distinct classes because
"no-go lock" and "parked" are separate states.)

### 10.3 Provenance honesty

`SYNTHETIC_FIXTURE` for all card instances, model outputs, snapshots and
observations; `CANONICAL_SOURCE_SLICE` for card identity/execution class/
status/exposure, the seven trigger names, the evidence ids and their
statuses. Fixtures carry **no** win rate, expectancy, probability or
risk/reward figure, and no fixture may be cited as empirical evidence.

---

## 11. Failure and security matrix

| Condition | Required result |
|---|---|
| Card unknown / id unresolvable | `UNRESOLVED` (`SETUP_CARD_UNRESOLVED`) |
| Card `PARKED` / `IMPLEMENTATION_NOT_PARITY_SAFE` | `BLOCKED` (`SETUP_NOT_CANONICAL_FOR_SURFACE`) |
| Research-only card requested as production | `BLOCKED` (`RESEARCH_ONLY_NOT_PRODUCTION`) |
| Active III.4 stand-down lock | `BLOCKED`, reason from the lock |
| Model state missing / version mismatch | `UNRESOLVED` (`MODEL_VERSION_UNAVAILABLE` / `PARENT_STATE_MISSING`) |
| Anchor unresolved / R15 unmaterialised | `UNRESOLVED` (`ANCHOR_UNRESOLVED`) |
| Cross-asset tier used | `BLOCKED` (`TIER_NOT_NATIVE`) |
| Data `NONFINAL`/`STALE`/`GAP` | `BLOCKED` (`DATA_QUALITY_BLOCKED`) |
| Trigger unsatisfied | `WATCH` (`TRIGGER_NOT_SATISFIED`) |
| Invalidation fired | `BLOCKED` (`SETUP_INVALIDATED`) |
| Automation requested on manual/research card | `BLOCKED` (`AUTOMATION_NOT_APPROVED`) |
| Numeric statistic without `CL.*` | refusal (`UNSUPPORTED_STATISTIC`) |
| Unknown enum / unknown version anywhere | fail closed |

Security/boundaries: no network, no file I/O, no wall clock, no provider
import, no composition root, no API route, no secret, no migration, no
write to corpus or ledger.

---

## 12. Known gaps and stop conditions

### 12.1 New gaps (this Bloc)

| Gap | Statement | Consequence |
|---|---|---|
| III.5-GAP-1 | Quarter-zone numeric mapping (±10/±15, quarter boundaries) is not materialised as a canonical geometric rule | XAU caps at `WATCH`; `ELIGIBLE` requires a versioned canonical mapping |
| III.5-GAP-2 | ST and P90 have **no** canonical Setup Card | represented as framework/lineage only; no `SET.*` id invented |
| III.5-GAP-3 | XAU ladder/structural invalidation is "from the active implementation", not canonicalised numerically | price invalidation `DECLARED`; verdict capped |
| III.5-GAP-4 | Trigger observation vocabulary (`EXCURSION`, `REJECTION`, `SR_FLIP`, `OCC`) is not yet a measurement-layer output | III.5 defines the matching contract; observations must be supplied by a governed source |
| III.5-GAP-5 | No canonical setup statistics exist (no `CL.*` for setup WR) | `statistics.py` can only reference evidence; no result numbers |
| III.5-GAP-6 | Setup eligibility durability/registry snapshot storage undecided (inherits III.4-GAP-10) | no migration, no persistence |
| III.5-GAP-7 | No live/feed parity for any operator class | automation stays `UNVERIFIED` |

### 12.2 Carried gaps (open, disclosed)

III.4-GAP-1…12 (notably GAP-10 durable history, GAP-11 ST/P90
representation, GAP-12 intrabar ordering), III.3-GAP-1…10,
III.2-GAP-1…6 (R15 anchor rule), III.1 GAP-1…5, plus R15 Range Birth
production eligibility, JPY manual parity, BTC weekly/monthly anchors,
XAU small-N promotions, missing historical slices, provider wiring.

### 12.3 Stop conditions (report, do not improvise)

1. Any required canonical Setup Card missing, contradictory or
   non-canonical in a way that would require inventing identity or
   parameters.
2. A needed upstream contract absent or ambiguous (trigger observation
   source, quarter mapping) beyond a bounded gap entry.
3. Any expectation to clear or bypass a III.4 eligibility lock.
4. Any request to emit automation approval, orders, sizing or advice.
5. Any need to modify a ratified upstream module or add a migration.
6. Any need for network, provider, clock or filesystem access.

On a stop condition: record it, keep the surface `UNRESOLVED`/`BLOCKED`,
and escalate to the operator.

---

## 13. Acceptance / ratification requirements (this Bloc)

A future III.5 ratification requires, at minimum:

* the frozen clause map executed with **no** weakened, skipped or xfailed
  test;
* every production/operator emission traceable to a canonical Setup Card;
* the whole registry proven to contain no `AUTOMATION_APPROVED` reachable
  state at this head;
* the four-way eligibility vocabulary proven total and fail-closed;
* the trigger downgrade matrix (touch ≠ close ≠ acceptance ≠ rejection)
  proven structurally;
* the invalidation trichotomy proven non-substitutable;
* statistics proven numeric-free without a `CL.*` id;
* `EVIDENCE.md` + `RATIFICATION.md` with root-cause repair history and
  the new module-hash baseline;
* Book III gate §Setups drivers satisfied verbatim;
* CI green at the ratifying head.

---

## 14. Handoffs

### 14.1 To III.6 (Intelligence API & Snapshot Service)

III.6 may assume III.5 returns facts, not prose:

* `setup_id` + `setup_version` + `evaluation_hash`;
* `eligibility` + bounded `eligibility_reasons`;
* typed location, trigger requirement, three invalidations, ordered
  targets, promotion conditions;
* `manual_status` and `automation_permitted` (expected `False`);
* parent states/snapshots, transition refs, evidence refs with status;
* ordered explanation facts.

III.6 must apply Book II policy **before** release, must not fabricate a
confluence score, and must keep `current` vs `historical` explicit. A
setup-context endpoint may render an `UNRESOLVED`/`BLOCKED` evaluation —
it may never upgrade one.

### 14.2 To the operator

Two decisions remain open and are **not** resolved by this packet:
(III.5-GAP-1/3) materialise the XAU quarter mapping and ladder
invalidation canonically; and (III.5-GAP-6, with III.4-GAP-10) decide
whether setup/transition history becomes durable storage. Until then the
XAU operator is `WATCH`-capped and Fib stays `RESEARCH_ONLY`.

### 14.3 Non-authorization

This document authorizes **planning only**. It does not authorize
implementing `app/forge/setup_engine/`, creating fixtures, writing the
suite, publishing an API, or beginning III.6.
