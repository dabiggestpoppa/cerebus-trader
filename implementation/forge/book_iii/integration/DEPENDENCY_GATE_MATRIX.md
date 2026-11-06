# BOOK III — DEPENDENCY & RELEASE-GATE MATRIX

**Book:** III · **Packet:** BA-23 Rung 1 (planning + dependency audit)
**Status:** PROPOSED — binding only after an authorized integration rung
**Starting head:** `ecb97ee2f5b8ba7adfd407997be379fee49ffc7d`
**Companions:** `PLAN.md`, `ACCEPTANCE.md`

Open-gap register across III.1–III.6, with ownership, blocked capability,
authorization and beta/production classification. No gap is closed by this
document; every rating below is a planning judgement grounded in the ratified
bloc evidence packs.

---

## 1. Classification key

| Class | Meaning |
|---|---|
| **A** | Blocks deterministic cross-bloc integration testing |
| **B** | Blocks live or historical production data functionality |
| **C** | Blocks a specific model/setup promotion |
| **D** | Blocks external exposure or commercial launch |
| **E** | May remain explicitly deferred without violating frozen launch scope |

Beta = private, invitation-only operational use. Production = paid public launch
under Book VIII GO.

---

## 2. Full open-gap register

### III.1 — Market Data & Clock Contracts

| Gap | Owner | Current restriction | Closure evidence | Blocks | Class | Beta | Prod |
|---|---|---|---|---|---|---|---|
| III.1-GAP-1 no real historical bar slices | Operator / data | synthetic labelled fixtures only | canonical slices + evidence refs | empirical claims, replay over real history | B | yes | yes |
| III.1-GAP-2 session families without canonical definitions | Book I / research | London/MLR, weekly-seed intraday, DT binding, month/quarter frames disclosed missing | canonical definitions per family | those models' sessions | C | partial | yes |
| III.1-GAP-3 final-bar rules beyond M5 | Research | other lineages resolve `NO_CALCULATION` | canonical rule per lineage | those lineages | C | partial | yes |
| III.1-GAP-4 no provider selection/wiring | Operator / Book II | seam `NOT_CONFIGURED` | authorized adapter + parity | any live data | B | yes | yes |
| III.1-GAP-5 live-feed parity unproven | Book III / provider | scripted parity only | live replay parity run | live claims | B | yes | yes |

### III.2 — Measurement & Feature Engine

| Gap | Owner | Current restriction | Closure evidence | Blocks | Class | Beta | Prod |
|---|---|---|---|---|---|---|---|
| III.2-GAP-1 R15 Range Birth rule not materialized | Book I governance | anchor registry empty; `automation_ready=False` | exact rule + canonical source + evidence | Fib production anchors | C | no | yes |
| III.2-GAP-2 JPY tiers partially canonical | Book I research | JPY tier lookup refuses | canonical per-pair tier/AU tables | JPY tier interpretation | C | partial | yes |
| III.2-GAP-3 XAU calibration is spatial bands | Research | no tier table | ratified table if one exists | universal XAU tier claims | C | no | yes |
| III.2-GAP-4 no event calendar | Operator / data | synthetic events only | canonical event slices | real news conditioning | B | yes | yes |
| III.2-GAP-5 fixtures synthetic | Book III | labelled synthetic | canonical slices (with GAP-1) | empirical evidence | E | no | no |
| III.2-GAP-6 HO statistics evidence-bound | Book I / research | referenced by id only | definitions + attachments | numeric destination display | C | partial | yes |

### III.3 — CEREBUS Model Runtime

| Gap | Owner | Current restriction | Closure evidence | Blocks | Class | Beta | Prod |
|---|---|---|---|---|---|---|---|
| III.3-GAP-1 R15 | Book I governance | eligibility requests refuse | materialized rule | Fib production states | C | no | yes |
| III.3-GAP-2 JPY parity | Research / operator | `MANUAL_OPERATOR` | tables + parity approval | JPY automation | C | no | yes |
| III.3-GAP-3 XAU calibration shape | Research | promotions small-N, evidence-linked | ratified table | universal promotion claims | C | no | yes |
| III.3-GAP-4 no event calendar | Operator | synthetic events | canonical slices | real conditioning | B | yes | yes |
| III.3-GAP-5 HO statistics | Book I | evidence ids only | definitions | numerical display | C | partial | yes |
| III.3-GAP-6 no real bars | Operator | synthetic | canonical slices | empirical claims | B | yes | yes |
| III.3-GAP-7 sessions/live parity | Upstream | explicit degradation | upstream decisions | live-feed claims | B | yes | yes |
| III.3-GAP-8 BTC weekly/monthly anchors | Research | `UNRESOLVED` | canonical definitions | BTC weekly/monthly classification | C | partial | yes |
| III.3-GAP-9 XAU parked/quarter-zone doctrine | III.5 | parked flag respected | III.5 materialization | setup eligibility | E | no | no |
| III.3-GAP-10 ST/P90 disclosure | III.5 | re-disclosure only | III.5.9/III.5.10 | representation | E | no | no |

### III.4 — State, Path & Transition Engine

| Gap | Owner | Current restriction | Closure evidence | Blocks | Class | Beta | Prod |
|---|---|---|---|---|---|---|---|
| III.4-GAP-1 R15 | Book I governance | `RANGE_ACTIVE` needs `CANONICAL` | materialized rule | Fib transitions | C | no | yes |
| III.4-GAP-2 JPY parity | Research | role-separated only | tables + approval | JPY automation | C | no | yes |
| III.4-GAP-3 XAU calibration | Research | small-N preserved | ratified table | universal promotion | C | no | yes |
| III.4-GAP-4 event calendar | Operator | no event geometry | canonical slices | conditioning | B | yes | yes |
| III.4-GAP-5 HO statistics | Book I | evidence ids | definitions | numeric stats | C | partial | yes |
| III.4-GAP-6 real bars | Operator | synthetic | canonical slices | empirical claims | B | yes | yes |
| III.4-GAP-7 sessions/parity | Upstream | clock-bound degradation | upstream | live claims | B | yes | yes |
| III.4-GAP-8 BTC remap | Research | `RULE_NOT_MATERIALIZED` | canonical definitions | BTC weekly/monthly | C | partial | yes |
| III.4-GAP-9 XAU parked doctrine | III.5 | parked enforced | III.5 | setup semantics | E | no | no |
| III.4-GAP-10 durable history storage | Book II durability packet | logical contract only | migration + restore drill | cross-session history | A | yes | yes |
| III.4-GAP-11 ST/P90 | III.5 | deferred | III.5 | representation | E | no | no |
| III.4-GAP-12 bar-granularity bound | Book III | refuses intrabar guess | finer granularity if ever | tick-level claims | E | no | no |

### III.5 — Operator Setup Engine

| Gap | Owner | Current restriction | Closure evidence | Blocks | Class | Beta | Prod |
|---|---|---|---|---|---|---|---|
| III.5-GAP-1 quarter-zone mapping uncanonicalised | Book I / research | XAU caps at `WATCH` | canonical mapping binding | XAU `ELIGIBLE` | C | yes | yes |
| III.5-GAP-2 no canonical ST/P90 card | Book I | ST manual, P90 `UNVERIFIED` | canonical cards if promoted | ST/P90 setup identity | E | no | no |
| III.5-GAP-3 XAU ladder invalidation uncanonicalised | Book I / research | declared invalidation, verdict capped | canonical binding | XAU `ELIGIBLE` | C | yes | yes |
| III.5-GAP-4 trigger vocabulary absent upstream | III.2 / operator | matching contract refuses blind touch | governed observation source | end-to-end trigger proof | A | yes | yes |
| III.5-GAP-5 no canonical setup statistics | Research | no numeric result type | `CL.*` claim + population | WR/statistics | C | partial | yes |
| III.5-GAP-6 setup/registry durability | Book II durability | no persistence | migration + drill | durable setup history | A | yes | yes |
| III.5-GAP-7 no live/feed parity | Provider | all lineages `UNVERIFIED` | live parity | automation claims | B | yes | yes |
| III.5-DEFECT-1 card schema incompatibility | Book I governance | 3 machine errors on all cards | separate ADR/schema decision | strict machine-card ops | A | yes | yes |
| III.5-REC-1 `SETUP.*` carried verbatim | Book I | no `SET.*` minted | Book I decision | none (by design) | E | no | no |
| III.5-REC-2 status downward-only projection | Book I | no promotion | Book I decision | none (by design) | E | no | no |

### III.6 — Intelligence API & Snapshot Service

| Gap | Owner | Current restriction | Closure evidence | Blocks | Class | Beta | Prod |
|---|---|---|---|---|---|---|---|
| III.6-GAP-1 no durable snapshot/history store | Book II durability | retained-input replay only | migration + replay verification | cross-session history | A | yes | yes |
| III.6-GAP-2 provider not configured | Operator / Book II | `PROVIDER_NOT_CONFIGURED` | authorized adapter | current-live snapshots | B | yes | yes |
| III.6-GAP-3 Book I card defect | Book I governance | `SCHEMA_INCOMPATIBLE` | ADR decision | strict card projection | A | yes | yes |
| III.6-GAP-4 no versioned staleness threshold | Product / governance | timestamps only, unresolved | versioned staleness policy | stale labelling | B | no | yes |
| III.6-GAP-5 no canonical confluence model | Book I / research | no score emitted | future canonical model | cross-model score | E | no | no |
| III.6-GAP-6 no stable entitlement fingerprint | Book II / VI | recompute or refuse | entitlement identity | cache-safe entitlement reuse | D | yes | yes |
| III.6-GAP-7 Book IV/V consumers absent | Books IV / V | DTO only | consumer implementation | end-to-end product | E | no | no |
| III.6-GAP-8 Book VIII transport hardening incomplete | Book VIII | no deployment | security/launch evidence | external exposure | D | yes | yes |

---

## 3. Ownership summary

| Owner | Gaps | Authorization required |
|---|---|---|
| Book I governance | III.1-GAP-2 (shared), III.5-DEFECT-1, III.5-REC-1/2, III.6-GAP-3, III.2-GAP-1/6 | Book I ADR + operator approval |
| Book II durability | III.4-GAP-10, III.5-GAP-6, III.6-GAP-1 | Book II packet + additive migration |
| Book II route/policy | router registration, III.6-GAP-6 | Book II freeze amendment |
| Provider / operator | III.1-GAP-1/4/5, III.3-GAP-4/6/7, III.6-GAP-2 | provider packet |
| Research | R15, JPY, XAU, BTC, HO stats, ST/P90 | research ratification |
| Book III (integration) | III.5-GAP-4, fixture/lineage proofs | BA-23 R2 |
| Book VIII | III.6-GAP-8 | security/launch packet |

---

## 4. Release gates

### 4.1 Integration gate (WP-1)

Required: 96/96 integration tests, frozen-integrity 50/50 + 79 modules, one
lineage traversal, denial-before-composition, replay hash equality, defect still
open, full regression, CI green.

**A-class gaps do not all block this gate.** III.5-GAP-4 and III.5-DEFECT-1 are
provable as explicit refusal/verbatim paths; durability gaps (III.4-GAP-10,
III.5-GAP-6, III.6-GAP-1) are tested as in-memory retained-input behaviour and
must remain *disclosed*. The gate proves composition, not persistence.

### 4.2 Private-beta gate

Must be closed: provider configured with parity (III.1-GAP-4/5, III.6-GAP-2),
staleness policy (III.6-GAP-4), route registration authorized (Book II),
durability landed and restore-drilled (A-class durability), entitlement identity
(III.6-GAP-6), Book VIII beta security evidence.

May remain open: R15/Fib production, JPY automation, XAU universal promotion,
BTC weekly/monthly, ST/P90, confluence (E/C).

### 4.3 Production launch gate

All B and D gaps closed; C gaps either closed or the affected family explicitly
excluded from the paid surface; Book VIII GO; Book VI entitlement projection
live; legal review complete.

---

## 5. Critical path and parallel work

```
WP-1 integration (must be first)
├── WP-2 route registration ──► WP-7 (Book V UI)
├── WP-3 provider adapter ────► beta data
├── WP-4 durability ──────────► historical surfaces
├── WP-5 Book I ADR ──────────► strict card ops (may run parallel)
├── WP-6 Book IV (after WP-1 DTO) ──► WP-7
├── WP-8 Book VI commerce (parallel)
├── WP-9 Book VII research (parallel)
└── WP-10 Book VIII launch (last)
```

Critical path: **WP-1 → WP-3/WP-4 → WP-2 → WP-6/WP-7 → WP-10**.
Safe parallel: WP-5, WP-8, WP-9 from WP-1; WP-6 from WP-1; WP-3/WP-4 from WP-1.
No packet may start before its upstream contract is frozen.

---

## 6. Book IV/V readiness determination

**Book IV planning and prototype implementation: AUTHORIZED to begin after this
plan is committed**, against the internal `IntelligenceGateway` + III.6 DTO
fixtures only. Rationale: the DTO is frozen by 258 tests, consumers cannot alter
Book III truth, and no production exposure is involved. Book IV must not be
wired to a live route, live data or paid capability until WP-2/WP-3/WP-4 close.

**Book V: MAY prototype against DTO fixtures; production dashboard requires
WP-2 and WP-3.** The UI may render eligibility/exposure verbatim and may not
compute signals.

**Not authorized:** Book IV/V deployment, Book VI implementation outside its own
packet, Book VIII launch, or any production GO.

---

## 7. Stop conditions

Any of the following stops the affected packet: a ratified interface hash
mismatch; a frozen Book I/II contract change; a provider contract that changes
domain semantics; a required source that cannot be located; a destructive
migration without restore proof; a consumer that must recompute Book III truth;
or pressure to represent an open gap as closed.
