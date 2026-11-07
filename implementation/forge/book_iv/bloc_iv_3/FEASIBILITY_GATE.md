# BOOK IV / BLOC IV.3 — FEASIBILITY GATE
## CONTEXT PACKAGER — BA-28 RUNG 1

**Base HEAD:** `23b2b9e19f1b1dee59c4aa9379a35a1dfed981b7`
**Contract:** `CONTEXT_CONTRACT_V1` (proposed)
**Status:** Pre-implementation gate

This gate classifies all 92 requirements before IV.3 implementation. It does not
close any upstream gap.

---

## 1. CLASSIFICATION

| Class | Meaning | Count |
|---|---|---:|
| **F1** | Directly supported by existing IV.1/IV.2 or frozen Book I/II/III contracts | 22 |
| **F2** | Deterministic IV.3 packaging logic over those contracts | 65 |
| **F3** | Later IV.4/IV.5/IV.6 or Book VII responsibility | 2 |
| **F4** | Missing authoritative source or operational dependency | 3 |
| **Total** | | **92** |

No requirement is infeasible. F3/F4 requirements are represented by a frozen
bounded state or optional already-authorized projection; they are never closed
with synthetic authority.

---

## 2. PER-GROUP CLASSIFICATION

| Group | Requirements | F1 | F2 | F3 | F4 |
|---|---|---:|---:|---:|---:|
| T1 context sections | R1–R9 | 5 | 3 | 1 | 0 |
| T2 canonical compression | R10–R16 | 0 | 7 | 0 | 0 |
| T3 token budgets | R17–R24 | 0 | 7 | 0 | 1 |
| T4 epistemic labels | R25–R33 | 1 | 7 | 1 | 0 |
| T5 layer ownership | R34–R40 | 3 | 4 | 0 | 0 |
| T6 small-N/evidence | R41–R49 | 4 | 3 | 0 | 2 |
| T7 no-evidence path | R50–R55 | 0 | 6 | 0 | 0 |
| T8 injection resistance | R56–R63 | 0 | 8 | 0 | 0 |
| T9 exposure minimization | R64–R71 | 2 | 6 | 0 | 0 |
| T10 context manifest | R72–R79 | 1 | 7 | 0 | 0 |
| T11 failure/refusal | R80–R86 | 0 | 7 | 0 | 0 |
| T12 frozen integrity | R87–R92 | 6 | 0 | 0 | 0 |
| **Total** | **92** | **22** | **65** | **2** | **3** |

### 2.1 F1 requirements (22)

`R2`, `R3`, `R4`, `R5`, `R6`, `R26`, `R34`, `R37`, `R38`, `R45`, `R46`,
`R47`, `R48`, `R64`, `R65`, `R72`, `R87`, `R88`, `R89`, `R90`, `R91`, `R92`.

These use actual plan fields, bundle/ref fields, statuses, layers, provenance,
OOS state, exposure vocabulary, contract hashes or frozen route/migration
checks.

### 2.2 F2 requirements (65)

All remaining requirements not listed in §2.1, §2.3 or §2.4. They require
deterministic section selection, compression, ordering, budgeting, labels,
trust separation, omission accounting, serialization, refusals or tests over
existing contracts.

### 2.3 F3 requirements (2)

| ID | Requirement | Why later | Owner | Closure evidence |
|---|---|---|---|---|
| R9 | General-knowledge allowance | IV.3 may declare a bounded allowance, but external/general knowledge authority and answer use belong to the later model/answer path | IV.4 / IV.5 / Book VII | Authorized general-knowledge policy and answer-layer tests |
| R31 | `INFERENCE` label reserved | IV.3 performs no inference; inference labeling and admission belong to the later answer compiler/validator | IV.5 | Inference policy, provenance and validator tests |

In this rung, R9 is satisfied by a control-only allowance marker with no
CEREBUS facts; R31 is satisfied by proving IV.3 never emits `INFERENCE`.

### 2.4 F4 requirements (3)

| ID | Requirement | Missing condition | Owner | Closure evidence |
|---|---|---|---|---|
| R18 | Replaceable tokenizer port / no accuracy claim | No authorized provider tokenizer or billing-accurate tokenizer contract exists | Book VII / provider integration | Versioned tokenizer adapter, model-specific conformance evidence and cost/accounting tests |
| R41 | Governed metric/population/sample/period | `EvidenceRef` does not carry complete statistical bodies and several canonical claims lack all fields | Book I corpus / Book VII | Authoritative statistical fields on canonical evidence and a governed detail projection |
| R43 | Governed small-N threshold | No authoritative small-N policy or threshold is present | Book I research / Book VII | Ratified threshold policy with population/event scope and versioned reference |

R18 is implemented in IV.3 Rung 2 as a deterministic estimator plus a
replaceable port; provider accuracy remains unclosed.

R41/R43 are implemented as optional `AuthorizedEvidenceStatistic` pass-through
plus explicit unresolved states. No N or threshold is synthesized.

---

## 3. GLOBAL DEPENDENCIES (NOT REQUIREMENT-LEVEL F4)

These can keep production gates open but do not make the deterministic IV.3
contract infeasible:

| Dependency | Current condition | IV.3 behavior |
|---|---|---|
| Current market provider | `market_data: NOT_CONFIGURED` | Preserve `PROVIDER_NOT_CONFIGURED`; no current values |
| Durable historical snapshots | absent | Preserve `HISTORICAL_UNAVAILABLE`; no substitution |
| Book VI entitlement projection | absent | Package never grants or widens exposure |
| Book I Setup Card schema | `III.5-DEFECT-1` OPEN | Setup refs verbatim; no card-schema operation |
| Real semantic index | deterministic support only | Excerpts are untrusted, bounded, never authoritative |
| IV.2 snapshot payload values | `IntelligenceRef` is reference-only | Optional authorized detail keyed to existing snapshot id; otherwise `DETAIL_NOT_SUPPLIED` |
| IV.2 evidence statistics | absent | Optional authorized detail keyed to existing evidence id; otherwise unresolved |

No synthetic fixture may convert any of these into a positive production
capability.

---

## 4. TEST-VERSUS-CAPABILITY RULE

1. A test passes only when it asserts the exact IV.3 contract outcome.
2. A bounded state such as `PROVIDER_NOT_CONFIGURED`, `MISSING_EVIDENCE`,
   `DETAIL_NOT_SUPPLIED`, `N_NOT_PROVIDED` or `SMALL_N_UNRESOLVED` is a valid
   pass when that is the honest outcome.
3. A missing production capability may not be converted into a synthetic
   positive.
4. A green suite means the package contract is deterministic, minimized,
   provenance-preserving and injection-resistant.
5. It does not mean live data, provider token accuracy, complete statistical
   authority, entitlement or production readiness exists.

---

## 5. UPSTREAM COMPATIBILITY

| Surface | Compatibility finding |
|---|---|
| IV.1 plan | All required query fields and plan ID exist; no change needed |
| IV.2 bundle | All typed refs, limitations, refusals, trace and bundle ID exist; read-only |
| IV.2 refs | Snapshot and evidence references are sufficient for identity but not full payloads; detail projections bridge only when already authorized |
| IV.2 trace | Consumer/internal distinction is sufficient; IV.3 creates its own manifest without exposing rejected IDs |
| Book I | Canonical statuses, layers, exposure and object IDs available |
| Book II | Authorization already applied before the bundle; IV.3 does not re-decide access |
| Book III | Snapshot refs, quality, no-go and refusal available; no provider |
| III.5 | Setup identity/class/surface available; card schema defect remains |
| Routes/migrations | No change required |

---

## 6. ENTRY AND EXIT CRITERIA

### Rung 2 entry

1. Four planning documents committed and pushed.
2. Base head remains an ancestor of `forge`.
3. IV.1 60/60 and IV.2 72/72 remain green.
4. 92 requirement names and 92 test names are frozen.
5. No source, route, migration or provider change is authorized.

### Rung 2 exit

1. 92/92 exact tests pass with zero skips/xfails.
2. All 20 fixtures reproduce byte-identically.
3. No forbidden exposure enters any package or manifest.
4. Mandatory no-go/invalidation survives every budget case.
5. Full regression and both CI jobs are green.
6. Evidence/ratification separates contract PASS from live/tokenizer/
   statistical/entitlement readiness.

**Feasibility verdict:** PASS for the deterministic `CONTEXT_CONTRACT_V1`.
Production context quality, tokenizer accuracy, current data, complete
statistics and commercial entitlement remain open.
