# Ratification supplement V2 (BA-34)

**F-06: PASS. F-07: PASS. F-08: preserved PASS. Amendment requirements: 27/27
unchanged. No earlier ratification is edited.**

Starting head `97a83d13d2a3958b3578bc4c39eb31973a2f34a9`. Scope: IV.6 evaluation
coverage. No IV.5, IV.1–IV.4, Book I–III, hash-infrastructure, route, migration,
provider or entitlement change.

## 1. Findings

| Finding | Severity | Owner | Verdict | Basis |
|---|---|---|---|---|
| F-06 CHAIN evidence path | S3 | IV.6 | **PASS / CLOSED** | every scorable CHAIN positive has an independently declared path; 10/10 path and citation support; 4 original plan-only cases reconciled individually; 8 wrong-reference controls fail |
| F-07 refusal limitation coverage | S4 | IV.6 | **PASS / CLOSED** | all 72 V1 refusals now assert applicable user-safe limitations; 72/72 preserve; 0 leaks; 0 false refusals over 58 positives |
| F-08 checkout-encoding hash guards | S4 | Test infrastructure | **PASS, preserved** | 17/17 guards and AM1-R27 green in both encodings; helper and constants untouched by this rung |
| F-01–F-05 | as ratified | IV.5 / IV.6 | **unchanged** | their drivers remain green in the 2654-pass suite |
| F-07a limitation representation | S4 | IV.5 | **OPEN (new)** | 31 of 72 refusals convey the restriction in `detail`, not the `limitations` tuple |
| F-09 historical-lineage admission | S3 | IV.2 / IV.4 | **OPEN (new)** | P90, Base80, Markov legacy questions retrieve and package, then yield no validated answer |

F-06 and F-07 pass on measured behaviour, not on the pre-existing tests passing:
those tests are the baseline, and both contracts now fail when evidence is wrong
or a limitation is dropped.

## 2. What is ratified

- `ASK_EVALUATION_EVIDENCE_PATH_V2` and `ASK_EVALUATION_REFUSAL_LIMITATIONS_V1`
  as additive evaluation contracts, with `ASK_EVALUATION_COVERAGE_SCORING_V1`
  as their scoring supplement.
- The additive corpus `ASK_EVALUATION_DATASET_V2` (EV-145–EV-154, digest
  `aa7caee0a798deb4775192fe64026a1736341763a74947d8fa85d52df0d3eed2`).
- EC-01–EC-30 as the binding drivers for the two findings.
- The measured populations in `EVALUATION_COVERAGE_SUPPLEMENT_V1.md` §3.

## 3. What is not ratified

- F-07a as closed. It is measured and recorded, not repaired: IV.5 is frozen for
  this rung and changing the payload representation would alter frozen answers.
- F-09 as repaired, or `HISTORICAL_LINEAGE` model questions as covered.
- The two `CORPUS_ABSENT` V1 cases (EV-007, EV-010) as passing. They remain
  visible exclusions, not successes; adding the missing models is a Book I
  corpus decision.
- BG-C operational readiness, `EV-GATE-01`–`13` closure, `EV-GATE-12` human
  review, provider or market-data readiness, entitlement or retention policy.
- Any claim of complete evaluation coverage for the whole Ask CEREBUS surface.
  This rung closes two named findings over declared populations.

## 4. Original evidence preserved

| Item | State |
|---|---|
| EV-001–EV-120 and manifest digest `74bc217b…cbd31a8` | unchanged (EC-27) |
| EV-121–EV-144 and digest `881e8403…21492339` | unchanged (EC-27) |
| Q1–Q5 fixtures, `SCORING_V1`, `SCORING_V2` results | unchanged |
| Original IV.6 oracle (`oracle.py`) | unchanged |
| Original 112 evaluation drivers | unchanged, all green |
| Ratification V1, supplement V1, hash ratification V1 | unedited |
| Hash helper, constants, `.gitattributes` | unedited |

`git diff` for this rung touches only `app/forge/ask_cerebus/evaluation/`
(three new modules plus the loader), `tests/` (one new driver file) and
`implementation/forge/book_iv/` (new corpus and four documents). The evaluation
enums, dataset, versions, oracle, matching, scoring and harness modules were not
modified, so V1's 20-metric surface and exact-count assertions still hold
(EC-28).

## 5. Security non-regression

The full suite passes with all IV.5 findings repaired and their drivers green:
F-01 guidance prohibition, F-02 untrusted rendering, F-03 no-go consistency,
F-04 prose disposition, F-05 numeric populations. No validator, compiler,
citation, admission or uncertainty module changed. The amendment's 21 injection
attack cases still record zero exposures; its 20 refusals still carry
`NO_GO_ACTIVE` where an active no-go exists.

## 6. Gate status

| Gate | Verdict | Change |
|---|---|---|
| BG-A deterministic completeness | **PASS (amended scope)** | coverage extended, determinism unchanged |
| BG-B end-to-end evidence integrity | **PASS (amended scope)** | two residual limits closed; F-07a and F-09 named |
| BG-C operational readiness | **BLOCKED** | unchanged; no provider, market, entitlement or retention work |
| `EV-GATE-01`–`13` | **OPEN** | unchanged; `EV-GATE-12` not discharged |

BG-B improves only in the two named dimensions. It does not become an operational
claim, and BG-C is not unblocked by evaluation coverage.

## 7. Verification actually run

```
python -m pytest tests/test_forge_ask_cerebus_evaluation_coverage.py -q
    -> 30 passed
python -m pytest -q
    -> 2654 passed, 0 failed, 29 skipped
```

The delta from the BA-33 baseline (2624 passed) is exactly the 30 new drivers.
Native Windows and both checkout encodings remain green; the coverage contracts
read fixture and payload content, not raw file bytes, so BA-33's canonical
measurement is unaffected.

## 8. Commit ladder

| Stage | Content |
|---|---|
| 1 | additive corpus EV-145–EV-154 and its manifest |
| 2 | evidence-path evaluation V2 and the corpus loader |
| 3 | refusal-limitation evaluation V1 and the coverage scoring supplement |
| 4 | EC-01–EC-30 drivers |
| 5 | (no root-cause repair was authorized or required inside IV.6; the two findings it exposed are IV.5 and IV.2/IV.4 work) |
| 6 | coverage evidence and this supplement |
| 7 | final-head CI receipt |

Append-only; fast-forward push; no amend, squash, rebase, reset or force.
