# BOOK IV / BLOC IV.3 — EVIDENCE
## CONTEXT PACKAGER — BA-28 RUNG 2

**Starting HEAD:** `0d64fa8cf6d1c568dae6d7110281d38b5587705a`
**Implementation HEAD:** `812aa7fb3c4f3eb00177a21d7a49338f3bca9506`
**Contract:** `CONTEXT_CONTRACT_V1`
**Verdict:** PASS (deterministic contract)

---

## 1. PHASE 0 FOUNDATION

| Check | Result |
|---|---|
| Local HEAD equals `origin/forge` at start | PASS — `0d64fa8…` |
| Append-only ancestry from planning head | PASS |
| Four IV.3 planning documents present | PASS |
| IV.1 plan contract / 60 tests | PASS |
| IV.2 contract / 72 tests | PASS |
| IV.2 18 fixture baseline | PASS |
| Book III integration / 96 tests | PASS |
| Frozen routes and migrations | PASS — `145757e0…d190af`; `[1,2,3,4]` |
| Market provider | `NOT_CONFIGURED`; unchanged |
| `.bu_tmp/` | Preserved |

Focused pre-implementation check: `132 passed` for IV.1 + IV.2. Book III:
`96 passed`.

---

## 2. IMPLEMENTED MODULES

`app/forge/ask_cerebus/context/`

| Module | Responsibility |
|---|---|
| `versions.py` | Contract, manifest, estimator and identity constants |
| `enums.py` | Sections, outcomes, labels, trust and refusal vocabularies |
| `schema.py` | Immutable facts, items, sections, details, package, manifest |
| `selector.py` | Section/object applicability and general-knowledge permission |
| `compression.py` | Canonical fact construction and bounded excerpts |
| `labels.py` | Status mapping, number admission, small-N state |
| `trust.py` | Exposure, fact and field allowlists, excerpt handling |
| `budgeting.py` | `CTX_UTF8_QUARTER_V1`, replaceable tokenizer port, trimming |
| `manifest.py` | Section digests, trust-boundary hash and manifest digest |
| `service.py` | Packaging, authorization checks, refusal paths and output |
| `__init__.py` | Public IV.3 surface |

No retrieval service, policy engine, canonical store, route or migration was
added.

---

## 3. REQUIREMENT COVERAGE

| Group | Requirements | Covered |
|---|---|---:|
| T1 context sections | R1–R9 | 9/9 |
| T2 canonical compression | R10–R16 | 7/7 |
| T3 token budgets | R17–R24 | 8/8 |
| T4 epistemic labels | R25–R33 | 9/9 |
| T5 layer ownership | R34–R40 | 7/7 |
| T6 small-N/evidence | R41–R49 | 9/9 |
| T7 no-evidence | R50–R55 | 6/6 |
| T8 injection resistance | R56–R63 | 8/8 |
| T9 exposure minimization | R64–R71 | 8/8 |
| T10 context manifest | R72–R79 | 8/8 |
| T11 failure/refusal | R80–R86 | 7/7 |
| T12 frozen integrity | R87–R92 | 6/6 |
| **Total** | **R1–R92** | **92/92** |

Feasibility remains **F1/F2/F3/F4 = 22/65/2/3**. F3/F4 were not converted into
positive production capabilities.

---

## 4. TEST RECONCILIATION

`tests/test_forge_ask_cerebus_context.py`

- Named requirement drivers: **92** (`C-01`–`C-92`).
- Exact-name comparison against `ACCEPTANCE.md`: 92 expected, 92 found,
  92 unique, zero missing, zero extra.
- Additional fixture reproduction driver: 1.
- Total collected: **93**.
- Result: **93 passed** in 4.69s.
- Skips/xfails: **0**.
- Weak placeholder tests: none.

```
93 passed in 4.69s
```

---

## 5. TWENTY GOLDEN FIXTURES

`implementation/forge/book_iv/bloc_iv_3/fixtures/`

- `_builders.py` — deterministic scenario construction.
- `generate.py` — writes all expected packages and manifest.
- `PROVENANCE.md` — input and boundary for every scenario.
- `FIXTURE_MANIFEST.json` — LF-normalized SHA-256 and byte counts.
- `expected/Q3-01.json`–`expected/Q3-20.json`.

Measured: **20 generated, 20 unique package identities, 20 reproduced
byte-identically**. Q3-20 is the mandatory-overflow refusal; Q3-19 is the
exposure refusal. No fixture claims live data or empirical performance.

---

## 6. SOURCE AND IDENTITY MATCHING

- Required equality: `plan.plan_id == bundle.query_plan_id`.
- Unsupported plan/bundle versions refuse.
- Optional intelligence details are accepted only for snapshot IDs already in
  the bundle.
- Optional evidence statistics are accepted only for evidence IDs already in
  the bundle.
- Unknown detail IDs refuse with `CONTEXT_DETAIL_UNAUTHORIZED`; no loader is
  called.
- Duplicate canonical identities are suppressed; status/facts are not merged.
- Detail cannot alter status, layer, exposure or identity.

---

## 7. CONTEXT SECTIONS

All nine frozen sections exist:

`QUERY_CONTRACT`, `CURRENT_INTELLIGENCE`, `CANONICAL_MODEL`, `SETUP`, `CLAIMS`,
`EVIDENCE`, `LINEAGE_TERMS`, `LIMITATIONS_NEGATIVE`, `GENERAL_KNOWLEDGE`.

Only applicable sections are emitted. Absent sections are recorded in the
manifest. Query control is always present in non-refusal packages. Limitations
and refusals remain mandatory.

---

## 8. BUDGET ACCOUNTING AND OVERFLOW

- Estimator: `CTX_UTF8_QUARTER_V1`.
- Default: 4,096 units; reserve: 512.
- Excerpt cap: 1,000 characters; section cap: 64 items.
- Mandatory floor is estimated before optional trimming.
- Optional trimming follows reverse priority with stable ordering.
- Trimmed items enter the omission ledger.
- Mandatory overflow returns `CONTEXT_BUDGET_EXCEEDED` with no sections and no
  partial narrative.

Q3-20 verifies the refusal. C-21 verifies that mandatory no-go cannot be
trimmed.

---

## 9. EPISTEMIC LABELS

- Only the frozen label vocabulary is emitted.
- `INFERENCE` is reserved; scans and C-31 confirm IV.3 never emits it.
- Source status is retained verbatim alongside the mapped label.
- Canonical identity is not numerical validation.
- Candidate/validated status is not promoted by packaging.
- Falsified/parked/superseded evidence remains negative.
- Unmapped statuses fail closed with no number.
- General knowledge carries only the allowance marker.

---

## 10. LAYER SEPARATION

- Canonical and claim layers are preserved from authorized sources.
- Setup layers remain source-derived.
- L3 results are not placed in L1 setup fields.
- L2 path facts are not entry authority.
- Historical P90 remains historical.
- JPY manual state has no execution permission.
- Fib research state has no production surface.
- Cross-layer output contains no confluence score.

---

## 11. NUMERICAL AND SMALL-N INTEGRITY

- Metric, event, population, sample size and period are retained when supplied.
- Missing N emits `N_NOT_PROVIDED`; no zero or default is substituted.
- Missing threshold emits `SMALL_N_UNRESOLVED`; no threshold is invented.
- Actual governed N is retained even when the threshold is unresolved.
- Evidence status, provenance and OOS state are retained.
- Conflicting evidence is packaged on both sides with original statuses.
- Unsupported, missing or inadmissible evidence cannot emit a result value.

---

## 12. MISSING-EVIDENCE PATH

Q3-05, Q3-07 and Q3-09 verify:

- explicit `MISSING_EVIDENCE` control;
- known model/claim context retained;
- no intuition, semantic or historical substitution;
- no unsupported statistic;
- `PARTIAL`, never verified, when evidence is missing.

---

## 13. INJECTION RESISTANCE

- Retrieved text is `UNTRUSTED_DATA`.
- Control facts are `TRUSTED_CONTROL`.
- Trusted control items carry no excerpt text.
- Source text cannot alter query control, no-go, labels, layers, identity,
  setup or exposure.
- Instruction-like text remains bounded data and is SHA-256 hashed.
- Secret-like semantic text is excluded rather than forwarded.

Q3-18 and C-56–C-63 verify the boundary structurally, not by relying on an LLM
instruction.

---

## 14. EXPOSURE MINIMIZATION

- `INTERNAL_METHOD` and `INTERNAL_CODE` refuse the package.
- Denied identifiers do not enter package, manifest or omission metadata.
- Exposure is never widened.
- Facts/items obey allowlists.
- Excerpts are bounded.
- Secret-like semantic material is excluded.
- Consumer manifest contains no forbidden internal identity.
- Omissions carry section/reason and only authorized source IDs.

Q3-19 verifies a fail-closed exposure refusal with no identifier leakage.

---

## 15. MANIFEST DETERMINISM

- Manifest binds plan ID and bundle ID.
- Manifest binds `CONTEXT_MANIFEST_V1` and `CONTEXT_CONTRACT_V1`.
- Included/omitted sections and authorized object IDs are recorded.
- Section digests and trust-boundary hash are deterministic.
- Package ID: `PKG.<32 hex>`.
- Manifest digest: `MFD.<64 hex>`.
- Canonical JSON; no clock, random, process, path or cache identity.
- Same inputs reproduce identical bytes.

---

## 16. FROZEN UPSTREAM INTEGRITY

Pinned and rechecked:

| File | SHA-256 prefix |
|---|---|
| IV.1 `plan.py` | `c43a34ba…fd344b` |
| IV.2 `bundle.py` | `b38b356e…cc3455` |
| IV.2 `refs.py` | `bbe1b937…1daa2` |
| IV.2 `trace.py` | `6f8f0800…2e44d` |
| IV.2 `service.py` | `d4ef64f9…5fd83` |
| Book I `policy.py` | `f10751e6…28fcc` |
| Book II enforcement | `9ccc3b72…6e381` |
| Book III contracts | `7d8f90ad…97d4f0` |
| Routes | `145757e0…d190af` |

No frozen upstream module, route, migration or provider setting was modified.

---

## 17. DEFECTS AND REPAIRS

| Finding | Repair |
|---|---|
| EUR detail `state` rejected by fact allowlist | Added governed intelligence paths `state`, `levels`, `path`, `setup`, `cutoff` |
| Setup appeared in both canonical and setup sections | Excluded SETUP from the canonical selector; setup owns its section |
| Claim layer was blank because model ID and object ID differ | Added model-ID/object-ID alias mapping for layer derivation |
| Q3-02 and Q3-09 initially produced identical bytes | Made missing-N fixture distinct with explicit N absence |
| One omission test used a nonbinding budget | Derived the budget from the measured canonical baseline |
| Injection tests searched preserved text for forbidden words | Corrected assertions to inspect trusted control state |
| Refusal-manifest test expected no omitted section list | Corrected to verify no denied identity and only valid section IDs |

All repairs are covered by the 93 passing tests. No assertion was weakened to
make a defect disappear.

---

## 18. REGRESSION

- IV.3: **93 passed**.
- IV.1 + IV.2 focused: **132 passed**.
- Book III integration: **96 passed**.
- Full repository: **2,303 passed, 29 skipped, 4 warnings in 106.93s**.
- Baseline was 2,210 passed, 29 skipped; IV.3 adds 93 passing tests.
- No prior test was removed or relaxed.

---

## 19. CI EVIDENCE

- Run: `42417788907`
- Head: `812aa7fb3c4f3eb00177a21d7a49338f3bca9506`
- `test`: **SUCCESS**, 37s
- `postgres`: **SUCCESS**, 1m0s
- URL: https://github.com/dabiggestpoppa/cerebus-trader/actions/runs/42417788907

Final documentation-head CI is recorded separately in `CI_RECEIPT.md`.

---

## 20. NON-CLAIMS

A green IV.3 contract does **not** establish:

- provider-tokenizer accuracy (R18);
- complete governed statistical bodies (R41);
- a canonical small-N threshold (R43);
- live current data;
- durable history;
- Book VI entitlement;
- general-knowledge/inference authority;
- production LLM behavior;
- Book IV completion.

**Evidence verdict:** deterministic `CONTEXT_CONTRACT_V1` satisfied.
Operational and downstream capabilities remain explicitly open.
