# BOOK IV / BLOC IV.1 — FEASIBILITY & GAP GATE

**Bloc:** IV.1 · **Rung:** BA-26 Rung 1 (planning)
**Question:** can IV.1 be implemented now without inventing authority?

---

## 1. Classification key

- **F1 — directly available** in Book I/II/III contracts at this head.
- **F2 — deterministic interpreter logic** required (no new authority).
- **F3 — downstream dependent**: IV.2–IV.6 or Book VII must satisfy it.
- **F4 — blocked** by missing canonical authority or platform integration.

Classification is of **IV.1 implementation**, not of downstream execution.
A requirement can be classifiable (F2) while its downstream fulfilment is
F3/F4; the split is recorded in §3.

---

## 2. Requirement classification (53 rows)

| ID | Requirement (short) | Class | Owner / source | Closure evidence |
|---|---|---|---|---|
| R1 | definition intent | F2 | IV.1 | A-01 |
| R2 | model-description intent | F2 | IV.1 | A-02 |
| R3 | current-state intent | F2 | IV.1 | A-03 |
| R4 | level intent | F2 | IV.1 | A-04 |
| R5 | setup-context intent | F2 | IV.1 | A-05 |
| R6 | statistic intent | F2 | IV.1 | A-06 |
| R7 | comparison intent | F2 | IV.1 | A-07 |
| R8 | historical-lineage intent | F2 | IV.1 | A-08 |
| R9 | methodology intent | F2 | IV.1 | A-09 |
| R10 | indicator-navigation intent | F2 | IV.1 | A-10 |
| R11 | troubleshooting intent | F2 | IV.1 | A-11 |
| R12 | general-knowledge intent | F2 | IV.1 | A-12 |
| R13 | instrument identity | F1 | Book I/III registry | A-13 |
| R14 | model identity | F1 | Book III model registry | A-14 |
| R15 | setup identity | F1 | Book I canonical / III.5 | A-15 |
| R16 | term/alias exactness | F1 | `retrieval/aliases.py` | A-16 |
| R17 | layer vocabulary | F1 | `model_runtime.contract.Layer` | A-17 |
| R18 | session/timeframe | F1 | Book III clock/session registry | A-18 |
| R19 | generation token | F2 | IV.1 | A-19 |
| R20 | BTC Game ≠ Tracker | F4 | Book I/VII canonical promotion | A-20 |
| R21 | beginner depth | F2 | IV.1 | A-26 |
| R22 | operator depth | F2 | IV.1 | A-27 |
| R23 | researcher depth | F2 | IV.1 | A-28 |
| R24 | depth cap | F4 | Book VI capability projection / Book II policy | A-29 |
| R25 | CURRENT scope | F1 | III.6 `SnapshotRequest` | A-30 |
| R26 | AS_OF scope | F1 | III.6 `HistoricalRequest` | A-31 |
| R27 | HISTORICAL scope | F3 | IV.2 + III.6 history | A-32 |
| R28 | MODEL_VERSION scope | F1 | III.6 pinned version | A-33 |
| R29 | GENERAL scope | F2 | IV.1 | A-34 |
| R30 | no substitution | F3 | IV.2 + III.6 | A-35 |
| R31 | action detection | F2 | IV.1 | A-36, A-37, A-40 |
| R32 | setup-context flag | F2 | IV.1 | A-38 |
| R33 | no approval | F2 | IV.1 | A-39 |
| R34 | statistic detection | F2 | IV.1 | A-41, A-42 |
| R35 | evidence flag | F2 | IV.1 | A-43, A-45 |
| R36 | measurement exception | F3 | IV.2 + III.6 measurement | A-44 |
| R37 | P90 generation | F4 | Book I/VII P90 provenance | A-21 |
| R38 | ST/Base80 generation | F3 | IV.2 + doctrine/evidence | A-22 |
| R39 | old Markov/Fib | F3 | IV.2 + Book I lineage | A-23 |
| R40 | no generation promotion | F4 | Book I/VII lineage authority | A-25 |
| R41 | resolved | F2 | IV.1 | A-46 |
| R42 | explicit scope | F2 | IV.1 | A-47 |
| R43 | material ambiguity | F2 | IV.1 | A-48 |
| R44 | unsupported identity | F2 | IV.1 | A-49 |
| R45 | unavailable generation | F3 | III.6 retention + IV.2 | A-50 |
| R46 | candidates + reasons | F2 | IV.1 | A-51 |
| R47 | no fake confidence | F2 | IV.1 | A-51, A-57 |
| R48 | intent/version in plan | F1 | frozen field set | A-52 |
| R49 | ids separate from entities | F2 | IV.1 | A-53 |
| R50 | market/layer | F1 | canonical + III.6 | A-54 |
| R51 | scope/depth + immutable | F2 | IV.1 | A-55, A-59 |
| R52 | requirement flags | F2 | IV.1 | A-56 |
| R53 | deterministic serialization | F2 | IV.1 | A-58, A-60 |

**Counts: F1 = 11 · F2 = 32 · F3 = 6 · F4 = 4 · total = 53.**

---

## 3. Capability split

| Stage | Can do at IV.1 | Cannot do |
|---|---|---|
| Interpreter | classify intent/entities/depth/scope/flags/ambiguity | answer, approve, compute |
| Retrieval (IV.2) | resolve canonical objects and evidence | invent canonical ids |
| Snapshot (III.6) | provide pinned snapshots when configured | provide live data while `NOT_CONFIGURED` |
| LLM (IV.4) | explain an authorized package | supply a fact or number |
| Validator (IV.5) | authorize the final factual sentence | widen exposure or eligibility |

IV.1 is not responsible for IV.2–IV.6 capabilities.

---

## 4. F3 items — owner and closure evidence

| ID | Dependency | Owner | Closure evidence required |
|---|---|---|---|
| R27 | historical reconstruction | III.6 history + IV.2 | retained-input replay or `HISTORICAL_UNAVAILABLE` test |
| R30 | no substitution | IV.2 | current-scope test rejects corpus fallback |
| R36 | deterministic measurement | IV.2 + III.6 | measurement id/quality + snapshot test |
| R38 | ST/Base80 evidence | IV.2 + Book VII | generation-tagged evidence link |
| R39 | old Markov/Fib | IV.2 + Book I lineage | lineage resolution test |
| R45 | unavailable generation | III.6 retention | explicit `UNAVAILABLE_GENERATION`/`HISTORICAL_NOT_RETAINED` |

---

## 5. F4 items — blocking authority

| ID | Gap | Why blocked | Owner / required decision |
|---|---|---|---|
| R20 | BTC Game canonical status | launch-canonical family is BTC Tracker; BTC Game is research/artifact (`MASTER AUDIT` §9) | Book I/VII promotion decision; until then IV.1 must return `UNSUPPORTED_IDENTITY`/research scope, never Tracker |
| R24 | entitlement projection | no stable Book VI capability fingerprint (III.6-GAP-6) | Book VI capability + Book II policy contract |
| R37 | P90 current performance | historical lineage lacks current verified provenance | Book I/VII evidence identity; until then historical only |
| R40 | generation promotion guard | no lineage authority shared across generations | Book I promotion contract + Book VII |

No F4 item blocks writing the interpreter: each is represented as an explicit
outcome (`UNSUPPORTED_IDENTITY`, capped depth, historical scope, lineage flag).
Implementation may proceed only if the plan can express the gap without
closing it.

---

## 6. Feasibility verdict

- **Implementation-feasible now:** R1–R19, R21–R23, R25–R26, R28–R29,
  R31–R35, R41–R44, R46–R53 (49 requirements).
- **Feasible with governed gap outcomes:** R20, R24, R27, R30, R36–R40, R45
  (expressible, not satisfiable end-to-end).
- **Not feasible in IV.1:** live current facts, evidence retrieval, answer
  validation, entitlement grants. These are F3/F4 by design.

**Gate result: CONDITIONAL PASS for planning; implementation readiness is not
a claim of end-to-end capability.**

---

## 7. Rejected alternatives

| Alternative | Why rejected |
|---|---|
| LLM-based intent classification | non-deterministic; violates core law |
| embedding/fuzzy alias matching | can silently merge BTC Game/Tracker or P90 generations |
| numeric confidence scores | directive forbids fabricated confidence |
| interpreter-side entitlement lookup | duplicates Book II authority |
| current-state inference from corpus | violates Book III ownership |
| inventing BTC Game canonical id | plan/audit forbids |
| promoting Fib R15 to production | production eligibility remains gated |

---

## 8. Risks and stop conditions

Risks: alias vocabulary drift; generation wording overlap; depth semantics
confused with access; downstream treating `requires_evidence` as evidence;
pressure to answer in IV.1.

Stop if implementation needs a new intent, a canonical id that does not exist,
an entitlement decision, a numeric confidence, a live provider call, an LLM
call, or any Book I/II/III source change.
