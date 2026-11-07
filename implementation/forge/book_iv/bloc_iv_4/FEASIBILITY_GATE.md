# BOOK IV / BLOC IV.4 — FEASIBILITY GATE
## BA-29 RUNG 1

**Contract:** `ASK_GATEWAY_CONTRACT_V1` (proposed)
**Base HEAD:** `a15e0bf89a4192832ae94bf92f3f78f5069ca312`
**Requirements:** 60
**Classification:** F1=18, F2=35, F3=3, F4=4
**Verdict:** **F1/F2 feasible; F3/F4 open; implementation not authorized by this document alone**

---

## 1. EVIDENCE BASE

| Evidence | Verified result |
|---|---|
| Repository HEAD | `a15e0bf89a4192832ae94bf92f3f78f5069ca312` |
| IV.1 suite | 60 passed |
| IV.2 suite | 72 passed |
| IV.3 suite | 93 passed |
| IV.3 golden corpus | 20/20 |
| Book III integration | 96/96 |
| Full repository | 2,303 passed, 29 skipped |
| CI run | `42418069255` — `test` and `postgres` success |
| Routes | frozen hash `145757e0…d190af` |
| Migrations | `[1,2,3,4]`; unchanged |
| OpenRouter adapter | absent |
| LLM credentials | absent |
| Real provider call | none |
| Market data | `NOT_CONFIGURED` |
| `.bu_tmp/` | preserved |

Planning was source inspection and contract derivation only. No code or network
test was needed or run.

---

## 2. CLASS DEFINITIONS

| Class | Definition | Release meaning |
|---|---|---|
| **F1** | Directly supported now by a frozen contract, port, type or verified baseline. | Implementable without a new external dependency. |
| **F2** | Deterministic engineering in IV.4 using F1 inputs and local policy/fixtures. | Implementable in Rung 2. |
| **F3** | Requires a later product/operations decision or a Book VI-style owner. | Must be explicitly configured or refused; no silent default. |
| **F4** | Requires absent external/provider infrastructure, credentials, data-use terms or a real candidate matrix. | Cannot close in IV.4 Rung 2; production gate. |

F3/F4 are **not** waived by a green fake test.

---

## 3. REQUIREMENT MATRIX

Owner abbreviations:

- **GW** — IV.4 Gateway owner.
- **B2** — Book II provider/platform owner.
- **V5** — IV.5 Answer Compiler/validator owner.
- **EV** — IV.6 Evaluation owner.
- **OPS** — Operations/Book VI owner.
- **SEC** — Security/privacy owner.
- **PROV** — Provider integration owner.

### T1 — Provider port compatibility

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R1 | F1 | GW + B2 | A-01; port import check; frozen `llm.py` hash unchanged |
| R2 | F1 | GW | A-02; transport-only request shape |
| R3 | F2 | GW | A-03; capability-mismatch refusal |
| R4 | F1 | GW | A-04; response/usage metadata preserved |
| R5 | F1 | GW + B2 | A-05; frozen error-class mapping |
| R6 | F1 | GW + B2 | A-06/A-71; no vendor import; routes/hash unchanged |

### T2 — Model routing

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R7 | **F3** | GW + OPS | Accepted route catalog/budget policy; A-07 after policy id/config exists |
| R8 | F2 | GW | A-08; bounded unsupported-route refusal |
| R9 | F2 | GW | A-09; model-name independence |
| R10 | F2 | GW | A-10; policy version + determinism |
| R11 | F2 | GW | A-11; route trace fields |
| R12 | F2 | GW | A-12; declared-only fallback list |

### T3 — Versioned prompts

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R13 | F2 | GW + V5 | A-13; three prompt IDs/versions |
| R14 | F2 | GW | A-14; effective-depth selection |
| R15 | F2 | GW | A-15; no hidden evidence store |
| R16 | F2 | GW + SEC | A-16/A-47; trusted/untrusted boundary |
| R17 | F2 | GW + V5 | A-17; separate non-authoritative prompts |
| R18 | **F4** | PROV + GW | Real tokenizer/context-limit evidence for each candidate model; A-18 covers only declarative bounds now |

### T4 — Structured draft

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R19 | F2 | GW + V5 | A-19; frozen schema fields |
| R20 | F2 | GW + V5 | A-20; number/evidence link |
| R21 | F2 | GW + V5 | A-21; package-local citation resolution |
| R22 | F2 | GW + V5 | A-22; no added truth/status/entitlement |
| R23 | F2 | GW + V5 | A-23; no-go/conflict/history preservation |
| R24 | F2 | GW | A-24; malformed-output refusal |

### T5 — Timeouts, retries, cancellation

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R25 | F1 | GW + B2 | A-25; per-attempt and total deadline |
| R26 | F2 | GW | A-26/A-61; retryable/idempotent only |
| R27 | F2 | GW | A-27/A-61; attempt/cost caps |
| R28 | F2 | GW | A-28/A-62; stable retry identity |
| R29 | F1 | GW + B2 | A-29; frozen taxonomy |
| R30 | F2 | GW | A-30/A-63; bounded cancellation |

### T6 — Safe fallback

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R31 | **F3** | GW + OPS | Accepted declared-alternate policy; A-31 after policy authority exists |
| R32 | F2 | GW | A-32; same package/manifest |
| R33 | F2 | GW + SEC | A-33/A-64; no exposure/entitlement widening |
| R34 | F2 | GW | A-34; same prompt/schema |
| R35 | F2 | GW | A-35; attempt/model trace |
| R36 | F2 | GW + V5 | A-36/A-65; fail closed, no masking |

### T7 — Cost/latency controls

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R37 | F1 | GW | A-37; dimensions and counters |
| R38 | F2 | GW | A-38; configurable budgets |
| R39 | F2 | GW | A-39/A-66; pre-call refusal |
| R40 | F1 | GW + SEC | A-40; bounded secret-free aggregates |
| R41 | **F4** | PROV + OPS | Authoritative price source/effective date; A-41 can only mark reported/estimated |
| R42 | **F3** | GW + OPS | Accepted account/feature cost allocation; A-42 covers retry/fallback reconciliation only after that design exists |

### T8 — Privacy/minimization

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R43 | F1 | GW + SEC | A-43/A-67; package-only minimized input |
| R44 | F1 | GW + SEC | A-44; exclusion checks |
| R45 | F1 | GW + SEC | A-45/A-68; no credential path |
| R46 | F2 | GW + SEC | A-46/A-68; redaction tests |
| R47 | F1 | GW + SEC | A-47; trust boundary retained |
| R48 | **F4** | SEC + PROV | Signed retention/no-training terms and region/use approval; A-48 can only require explicit policy/gate |

### T9 — Deterministic fake

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R49 | F1 | GW + EV | A-49; deterministic valid draft |
| R50 | F2 | GW + V5 + EV | A-50; bad-draft scripts |
| R51 | F2 | GW + SEC + EV | A-51; injection script |
| R52 | F2 | GW + B2 | A-52; failure/error scripts |
| R53 | F1 | GW | A-53; fixed usage/cost/latency |
| R54 | F1 | GW | A-54/A-69; provider swap, no domain change |

### T10 — Provider replacement

| Req | Class | Owner | Closure evidence |
|---|---|---|---|
| R55 | **F4** | PROV + EV | Real candidate matrix with recorded capability/cost/results; A-55 only proves the harness is reusable |
| R56 | F2 | GW + B2 | A-56; composition-root selection |
| R57 | F2 | GW + B2 | A-57; adapter-only vendor |
| R58 | F2 | GW | A-58; capability refusal |
| R59 | F1 | GW + B2 | A-59/A-69; port semantics preserved |
| R60 | F1 | GW | A-60/A-72; no production-readiness claim, no network |

---

## 4. F3 GATES — OWNER DECISIONS REQUIRED

### F3-1 — R7: route catalog and budget policy

**Need:** authoritative task/depth -> candidate ordering, latency/cost ceilings,
and the policy owner.

**Interim IV.4 law:** support a versioned policy object; refuse an unspecified
route. Do not encode an implied “best model”.

**Closure evidence:** accepted policy ID, owner, change procedure and A-07
fixture matrix.

### F3-2 — R31: declared alternate policy

**Need:** operations decision on whether fallback is allowed, which models are
authorized alternatives, and how outage recovery is operated.

**Interim IV.4 law:** no alternate unless explicitly declared; no discovery.

**Closure evidence:** approved alternate list and A-31/A-33 fixture evidence.

### F3-3 — R42: account/feature cost allocation

**Need:** mapping of gateway spend to account/feature and parent/child budget
rules for retries/fallback.

**Interim IV.4 law:** per-call accounting is deterministic; no claim of billing
accuracy or customer charge.

**Closure evidence:** allocation design plus A-42 accounting reconciliation.

---

## 5. F4 GATES — EXTERNAL INFRASTRUCTURE REQUIRED

### F4-1 — R18: exact tokenizer/context limits

No provider tokenizer or verified model limit is present. Declarative
conservative bounds may be implemented, but exact accounting cannot be claimed.
Closure requires per-model tokenizer/limit evidence.

### F4-2 — R41: authoritative cost

Provider-reported cost may be absent or approximate. It must be tagged
`reported`/`estimated`; never called billing truth. Closure requires a priced
catalog with effective dates and currency.

### F4-3 — R48: retention/training/security terms

No provider data-use agreement exists. A real request is blocked until
retention, training, region and access terms are approved by the security owner.

### F4-4 — R55: real candidate provider/model matrix

Only deterministic fakes exist. The 72 tests and 24 scenarios are
provider-neutral, but actual candidate evaluation requires credentials and
approved network execution. That is outside Rung 1 and cannot be simulated into
a pass.

---

## 6. RISK REGISTER

| Risk | Severity | Mitigation |
|---|---|---|
| Model output invents a number | Critical | Structured numeric links; IV.5 rejection; Q4-06–Q4-08 |
| Candidate promoted to validated | Critical | Status/layer preservation; IV.5 authority; Q4-11–Q4-14 |
| Prompt injection changes rules | Critical | Trusted/untrusted envelope; no tool access; Q4-17 |
| Fallback re-retrieves broader data | Critical | Same package/manifest; Q4-22 |
| Malformed output parsed loosely | High | Strict schema; no prose fallback; Q4-21 |
| Retry duplicates cost or calls | High | Attempt/cost caps; deterministic accounting |
| Provider receives secret/internal data | Critical | Package-only minimization; redaction; F4 gate |
| Model name becomes authority | High | Model-neutral routing; R9 |
| Fake green misreported as production | High | R60 and explicit feasibility verdict |
| Exact tokens/cost overstated | Medium | F4 markers; no false precision |

---

## 7. VERDICT

**F1/F2:** feasible and ready for Rung 2 implementation planning.
**F3:** three decisions remain; gateway must refuse rather than assume.
**F4:** four production gates remain open; no credential or real call is
authorized.
**Overall:** **CONDITIONAL GO FOR RUNG 2 IMPLEMENTATION ONLY.**
**Production:** **NO-GO** until all F4 gates and IV.5 validation are closed.
