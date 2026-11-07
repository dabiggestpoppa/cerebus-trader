# BOOK III INTEGRATION — FEASIBILITY GATE

**Packet:** BA-23 Rung 2 · **Status:** PRE-IMPLEMENTATION GATE
**Starting head:** `9f423a490d6b1d74be4f2bd03827593152103e4c`
**Depends on:** `PLAN.md`, `ACCEPTANCE.md`, `DEPENDENCY_GATE_MATRIX.md`

This gate is executed **before** any integration test is written. It answers one
question per frozen requirement: can this be proven with the ratified public
interfaces, or does it require authority that does not exist?

It also resolves the test-versus-gate ambiguity that otherwise lets a green
suite masquerade as a closed release gate.

---

## 1. Resolution of the test-versus-gate ambiguity

### 1.1 The rule

| # | Rule |
|---|---|
| R1 | A frozen test **passes** only when it asserts the exact outcome the frozen contract permits for the constructed inputs. |
| R2 | Where the frozen contract specifies a bounded refusal (`PROVIDER_NOT_CONFIGURED`, `DATA_QUALITY_BLOCKED`, `SCHEMA_INCOMPATIBLE`, `HISTORICAL_UNAVAILABLE`, `VERSION_DRIFT`, …), asserting that refusal **is** a pass — it is not a weakened positive. |
| R3 | Where a requirement demands a positive capability that no ratified module can supply, the test is **not** rewritten to fake it. The requirement is recorded `BLOCKED` with its owning packet, and the integration gate stays **OPEN**. |
| R4 | A green suite therefore means *contracts compose and governed refusals are correct*. It does **not** mean durability, live data, exposure or production readiness exist. |
| R5 | Gate status is computed from the A-class register, not from the test count. `96/96` can coexist with `GATE: OPEN`. |

### 1.2 Consequences

- No test may be skipped, xfailed or renamed to hide a missing capability.
- No fixture may fabricate a canonical rule, anchor eligibility, approval or
  statistic to make a positive path possible.
- The ratification record must state both numbers separately:
  **tests passed** and **gate status**.

---

## 2. Feasibility classification

| Class | Meaning | Count |
|---|---|---:|
| F1 | Directly provable through ratified public APIs | 63 |
| F2 | Provable through the integration harness over those APIs (no upstream edit) | 25 |
| F3 | Provable only as a frozen bounded refusal | 8 |
| F4 | Requires unavailable authority → test asserts the governed absence; gate stays OPEN | 0 |
| **Total** | | **96** |

No frozen name is infeasible. Six requirements exercise A-class gaps and are
therefore proven as **governed absence/refusal**, which keeps the system gate
OPEN while the contract itself is verified.

### 2.1 A-class blockers carried into the verdict

| Gap | Frozen requirement affected | What the suite can prove | Gate effect |
|---|---|---|---|
| III.4-GAP-10 durable transition history | IN-61…68 | in-memory retained-input replay, hash equality, distinct unavailability codes | OPEN |
| III.5-GAP-6 setup durability | IN-45, IN-64 | transport verbatim; no persistence claim | OPEN |
| III.6-GAP-1 durable snapshot store | IN-61…68 | no cross-process history; disclosure asserted | OPEN |
| III.5-GAP-4 trigger observation source | IN-39, IN-40 | blind touch and unresolved anchor cannot reach `ELIGIBLE` | OPEN |
| III.5-DEFECT-1 card schema | IN-69…76 | three machine errors, verbatim transport, `SCHEMA_INCOMPATIBLE` | OPEN |
| III.6-GAP-2 provider | IN-11, IN-19, IN-95 | `PROVIDER_NOT_CONFIGURED`; seam byte-identical | OPEN for live data |

---

## 3. Per-family feasibility

| Family | Names | Proven by | Notes |
|---|---|---|---|
| T1 lineage | 10 | III.1 `Bar`, III.2 `Measurement`, III.3 `ModelOutput`, III.4 `StateSnapshot`, III.5 `evaluate_setup`, III.6 `compose` | one key carried through every stage |
| T2 quality | 9 | III.1 finality/quality, III.2 constructors, III.6 freshness + `short_circuit_codes` | refusal codes are the frozen vocabulary |
| T3 families | 9 | III.3 registry keys, III.5 surfaces, III.6 views | no confluence field exists |
| T4 path | 8 | III.4 `build_path`, snapshot/ledger helpers | ambiguity asserted, never guessed |
| T5 setup | 9 | III.4 stand-down + III.5 `evaluate_setup` + III.6 payload | XAU/Fib/JPY restrictions survive |
| T6 policy | 7 | III.6 `IntelligenceGateway` over Book II enforcement | spy loader proves zero calls |
| T7 determinism | 8 | III.6 identity/hash/serialization | view labels excluded from hashes |
| T8 history | 8 | III.6 `HistoryStore` | no durable store claimed |
| T9 cards | 8 | III.6 `card_machine_errors` + corpus cards | exactly three errors each |
| T10 consumer | 7 | III.6 DTO + payload scans | consumer contract only |
| T11 security | 7 | gateway, cache, refusals, serialization | no entitlement hash invented |
| T12 integrity | 6 | freeze manifests, module counts, migration files, seam | detects real drift |

---

## 4. Gate decision

**Feasibility: PASS — all 96 names are implementable.**

**System gate after implementation: expected PARTIAL/OPEN**, because the six
A-class blockers above cannot be closed by tests. The implementation rung must
publish that status rather than converting refusal coverage into closure.
