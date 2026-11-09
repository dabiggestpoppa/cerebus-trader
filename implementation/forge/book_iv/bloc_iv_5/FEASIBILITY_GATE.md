# BOOK IV / BLOC IV.5 — FEASIBILITY GATE
## BA-30 RUNG 1

**Contract:** `ASK_ANSWER_CONTRACT_V1` (proposed)
**Base HEAD:** `b6018bb1c3923093981ffb4646a7798abf45b922`
**Requirements:** 76
**Classification:** F1=34, F2=35, F3=5, F4=2
**Verdict:** **F1/F2 feasible; F3/F4 open; implementation not authorized by this document alone**

---

## 1. EVIDENCE BASE

| Evidence | Verified result |
|---|---|
| Repository HEAD | `b6018bb1c3923093981ffb4646a7798abf45b922` |
| IV.1 suite | 60 passed |
| IV.2 suite | 72 passed |
| IV.3 suite | 93 passed |
| IV.4 suite | 72 passed |
| Book III integration | 96 passed |
| Five-suite run | 393 passed |
| IV.4 upstream CI at HEAD | run `42530961049` — `test` and `postgres` success |
| Routes | frozen hash `145757e0…d190af` |
| Migrations | `[1,2,3,4]`; unchanged |
| `GatewayDraft` | present; `UNVALIDATED` only |
| Setup eligibility contract | present; four-valued with fixed precedence |
| Market data | `NOT_CONFIGURED` |
| Real provider call | none |
| Network call during planning | none |
| `.bu_tmp/` | preserved |

Planning was source inspection and contract derivation only. No code or network
test was needed or run.

---

## 2. CLASS DEFINITIONS

| Class | Definition | Release meaning |
|---|---|---|
| **F1** | Directly supported now by a frozen contract, type, enum or verified baseline. | Implementable without a new external dependency. |
| **F2** | Deterministic engineering in IV.5 using F1 inputs and local fixtures. | Implementable in Rung 2. |
| **F3** | Requires a later product, operations or ownership decision. | Must be explicitly configured or refused; no silent default. |
| **F4** | Requires absent external infrastructure, policy, entitlement engine or licensing. | Cannot close in IV.5 Rung 2; production gate. |

F3/F4 are **not** waived by a green deterministic test.

---

## 3. REQUIREMENT MATRIX

Owner abbreviations:

- **AC** — IV.5 Answer Compiler/validator owner.
- **V4** — IV.4 gateway owner.
- **V3** — IV.3 context packager owner.
- **B2** — Book II provider/platform owner.
- **SETUP** — setup engine owner.
- **MEAS** — measurement/model-runtime owner.
- **SEC** — security/privacy owner.
- **OPS** — operations owner.
- **PROD** — product/UX owner.
- **B6** — Book VI entitlement owner.
- **EV** — IV.6 evaluation owner.
- **DATA** — corpus/data-governance owner.

### T1 — Input admission and answer authority

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R1 | F1 | AC + V4 | A-01; draft/package/manifest import check; `ASK_GATEWAY_CONTRACT_V1` hash unchanged |
| R2 | F1 | AC | A-02/A-84; identity and status refusal |
| R3 | F1 | AC + V3 | A-03; digest re-verification against `CONTEXT_CONTRACT_V1` |
| R4 | F1 | AC | A-04; no retrieval/provider seam in the module graph |
| R5 | F2 | AC | A-05; presentation-only diff |
| R6 | F2 | AC | A-06/A-82; single-outcome invariant |

### T2 — Beginner compiler

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R7 | F2 | AC + PROD | A-07; `WHAT IT MEANS` |
| R8 | F2 | AC | A-08; `WHAT CEREBUS SEES` |
| R9 | F2 | AC | A-09; limitations/no-go rendered |
| R10 | F2 | AC | A-10; next state or explicit not-encoded |
| R11 | F2 | AC + PROD | A-11/A-81; semantic block stability under heading compression |

### T3 — Operator compiler

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R12 | F2 | AC + MEAS | A-12; cited canonical facts only |
| R13 | F1 | AC + SETUP | A-13; reproduces `SetupEligibility` precedence |
| R14 | F2 | AC + MEAS | A-14; unresolved states explicit |
| R15 | F2 | AC + SETUP | A-15; encoded-only fields |
| R16 | F1 | AC | A-16; no-go preservation |
| R17 | F2 | AC + V3 | A-17; label attachment |

### T4 — Researcher compiler

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R18 | F1 | AC + MEAS | A-18; `AuthorizedEvidenceStatistic` fields |
| R19 | F1 | AC + V3 | A-19; claim/event identity |
| R20 | F1 | AC + V3 | A-20; population/N/small-N rendering |
| R21 | F1 | AC + V3 | A-21; period/generation |
| R22 | F2 | AC + MEAS | A-22; OOS/reproduction |
| R23 | F2 | AC + V3 | A-23; contradiction surfacing |

### T5 — Citation and provenance renderer

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R24 | F2 | AC | A-24; coverage check |
| R25 | F1 | AC + V3 | A-25; package-local resolution |
| R26 | **F3** | PROD + AC | Accepted provenance presentation contract (labels/links allowed per surface); A-26 covers typed rendering only until then |
| R27 | F2 | AC | A-27; deterministic ordering/dedupe |
| R28 | F2 | AC | A-28; citation/link source agreement |
| R29 | F2 | AC | A-29; no fabricated provenance |

### T6 — Numerical validator

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R30 | F2 | AC + V3 | A-30/A-77; normalization law and exact equality |
| R31 | F1 | AC + V4 | A-31; existing `NUMERIC_EVIDENCE_MISSING` path |
| R32 | F2 | AC | A-32; value-changing rounding rejection |
| R33 | F2 | AC + MEAS | A-33; unit/scale rejection |
| R34 | F2 | AC + MEAS | A-34; metric/evidence-class substitution |
| R35 | F1 | AC + V3 | A-35; N/status requirement from `AuthorizedEvidenceStatistic` |
| R36 | F1 | AC + V4 | A-36; draft numeric-link requirement |

### T7 — Layer validator

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R37 | F2 | AC + MEAS | A-37; L3→L1 rejection |
| R38 | F2 | AC + SETUP | A-38; L2 path→setup-WR rejection |
| R39 | **F3** | SETUP + OPS | Accepted, encoded rule that permits an L1 trigger to override a higher-layer no-go; A-39 refuses until that authority exists |
| R40 | F1 | AC + V3 | A-40; label equality and per-claim attribution |
| R41 | F1 | AC + V3 | A-41; frozen vocabulary |

### T8 — Setup and action validator

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R42 | F1 | AC + SETUP | A-42; eligibility-gated action language |
| R43 | F1 | AC + SETUP | A-43; fixed `SETUP_NOT_ENCODED` sentence |
| R44 | F1 | AC + SETUP | A-44; `worst_verdict` precedence |
| R45 | F2 | AC + SETUP | A-45; reason surfacing |
| R46 | F1 | AC + SEC | A-46; advice/sizing/execution prohibition |
| R47 | F1 | AC + SETUP | A-47; encoded-only field values |

### T9 — Status validator

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R48 | F2 | AC + V3 | A-48/A-78; status laundering rejection |
| R49 | F1 | AC + V3 | A-49; parked/superseded/negative preservation |
| R50 | F1 | AC + V3 | A-50; emitted label equals source label |
| R51 | F2 | AC + V3 | A-51; generation preservation |
| R52 | F2 | AC | A-52; no upgrade by confidence/tier/length |

### T10 — Freshness validator

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R53 | **F3** | PROD + MEAS | Accepted definition of "material current-state claim" and the cutoff that must be exposed; A-53 enforces the configured rule only |
| R54 | F2 | AC + MEAS | A-54; stale-as-live rejection |
| R55 | **F3** | PROD + MEAS | Accepted materiality policy for missing freshness; refusal rule depends on it |
| R56 | F1 | AC + MEAS | A-56; `CLOCK_UNRESOLVED` / `DATA_QUALITY_BLOCKED` propagation |

### T11 — Leakage validator

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R57 | F2 | AC + SEC | A-57/A-80; internal-material veto |
| R58 | **F4** | DATA + SEC | Corpus licensing/quote-scope policy and approved reproduction limits; A-58 enforces per-item `quote_scope` only |
| R59 | F2 | AC + SEC | A-59; enumeration veto |
| R60 | F1 | AC + SEC | A-60; system/config/credential veto |
| R61 | F1 | AC + SEC | A-61; untrusted-data boundary |

### T12 — Uncertainty and refusal

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R62 | F1 | AC | A-62; six-code exhaustiveness |
| R63 | **F3** | PROD + AC | Ratified refusal-precedence order; A-63 implements the documented order only |
| R64 | F2 | AC | A-64; no fabrication or hedge-as-answer |
| R65 | F1 | AC + SEC | A-65; safe refusal payload |
| R66 | F2 | AC | A-66; validator-specific code reporting |

### T13 — Final response record

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R67 | F2 | AC | A-67/A-83; deterministic `answer_id` |
| R68 | F1 | AC + V4 | A-68; identity/model/validation codes |
| R69 | F1 | AC + V3 | A-69; cited refs and per-claim labels |
| R70 | F1 | AC + V4 | A-70; latency/cost without secrets |
| R71 | **F4** | SEC + OPS | Approved retention policy (Book VIII) before prose persistence; A-71 enforces metadata-only default |

### T14 — Cross-cutting invariance

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R72 | F1 | AC | A-72; no network/model/retrieval seam |
| R73 | F2 | AC | A-73/A-83; byte determinism |
| R74 | F1 | AC | A-74; frozen hashes/routes/migrations |
| R75 | F1 | AC + SEC | A-75; secret-free payloads |
| R76 | F2 | AC | A-76/A-86; non-bypassable validators and honest reporting |

---

## 4. F3 GATES — OWNER DECISIONS REQUIRED

### F3-1 — R26: citation presentation contract

**Need:** the accepted user-facing provenance surface: which reference fields
are shown, link form, duplication rules and what may never be shown.

**Interim IV.5 law:** render a typed provenance reference derived only from
`source_ref_id`, `source_ref_type`, `provenance_refs`, `evidence_refs` and
`source_status`. Never render an internal ID.

**Closure evidence:** approved presentation contract (owner, field allowlist,
golden rendering corpus) plus A-26 fixtures.

### F3-2 — R39: cross-layer override authority

**Need:** whether any encoded rule permits an L1 trigger to override a
higher-layer no-go, who owns that rule, and how it is versioned.

**Interim IV.5 law:** refuse `LAYER_AUTHORITY_VIOLATION`. No override is assumed.

**Closure evidence:** accepted rule specification with version identity and an
A-39 case matrix.

### F3-3 — R53: current-state materiality and cutoff

**Need:** the definition of a "material" current-state claim and which
`as_of`/cutoff must be shown per model family.

**Interim IV.5 law:** enforce a declared, versioned materiality policy; an
unconfigured policy refuses rather than guessing.

**Closure evidence:** accepted policy ID and A-53 fixture matrix.

### F3-4 — R55: missing-freshness materiality

**Need:** whether a missing freshness basis is always `CURRENT_DATA_UNAVAILABLE`
or whether some model families carry a declared acceptable default.

**Interim IV.5 law:** refuse `CURRENT_DATA_UNAVAILABLE` when the configured
policy requires a basis and none is present.

**Closure evidence:** accepted policy plus A-55 cases.

### F3-5 — R63: refusal precedence ratification

**Need:** product approval of the six-code precedence order and the user-facing
wording for each code.

**Interim IV.5 law:** implement the documented order exactly; report the
prevailing code and record all failing codes.

**Closure evidence:** ratified precedence/wording document and A-63 fixtures.

---

## 5. F4 GATES — EXTERNAL INFRASTRUCTURE REQUIRED

### F4-1 — R58: corpus reproduction/licensing

`quote_scope` exists per item, but no licensing or reproduction policy defines
what a compliant answer may excerpt in aggregate. Bulk reproduction cannot be
declared safe by code alone. Closure requires an approved data-governance
policy and its permitted limits.

### F4-2 — R71: retention policy for prose

No approved fine-grained retention exists. IV.5 stores safe metadata only.
Closure requires a Book VIII retention/security decision covering final prose,
query text and record lifetime.

---

## 6. RISK REGISTER

| Risk | Severity | Mitigation |
|---|---|---|
| Invented number accepted | Critical | Exact value equality; `NUMERIC_*` refusals; Q5-07–Q5-09 |
| Correlation/target/WR laundering | Critical | Metric-substitution validator; Q5-10–Q5-12 |
| Simulation read as empirical | Critical | Evidence-class check; Q5-13 |
| L3/L2 authority masquerading as L1/setup | Critical | Layer validator; Q5-20–Q5-23 |
| Action emitted without eligible setup | Critical | Setup/action validator; Q5-24–Q5-29 |
| Candidate/historical read as current fact | Critical | Status/generation validator; Q5-30–Q5-33 |
| Stale data presented as live | High | Freshness validator; Q5-34–Q5-36 |
| Internal material rendered | Critical | Leakage veto; Q5-37–Q5-39 |
| Refusal converted into invented answer | Critical | Six-code refusal; no-hedge law; Q5-40–Q5-44 |
| Validator bypass via config | Critical | Fixed order; non-bypass requirement; A-76 |
| Non-deterministic answers | High | Deterministic assembly and `answer_id`; A-73 |
| Protected prose persisted | High | Metadata-only default; F4 gate |
| Green suite mistaken for production | High | R76/A-86 and explicit verdict |

---

## 7. VERDICT

**F1/F2:** feasible and ready for Rung 2 implementation planning.
**F3:** five decisions remain; IV.5 must refuse rather than assume.
**F4:** two production gates remain open; no credential, model call or corpus
policy exists.
**Overall:** **CONDITIONAL GO FOR RUNG 2 IMPLEMENTATION ONLY.**
**Production:** **NO-GO** until F4 gates close and IV.6 evaluation ratifies the
launch golden suite.
