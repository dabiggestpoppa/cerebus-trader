# BOOK IV / BLOC IV.6 — FEASIBILITY GATE
## ASK CEREBUS EVALUATION & RED TEAM
### BA-31 RUNG 1 — PLANNING PACKET

**Starting HEAD:** `578b55278ae64a6ced24e3e08782b396f07d35b4`
**Total requirements:** 102
**F1:** 61 · **F2:** 36 · **F3:** 2 · **F4:** 3

---

## 1. CLASSIFICATION LAW

| Class | Definition | Closure authority |
|---|---|---|
| **F1** | Directly supported by IV.1–IV.5 or Books I–III as they exist today | IV.6 Rung 2 |
| **F2** | Deterministic IV.6 evaluation logic (dataset, oracle, harness, scoring, report) | IV.6 Rung 2 |
| **F3** | Requires human review, a product-policy decision, or a later Book V capability | named human owner |
| **F4** | Requires a real provider, licensed market data, commercial entitlement, cross-session infrastructure, or external operational approval | Book VI / VII / VIII + operator |

**Law:** no deterministic fixture closes an F3 or F4 gate. A green IV.6 suite
proves F1 and F2 behavior only.

---

## 2. PER-REQUIREMENT CLASSIFICATION — 102

### 2.1 Chapter IV.6.1 (R1–R16)

| ID | Class | Note |
|---|---|---|
| R1 | F2 | contract constants |
| R2 | F2 | case schema |
| R3 | F2 | dataset container |
| R4 | F2 | canonical digest |
| R5 | F2 | declared evidence path |
| R6 | F2 | authority enum + rejection |
| R7 | F2 | import inspection |
| R8 | **F1** | all five stages exist and are public |
| R9 | **F1** | fixture index, fake semantic, `GatewayFakeLLM`, `SimulatedClock` exist |
| R10 | F2 | socket guard |
| R11 | F2 | id validation |
| R12 | F2 | balance check |
| R13 | F2 | execution record |
| R14 | F2 | manifest |
| R15 | F2 | version refusal |
| R16 | F2 | digest coupling |

### 2.2 Chapter IV.6.2 (R17–R24)

| ID | Class | Note |
|---|---|---|
| R17 | **F1** | canonical facts exist in Q1 fixtures |
| R18 | **F1** | IV.5 preserves limitations |
| R19 | **F1** | IV.5 numerical validator |
| R20 | **F1** | IV.5 advice validator |
| R21 | **F1** | IV.5 refusal vocabulary |
| R22 | **F1** | IV.5 status/layer validators |
| R23 | F2 | structural assertion on the answer contract |
| R24 | **F1** | IV.5 setup validator |

### 2.3 Chapter IV.6.3 (R25–R34)

| ID | Class | Note |
|---|---|---|
| R25 | **F1** | operator compiler renders model/layer/state |
| R26 | **F1** | `SEVERITY_ORDER` + `worst_verdict` already exist |
| R27 | **F1** | setup fields come from encoded `SetupRecord` |
| R28 | **F1** | no-go carried through IV.2/IV.3/IV.5 |
| R29 | **F1** | IV.5 layer validator |
| R30 | **F1** | IV.5 setup validator requires encoded eligibility |
| R31 | **F1** | IV.5 attaches epistemic status per claim |
| R32 | **F1** | IV.5 refusal vocabulary |
| R33 | **F1** | `SETUP_NOT_ENCODED` implemented verbatim |
| R34 | **F1** | IV.5 freshness validator |

### 2.4 Chapter IV.6.4 (R35–R44)

| ID | Class | Note |
|---|---|---|
| R35 | **F1** | claim identity + model version in IV.3 facts |
| R36 | **F1** | event/population facts in IV.3 |
| R37 | **F1** | N + small-N flag in IV.3 facts |
| R38 | **F1** | period + metric in IV.3 facts |
| R39 | **F1** | result value + unit in IV.3 facts |
| R40 | **F1** | OOS/reproduction facts in IV.3 |
| R41 | **F1** | `FORWARD_OOS` vs `HISTORICAL` labels exist |
| R42 | **F1** | `EVIDENCE_CLASS_LAUNDERING` covers simulation |
| R43 | **F1** | IV.3 surfaces contradictions/negative evidence |
| R44 | **F1** | IV.3 emits `DETAIL_NOT_SUPPLIED` / `N_NOT_PROVIDED` |

### 2.5 Chapter IV.6.5 (R45–R52)

| ID | Class | Note |
|---|---|---|
| R45 | **F1** | `NUMERIC_EVIDENCE_MISSING` |
| R46 | **F1** | `INSUFFICIENT_EVIDENCE` refusal |
| R47 | **F1** | `EVIDENCE_CLASS_LAUNDERING` |
| R48 | **F1** | research/automation status refusal |
| R49 | **F1** | metric substitution + evidence class |
| R50 | **F1** | `MISSING_FRESHNESS` / `CURRENT_DATA_UNAVAILABLE` |
| R51 | **F1** | `LAYER_LAUNDERING` |
| R52 | **F1** | `STATUS_LAUNDERING` / generation rule |

### 2.6 Chapter IV.6.6 (R53–R59)

| ID | Class | Note |
|---|---|---|
| R53 | **F1** | Book I aliases + IV.1 entity resolution |
| R54 | **F1** | generation ids in Book I registry |
| R55 | **F1** | distinct model ids `BTC.GAME` / `BTC.TRACKER` |
| R56 | **F1** | `RESEARCH_FLAG` label preserved |
| R57 | **F1** | `SUPERSEDED` label preserved |
| R58 | **F1** | IV.1/IV.2 resolve the asked generation |
| R59 | **F1** | `MODEL_VERSION_UNAVAILABLE` refusal |

### 2.7 Chapter IV.6.7 (R60–R67)

| ID | Class | Note |
|---|---|---|
| R60 | F2 | boundary classification is IV.6 logic |
| R61 | **F1** | Book II exposure enforcement |
| R62 | **F1** | IV.5 leakage validator |
| R63 | **F1** | IV.5 leakage validator |
| R64 | **F1** | IV.5 leakage enumeration |
| R65 | **F1** | IV.5 status validator |
| R66 | **F1** | Book III no-go + IV.5 setup validator |
| R67 | **F1** | IV.5 numerical + citation validators |

### 2.8 Chapter IV.6.8 (R68–R75)

| ID | Class | Note |
|---|---|---|
| R68 | **F1** | Book II policy, default deny |
| R69 | **F1** | Book I alias registry + policy |
| R70 | **F1** | IV.2 semantic port receives only authorized ids |
| R71 | **F1** | IV.2 historical availability handling |
| R72 | **F1** | IV.5 citation surface is typed provenance only |
| R73 | **F1** | IV.2 depth cap + policy capability |
| R74 | **F1** | policy engine is stateless and deterministic |
| R75 | **F4** | no cross-session cache or trace store exists to test |

### 2.9 Chapter IV.6.9 (R76–R82)

| ID | Class | Note |
|---|---|---|
| R76 | **F1** | `LIMITED_QUOTE_SCOPE` + IV.5 `LEAKAGE_CORPUS` |
| R77 | F2 | overlap measurement is evaluation logic |
| R78 | **F4** | cross-request reconstruction needs persistent aggregation |
| R79 | **F4** | multi-query limiting needs a shared rate/aggregation store |
| R80 | **F1** | IV.5 enumeration veto |
| R81 | **F1** | citations carry no protected id |
| R82 | F2 | classification and honest reporting |

### 2.10 Chapter IV.6.10 (R83–R92)

| ID | Class | Note |
|---|---|---|
| R83 | F2 | metric definition table |
| R84 | F2 | `NOT_APPLICABLE` population rule |
| R85 | F2 | unsupported-number numerator |
| R86 | F2 | exact-match numerator |
| R87 | F2 | two citation populations |
| R88 | F2 | correctness metrics |
| R89 | F2 | security metrics |
| R90 | F2 | usefulness metrics |
| R91 | F2 | severity + attribution |
| R92 | F2 | deterministic report |

### 2.11 Chapter IV.6.11 (R93–R98)

| ID | Class | Note |
|---|---|---|
| R93 | F2 | digest coupling |
| R94 | F2 | no-auto-update rule |
| R95 | F2 | impacted subset mapping |
| R96 | F2 | replay equality |
| R97 | F2 | evidence record assembly |
| R98 | F2 | separate verdicts |

### 2.12 Chapter IV.6.12 (R99–R102)

| ID | Class | Note |
|---|---|---|
| R99 | F2 | record schema |
| R100 | **F3** | disagreement policy requires an operator-owned disposition rule |
| R101 | **F3** | "evidence not truth" must be ratified by the corpus owner |
| R102 | F2 | honest status reporting |

### 2.13 Arithmetic

| Class | Count | Derivation |
|---|---|---|
| F1 | **61** | 2 + 7 + 10 + 10 + 8 + 7 + 7 + 7 + 3 |
| F2 | **36** | 14 + 1 + 1 + 2 + 10 + 6 + 2 |
| F3 | **2** | R100, R101 |
| F4 | **3** | R75, R78, R79 |
| **Total** | **102** | R1–R102 |

---

## 3. IV.6 DELIVERABLE FEASIBILITY

| Deliverable | Class | Why |
|---|---|---|
| Evaluation package (`app/forge/ask_cerebus/evaluation/`) | F2 | pure logic over existing types |
| Golden dataset (120 cases) | F2 | fixture-backed |
| Chain harness | F1 | five public stages exist |
| Independent oracle | F2 | literal expectations + fixture facts |
| Scoring/report | F2 | arithmetic over recorded outcomes |
| Red-team injection matrix | F1+F2 | attacks run against real boundaries |
| Entitlement matrix | F1 (mechanism) / F4 (commercial) | Book II only |
| Extraction matrix | F1 (single) / F4 (cross-session) | no persistent store exists |
| Human review workflow | F2 (record) / F3 (execution) | no reviewer exists yet |
| Launch thresholds | F3 | product authority |
| Real-provider evaluation | F4 | no provider authorized |
| Live current-data evaluation | F4 | `MARKET_DATA_STATUS = NOT_CONFIGURED` |

---

## 4. GATE REGISTER

### 4.1 Carried-forward upstream gates

| Gate | Description | Class | Owner | Closure evidence | Status |
|---|---|---|---|---|---|
| `EV-GATE-01` | IV.4 provider, tokenizer, pricing and privacy prerequisites | F4 | Gateway owner + operator | signed provider/privacy approval + real-provider eval run | OPEN |
| `EV-GATE-02` | IV.5 public citation presentation contract (R26 of IV.5) | F3 | Product/UX | ratified citation-surface spec; IV.6 citation metrics re-baselined on it | OPEN |
| `EV-GATE-03` | IV.5 current-data materiality/cutoff and the acceptable false-refusal rate | F3 | Product owner | written materiality policy + threshold decision | OPEN |
| `EV-GATE-04` | Book VI commercial entitlement | F4 | Book VI | entitlement resolution integrated behind `AuthorizationContext`; EV-094–EV-100 re-run against it | OPEN |
| `EV-GATE-05` | IV.5 corpus licensing and prose retention | F4 | Legal/Ops + Book VIII | licence terms + retention policy | OPEN |
| `EV-GATE-06` | Cross-session corpus-extraction protection | F4 | Book VIII | shared abuse store + rate/aggregation controls; EV-103/EV-104 re-run under them | OPEN |
| `EV-GATE-07` | Real current-market provider | F4 | Data owner | licensed feed + freshness contract; EV-050/EV-080–084 re-run live | OPEN |
| `EV-GATE-08` | Durable historical snapshots | F4 | Book VII | snapshot store + replay evidence | OPEN |
| `EV-GATE-09` | Governed statistics, N and small-N policy | F4 | Research owner | ratified statistic registry; EV-040/EV-043/EV-046 re-run against it | OPEN |
| `EV-GATE-10` | Real semantic retrieval | F4 | Book VII | production index; `SEMANTIC_UNAVAILABLE` gaps closed | OPEN |
| `EV-GATE-11` | IV.5 refusal-precedence ratification | F3 | Product/Governance | signed precedence ratification | OPEN |
| `EV-GATE-12` | Human/operator review execution | F3 | Operator (CEREBUS reviewer) | completed `HumanReviewRecord` set for EV-117–EV-120 | OPEN |
| `EV-GATE-13` | Launch threshold ratification | F3 | Product owner | signed threshold table referencing `SCORING_V1` metric ids | OPEN |

### 4.2 IV.6-internal dependency

| Gate | Description | Class | Status |
|---|---|---|---|
| `EV-DEP-01` | Refusal assertions target the six frozen refusal codes, not individual validation codes; any future validation-code change reopens the mapping | F2 | CLOSED BY DESIGN (this packet) |

### 4.3 What this rung cannot and does not close

- No gate in §4.1 is closed by any fixture, case or test planned here.
- `EV-GATE-04` means a passing Book II entitlement matrix is **not** commercial
  entitlement acceptance.
- `EV-GATE-06` means single-response extraction measurement is **not**
  cross-session abuse prevention.
- `EV-GATE-07` means freshness correctness is measured against fixtures, not
  against a live market.

---

## 5. FAILURE-SEVERITY AUTHORITY

| Severity | Who may waive | Waiver evidence |
|---|---|---|
| S1 | nobody | — (launch-blocking by definition) |
| S2 | Product owner | written waiver naming the case and rationale |
| S3 | Bloc owner | note in the evidence record |
| S4 | Bloc owner | note in the evidence record |

A waiver never edits a golden expectation; it is recorded beside it.

---

## 6. FROZEN INTEGRITY PINS

### 6.1 Git blobs at `578b552`

| Path | Blob |
|---|---|
| `implementation/forge/book_iv/bloc_iv_5/ACCEPTANCE.md` | `cd9edbeb834bb66f1e62643a3c25ef8fcd5acdac` |
| `implementation/forge/book_iv/bloc_iv_5/RATIFICATION.md` | `b7fb362718c6fb5efe4a367220b3060be2072bf4` |
| `implementation/forge/book_iv/bloc_iv_5/EVIDENCE.md` | `c60e223b83c49e3c1b86db4f7d5b72eae1dad13d` |
| `planning/forge/books/BOOK_IV_ASK_CEREBUS_PLAN_V1.md` | `f5c201431530ed2200cfbe1cd9959c9e7386aca6` |
| `app/forge/ask_cerebus/interpreter/plan.py` | `f898665cb804af0fff5cd7ebe6dd36b721d5a421` |
| `app/forge/ask_cerebus/retrieval/service.py` | `1b69cd5e578f264872de830dc0402413dc14e492` |
| `app/forge/ask_cerebus/context/service.py` | `74d66d9d33f0f90171ac0eca51e6023cdefbaac2` |
| `app/forge/ask_cerebus/llm_gateway/draft.py` | `a7c70c61db07136f169df2012380f956252baf35` |
| `app/forge/ask_cerebus/answer/service.py` | `dd6e3792b169c2b1db59cc107e580582bef31155` |
| `app/forge/ask_cerebus/answer/versions.py` | `28d7d9e08e247b0fdf9f437afbe058afd2eb5863` |
| `app/forge/service/routes.py` | `e83fa101f97b7f99a1ee9894d27f4672f0efbfda` |
| `app/forge/policy.py` | `11e60ea2a19eac33702b14212d8bc3fef28d0470` |

### 6.2 LF-normalized content hashes (checkout-independent)

| Path | SHA-256 |
|---|---|
| `bloc_iv_5/ACCEPTANCE.md` | `bdbbddc5c7690a5f50b22e8db602426f5e40e10b4cf04f60f802769960b72662` |
| `BOOK_IV_ASK_CEREBUS_PLAN_V1.md` | `18819a0ab0281ba9efee1b2b6f3776cf71c8efb0d21f5477edc06e20fe7f22ab` |
| `interpreter/plan.py` | `c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b` |
| `retrieval/service.py` | `d4ef64f9d3f994b08c331b48a2e720aa345f92af02d8b32a2d0feb9707d5fd83` |
| `context/service.py` | `c05b045c653ce23c749f12dea3e61d3cc42bdcebd5bbc399676a17a8cabe29cf` |
| `llm_gateway/draft.py` | `9aac55a78f78e917c24c3b78ab308af0422643e2bca718502f3672806040ba7c` |
| `answer/service.py` | `12d438945ec19c6feb32caac794ccfdd54f52c19fef53c6b2e1e23912c979d92` |
| `answer/versions.py` | `7f8263d3f71c0b3d6987f63582805441965254476613fad6e73890e0fa0876df` |
| `routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |
| `policy.py` | `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc` |

Migrations remain `[1, 2, 3, 4]`. `MARKET_DATA_STATUS = "NOT_CONFIGURED"`.

### 6.3 Verified baseline (this rung)

| Suite | Result |
|---|---|
| IV.1 | 60 passed |
| IV.2 | 72 passed |
| IV.3 | 93 passed |
| IV.4 | 72 passed |
| IV.5 | 86 passed |
| Full collection | 2,490 tests |

---

## 7. RUNG 2 IMPLEMENTATION-READINESS VERDICT

| Question | Answer |
|---|---|
| Can all 61 F1 requirements be implemented from existing interfaces? | **yes** — verified signatures, no new production route |
| Can all 36 F2 requirements be implemented deterministically? | **yes** — pure logic, fixture-backed |
| Are the 2 F3 requirements correctly deferred to human owners? | **yes** — R100, R101 |
| Are the 3 F4 requirements correctly deferred to later books? | **yes** — R75, R78, R79 |
| Does any planned case require a provider or live market? | **no** |
| Does any planned test depend on an unbuilt control? | **no** — F4 items are classified, not tested as passing |
| Is any gate silently closed by a fixture? | **no** — §4.3 |
| Is Book IV production readiness implied? | **no** — `BG-C` requires F4 closures |

**Verdict: IV.6 RUNG 2 IS FEASIBLE AND READY** for R1–R102 across F1/F2, with
F3/F4 explicitly deferred, owned and evidenced.
