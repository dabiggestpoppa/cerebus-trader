# Evaluation coverage supplement V1 (BA-34)

Scope: IV.6 evaluation coverage only. No IV.5 change, no canonical-hashing
change, no provider, market, entitlement or route work. Additive: no historical
case, digest, oracle result or ratification was edited.

## 1. What was added

| Artefact | Path | Version |
|---|---|---|
| Evidence-path contract | `app/forge/ask_cerebus/evaluation/evidence_path.py` | `ASK_EVALUATION_EVIDENCE_PATH_V2` |
| Refusal-limitation contract | `app/forge/ask_cerebus/evaluation/limitations.py` | `ASK_EVALUATION_REFUSAL_LIMITATIONS_V1` |
| Coverage scoring supplement | `app/forge/ask_cerebus/evaluation/coverage_scoring.py` | `ASK_EVALUATION_COVERAGE_SCORING_V1` |
| Additive corpus loader | `app/forge/ask_cerebus/evaluation/corpus.py` | loads V2 by path |
| Additive corpus | `implementation/forge/book_iv/bloc_iv_6/fixtures_v2/` | `ASK_EVALUATION_DATASET_V2` |
| Drivers | `tests/test_forge_ask_cerebus_evaluation_coverage.py` | EC-01–EC-30 |

## 2. Additive corpus identity

| Field | Value |
|---|---|
| Dataset version | `ASK_EVALUATION_DATASET_V2` |
| Cases | EV-145–EV-154 (10) |
| Digest | `aa7caee0a798deb4775192fe64026a1736341763a74947d8fa85d52df0d3eed2` |
| Execution mode | 10 CHAIN (no scripted packages) |
| Declared canonical paths | 9 |
| Declared plan-only controls | 1 (EV-154) |
| Location | `bloc_iv_6/fixtures_v2/`, beside the frozen V1 corpus |

EV-001–EV-120 and EV-121–EV-144 are untouched; their digests are re-asserted by
EC-27 (`74bc217b…cbd31a8` and `881e8403…21492339`).

## 3. Metric populations

| Metric | Numerator / denominator | Eligible | Excluded | Status |
|---|---|---|---|---|
| `chain_evidence_path_correctness` | **10 / 10** | EV-006, EV-145–EV-153 | EV-001, EV-002 (definitional plan source); EV-007, EV-010 (corpus absent); EV-154 (plan-only by design) | MEASURED |
| `citation_support_correctness` | **10 / 10** | same | same | MEASURED |
| `refusal_limitation_correctness` | **72 / 72** | all 72 V1 refusals | none (no V1 refusal lacks an applicable limitation) | MEASURED |
| `protected_refusal_leakage_rate` | **0 / 72** | all 72 V1 refusals | none | MEASURED |
| `false_refusal_rate` | **0 / 58** | 48 V1 + 10 V2 positives | none | MEASURED |

Denominator discipline: a case with no independently declared evidence path does
not enter the path denominator; a case with no applicable limitation cannot count
as a preservation success. The five path exclusions are named with their reasons
above, not silently dropped, and each remains visible in
`EVIDENCE_PATH_COVERAGE_V1.md`.

## 4. Requirement inventory (EC-01–EC-30)

The requirement set is derived from the mission's required coverage, not from a
target number: eight path families, eight refusal families, four integrity
families, plus scoring and independence.

| Family | Drivers |
|---|---|
| Baseline and V1 CHAIN reconciliation | EC-01, EC-02, EC-03, EC-04, EC-05 |
| Additive corpus integrity | EC-06, EC-07, EC-08 |
| Wrong-reference negative controls | EC-09 wrong model; EC-10 plan substitution; EC-11 generation mismatch; EC-12 irrelevant authorized citation; EC-13 missing evidence; EC-14 context omission; EC-15 dropped citation; EC-16 unauthorized evidence |
| Oracle independence | EC-17 import law (AST-parsed) |
| Refusal limitation coverage | EC-18 expectation coverage; EC-19 preservation; EC-20 missing-limitation detection; EC-21 leak detection; EC-22 no-go where blocked; EC-23 freshness limitation |
| False refusals and explanation | EC-24 rate 0/58; EC-25 blocked action, allowed explanation |
| Scoring and historical integrity | EC-26 denominators and exclusions; EC-27 historical digests; EC-28 frozen versions and metric surface |
| Manifest and substitution | EC-29 manifest identity; EC-30 plan-only rejection |

30 drivers, no skips, no xfails, no assertion-free test, no shape-only test where
an exact evidence identity is required, no expectation inferred from the run.

## 5. Findings

| ID | Severity | Owner | State | Basis |
|---|---|---|---|---|
| F-06 CHAIN evidence path | S3 | IV.6 | **CLOSED** | 10/10 path correctness; 4 plan-only cases individually reconciled; 8 negative controls fail as required |
| F-07 refusal limitation coverage | S4 | IV.6 | **CLOSED** | 72/72 preserve applicable limitations; 0 leaks; 0 false refusals over 58 positives |
| F-07a limitation representation | S4 | IV.5 | **OPEN** | 31 of 72 refusals convey the restriction in `detail`, not the `limitations` tuple |
| F-09 historical-lineage admission | S3 | IV.2 / IV.4 | **OPEN** | P90, Base80 and Markov legacy model questions retrieve and package, then produce no validated answer |
| F-01–F-05 | as ratified | IV.5 / IV.6 | unchanged | drivers still green |
| F-08 hash guards | S4 | Test infrastructure | **CLOSED (BA-33)** | 17/17 guards in both encodings; not reopened |

F-07a and F-09 are new findings produced by this rung. Neither is repaired: IV.5
and IV.4 are frozen for BA-34, and F-09's repair is a task-mapping or admission
decision outside evaluation. Both are recorded with their evidence rather than
absorbed into a passing metric.

## 6. Prior-population comparison

| Population | Before BA-34 | After BA-34 |
|---|---|---|
| V1 CHAIN positives with a declared canonical expectation | 4 of 5 had none | 5 of 5 declared; 1 scorable canonical, 2 definitional, 2 corpus-absent |
| V1 refusals asserting limitation preservation | 0 / 72 | 72 / 72 |
| Additive CHAIN positives | 1 (EV-144) | 11 (EV-144, EV-145–EV-154) |
| Evidence-path negative controls | 0 | 8 |
| Evaluation drivers | 112 (V1) + 3 (amendment) | 112 + 3 + 30 |

No historical result is reinterpreted. V1's 48/48 answered positives, 72/72
correct refusals and 0/48 false refusals stand; the amendment's 4/4 positives and
20 refusals stand.

## 7. Verification

```
python -m pytest tests/test_forge_ask_cerebus_evaluation_coverage.py -q   -> 30 passed
python -m pytest -q                                                      -> 2654 passed, 29 skipped
```

The full suite count moved from 2624 to 2654 by exactly the 30 new drivers; no
existing test changed status.
