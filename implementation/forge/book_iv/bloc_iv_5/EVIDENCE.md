# BOOK IV / BLOC IV.5 — EVIDENCE
## BA-30 RUNG 2

**Contract:** `ASK_ANSWER_CONTRACT_V1`
**Starting HEAD:** `5baec01ce089c4a65543b2887a8fc15088d6f195`
**Requirement set:** 76 (`R1`–`R76`)
**Acceptance drivers:** 86 (`A-01`–`A-86`)
**Golden scenarios:** 46 (`Q5-01`–`Q5-46`)
**Mode:** deterministic local evidence only; no provider, retrieval or market call.

---

## 1. IMPLEMENTED MODULE INVENTORY

`app/forge/ask_cerebus/answer/`

| Module | Responsibility |
|---|---|
| `versions.py` | Frozen contract/schema/validator-set versions, answer-id prefix, fixed validator order, F3/F4 status constants |
| `enums.py` | Depth, outcome, six answer refusal codes, refusal precedence, 33 validation codes, finding→refusal map, section ids, setup precedence, epistemic sets |
| `schema.py` | Immutable `CitationRef`, `AnswerNumber`, `AnswerClaim`, `AnswerSection`, `FinalResponseRecord`, `ValidatedAnswer`, `GovernedAnswerRefusal` with canonical payloads |
| `resolution.py` | Read-only `PackageIndex` over real `AuthorizedContextPackage` items, fact-derived `EvidenceCard`, limitations, setup items, as-of values |
| `admission.py` | `AnswerPolicy`, `Admission`, `AdmissionFailure`, draft/package/manifest identity and digest admission |
| `citations.py` | Resolution, internal-reference detection, user-facing provenance rendering, ordered de-duplicated collection |
| `validators.py` | Upstream propagation + numerical, metric/evidence-class, layer, setup/action, status/generation, freshness, leakage, citation, assembly validators |
| `compilers.py` | Beginner, operator and researcher compilers over one validation core; field bullets from authorized facts; server-side limitation propagation |
| `uncertainty.py` | Refusal selection by frozen precedence, safe refusal wording, failing-code collection |
| `record.py` | Deterministic draft fingerprint, `ANS.` answer identity, safe `FinalResponseRecord` |
| `service.py` | `validate_answer(draft, package, policy=...)` public entry point and `prepare_claims` |

Fixtures: `implementation/forge/book_iv/bloc_iv_5/fixtures/` — `_builders.py`,
`scenarios.py`, `generate.py`, 46 `Q5-*.json`, `FIXTURE_MANIFEST.json`.

Acceptance suite: `tests/test_forge_ask_cerebus_answer.py` (86 drivers).

---

## 2. REQUIREMENT COVERAGE — 76/76

Each requirement is driven by the identically numbered acceptance test.

| Group | Requirements | Drivers | Status |
|---|---|---|---|
| T1 input admission | R1–R6 | A-01–A-06 | covered |
| T2 beginner compiler | R7–R11 | A-07–A-11 | covered |
| T3 operator compiler | R12–R17 | A-12–A-17 | covered |
| T4 researcher compiler | R18–R23 | A-18–A-23 | covered |
| T5 citation/provenance | R24–R29 | A-24–A-29 | covered |
| T6 numerical validator | R30–R36 | A-30–A-36 | covered |
| T7 layer validator | R37–R41 | A-37–A-41 | covered |
| T8 setup/action validator | R42–R47 | A-42–A-47 | covered |
| T9 status validator | R48–R52 | A-48–A-52 | covered |
| T10 freshness validator | R53–R56 | A-53–A-56 | covered |
| T11 leakage validator | R57–R61 | A-57–A-61 | covered |
| T12 uncertainty/refusal | R62–R66 | A-62–A-66 | covered |
| T13 final response record | R67–R71 | A-67–A-71 | covered |
| T14 cross-cutting invariance | R72–R76 | A-72–A-76 | covered |
| Cross-cutting drivers | — | A-77–A-86 | covered |

No requirement is marked satisfied by prose alone: every row above has an
executing driver in the suite.

---

## 3. ACCEPTANCE TEST RESULT — 86/86

```
python -m pytest tests/test_forge_ask_cerebus_answer.py -q
86 passed
```

- 76 one-to-one requirement drivers (`A-01`–`A-76`).
- 10 cross-cutting drivers (`A-77`–`A-86`).
- Zero skips, zero xfails, zero placeholders, no duplicate names.

---

## 4. GOLDEN FIXTURES — 46/46 BYTE-IDENTICAL

`generate.py` writes each `Q5-*.json` with a canonical payload digest; `A-73`
rebuilds every scenario, re-runs the real compiler and compares the recorded
digest, answer identity and outcome.

| Band | Scenarios | Result |
|---|---|---|
| Valid controls | Q5-01–Q5-06 | answer, semantics/citations preserved |
| Numerical | Q5-07–Q5-14 | refused with the expected finding |
| Citation | Q5-15–Q5-19 | refused with the expected finding |
| Layer | Q5-20–Q5-23 | refused with the expected finding |
| Setup/action | Q5-24–Q5-29 | refused, fixed sentence where required |
| Status/generation | Q5-30–Q5-33 | refused with `STATUS_LAUNDERING` |
| Freshness | Q5-34–Q5-36 | refused, or unresolved clock propagated |
| Leakage | Q5-37–Q5-39 | refused with the expected leaking code |
| Refusal vocabulary | Q5-40–Q5-44 | exact frozen code, precedence honored |
| Record/determinism | Q5-45–Q5-46 | record complete, replay identical |

Two consecutive runs of all 46 scenarios produce identical payloads and
`answer_id`s (`A-83`, `A-73`).

---

## 5. VALIDATION BEHAVIOR EVIDENCE

### 5.1 Admission

Draft status, package/manifest identity, context contract, manifest digest,
package identity, draft-to-package binding and depth are all re-verified.
A mismatched draft or swapped manifest refuses before any rendering
(`A-02`, `A-03`, `A-84`).

### 5.2 Numerical truth

- Value equality against authorized `value_text` with normalization only; no
  value-changing rounding (`A-30`, `A-32`).
- Invented numbers (`A-31`), unit/scale changes (`A-33`), metric substitution
  (`A-34`), evidence-class laundering (`A-34`) and incomplete statistics
  (`A-35`) all refuse.
- Correlation→probability, target-completion→win-rate,
  basket-confirmation→win-rate and simulation→empirical are separately
  detected.
- Every numeric claim needs an admissible link inside the package (`A-36`).

### 5.3 Citations

Every material claim resolves to a rendered provenance reference
(`A-24`, `A-26`, `A-29`); unresolved, foreign or fabricated references refuse
the whole answer (`A-25`, `A-29`); a numeric claim's citation must match its
numeric link source (`A-28`).

### 5.4 Layer

L3→L1 (`A-37`), L2 path statistic→setup win rate (`A-38`), cross-layer override
without an encoded rule (`A-39`), misattributed layer (`A-40`) and non-frozen
layer vocabulary (`A-41`) all refuse.

### 5.5 Setup and action

Actionable language requires an `ELIGIBLE` encoded setup (`A-42`); the fixed
`SETUP_NOT_ENCODED` sentence is emitted verbatim (`A-43`); precedence is
`BLOCKED > UNRESOLVED > WATCH > ELIGIBLE` (`A-44`); blocking reasons are
surfaced (`A-45`); advice, sizing and execution instruction are prohibited
(`A-46`); setup fields may only restate encoded values (`A-47`).

### 5.6 Status and generation

`CANDIDATE`, `RESEARCH_FLAG`, `HISTORICAL`, `PARKED`, `SUPERSEDED` and
`NEGATIVE_EVIDENCE` cannot be promoted or dropped (`A-48`–`A-52`); the emitted
label must equal the source label and generation is preserved (`A-50`, `A-51`).

### 5.7 Freshness

Current-state claims require an `as_of`/cutoff (`A-53`); stale snapshots cannot
be presented as live (`A-54`); missing freshness refuses
`CURRENT_DATA_UNAVAILABLE` (`A-55`); `CLOCK_UNRESOLVED` is propagated rather
than hidden (`A-56`). Market data remains `NOT_CONFIGURED`.

### 5.8 Leakage and injection

Internal code/table/endpoint material (`A-57`), bulk corpus reproduction
(`A-58`), hidden-object enumeration (`A-59`), system/config disclosure (`A-60`)
and instruction injection from untrusted package text (`A-61`) are all blocked.

### 5.9 Refusal discipline

Exactly six answer refusal codes (`A-62`), deterministic precedence (`A-63`),
no fabrication or hedging into an answer (`A-64`), bounded safe detail
(`A-65`) and validator-specific failing codes (`A-66`).

### 5.10 Record

Deterministic `ANS.` identity (`A-67`), identity/model/validation codes
(`A-68`), citations and per-claim epistemic status (`A-69`), latency and cost
without secrets (`A-70`), metadata-only persistence (`A-71`).

---

## 6. FROZEN INTEGRITY

Verified unchanged by `A-74`:

| Path | SHA-256 |
|---|---|
| `app/forge/ask_cerebus/llm_gateway/draft.py` | `9aac55a78f78e917c24c3b78ab308af0422643e2bca718502f3672806040ba7c` |
| `app/forge/ask_cerebus/llm_gateway/enums.py` | `52fb6475631f7b6f3083f9e8e720b1a5f661cca0c7943701f173bf4d9e8b2892` |
| `app/forge/ask_cerebus/llm_gateway/versions.py` | `01dac8b2541788fc478e3c696ccbd13b1c7cba80d839733b2c7c3cd0f71cf61b` |
| `app/forge/ask_cerebus/context/schema.py` | `499dbdfb0054d6b1c7c41f61d6f91a2fdd15cad36346eb4297790e13b7cfc2c0` |
| `app/forge/ask_cerebus/context/enums.py` | `9c614f178707fb6ae319feed083e212591fbd51a23b1fe416ad74d07f7fe27df` |
| `app/forge/ask_cerebus/context/versions.py` | `0beaa9b0d3d1ba46cdd931f2d6405f41d96d998cb244b66b850b38d9882b8cfa` |
| `app/forge/service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

Migrations remain `[1, 2, 3, 4]`. No Book I, Book II, Book III, IV.1, IV.2,
IV.3 or IV.4 source was modified.

---

## 7. FULL REGRESSION (MEASURED)

| Suite | Command | Result |
|---|---|---|
| IV.5 | `pytest tests/test_forge_ask_cerebus_answer.py -q` | **86 passed** |
| IV.4 | `pytest tests/test_forge_ask_cerebus_gateway.py -q` | 72 passed |
| IV.3 | `pytest tests/test_forge_ask_cerebus_context.py -q` | 93 passed |
| IV.2 | `pytest tests/test_forge_ask_cerebus_retrieval.py -q` | 72 passed |
| IV.1 | `pytest tests/test_forge_ask_cerebus_interpreter.py -q` | 60 passed |
| Book III integration | `pytest tests/test_forge_book_iii_integration.py -q` | 96 passed |
| III.1 compatibility | `pytest tests/test_forge_market_data_provider_compatibility.py -q` | 49 passed |
| WP-3B | `pytest tests/test_forge_market_data_provider_integration.py -q` | 66 passed |
| Book II providers | `pytest tests/test_forge_providers.py -q` | 74 passed |
| Book I policy | `pytest tests/test_forge_policy.py -q` | 86 passed |
| Book I retrieval | `pytest tests/test_forge_retrieval.py -q` | 124 passed |
| Full repository | `python -m pytest -q` | **2461 passed, 29 skipped** |

The 29 skips are pre-existing environment-gated skips (PostgreSQL/pgvector),
not IV.5 skips. The IV.5 suite has no skips.

---

## 8. DEFECT / REPAIR HISTORY

| # | Defect found | Repair |
|---|---|---|
| 1 | `resolution.limitations()` treated a `ContextItem` as if it exposed `ref_type` | read `source_ref_type.upper()` |
| 2 | setup validator referenced a refusal code as a validation code | added `ValidationCode.SETUP_NOT_ENCODED` mapped to the same answer refusal |
| 3 | an empty-claims draft could still produce an answer | assembly validator now refuses `EMPTY_DRAFT` |
| 4 | `CLOCK_UNRESOLVED` never propagated from a `clock: UNRESOLVED` fact | mapped the fact value to the propagation code |
| 5 | researcher `PERIOD / GENERATION` omitted item generation | generation bullets added from authorized item generations |
| 6 | fixture loader registered a generic `_builders` module name and collided with an unrelated suite | fixtures load under a unique module name (`iv5_q5_builders`) |
| 7 | five acceptance tests asserted operator output for beginner semantics, a wrong migration comparison and an unlabeled replacement claim | drivers corrected; no production behavior weakened |
| 8 | unused imports in the new modules | removed |

No test was skipped, weakened, xfailed or deleted to obtain green.

---

## 9. SPEC ERRATA

The planning catalog in `ACCEPTANCE.md` did not name a validation code for every
rule. Rung 2 added these answer-level validation codes, all mapped into the six
frozen refusal codes (see `ACCEPTANCE.md` §7):

`SETUP_NOT_ENCODED`, `ADVICE_PROHIBITED`, `UNTRUSTED_INSTRUCTION`,
`MISSING_FRESHNESS`, `EMPTY_DRAFT`, `MODEL_VERSION_UNAVAILABLE`,
`ACCESS_NOT_ENTITLED`, `AMBIGUOUS_SCOPE`.

The six refusal codes and their precedence are unchanged.

---

## 10. F3/F4 STATUS — UNCHANGED

| Gate | Status |
|---|---|
| R26 citation presentation authority | F3 open — typed provenance only |
| R39 cross-layer override authority | F3 open — no override rule exists; violation refuses |
| R53 current-state materiality/cutoff | F3 open — declared policy only |
| R55 missing-freshness materiality | F3 open — refuse, never assume |
| R63 refusal-precedence ratification | F3 open — documented order implemented |
| R58 corpus reproduction licensing | F4 open — per-item quote ceiling only |
| R71 prose retention policy | F4 open — metadata-only persistence |

A synthetic pass does not close any of these.

---

## 11. IV.6 READINESS

IV.6 can consume:

- the 86 executing drivers and their names;
- 46 regenerable golden fixtures with canonical digests;
- `FinalResponseRecord` for both outcomes;
- the six-code refusal catalog and the failing-code list;
- reproducible answers for identical draft/package pairs.

IV.6 must still supply launch-suite evaluation and any real-provider evidence.

---

## 12. CLAIMS NOT MADE

- No answer is claimed to be true; `ValidatedAnswer` is a bounded, cited
  explanation of authorized context.
- No provider, model, retrieval or market call was made or tested.
- No production entitlement, licensing, retention or freshness policy exists.
- A green deterministic suite is contract evidence, not production acceptance.
