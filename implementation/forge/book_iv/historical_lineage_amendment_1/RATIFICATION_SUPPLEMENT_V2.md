# RATIFICATION_SUPPLEMENT_V2

**BA-36 — Corrected BA-35 verdicts after hash-pin reconciliation and CI recovery.**
**Append-only supplement. Preserves BA-35 `RATIFICATION_SUPPLEMENT_V1.md` as historical evidence; does not overwrite it.**

## 1. Relationship to V1

`RATIFICATION_SUPPLEMENT_V1.md` (BA-35 Rung 2) recorded F-09/F-09b/F-10/F-07a
as PASS while noting that full regression and final-head CI were red due to
the authorized `retrieval/service.py` hash-pin conflict. This supplement
records the state after BA-36 governed hash-pin reconciliation: the pins are
rebaselined, the full regression is green, and final-head CI is the
gate for the final verdict.

V1 is preserved verbatim as historical evidence of the behavioural repair.

## 2. Corrected verdicts

| Item | V1 verdict | V2 verdict | Basis |
|---|---|---|---|
| F-09 — IV.2 historical-intelligence routing repair | PASS | PASS | 28/28 drivers (R01–R28); H1–H3 reach governed answer path; zero `ERROR` |
| F-09b — IV.6 refusal-composition repair | PASS | PASS | No `None` reaches `validate_answer`; governed admission failures preserved |
| F-10 — unmapped-intent harness behaviour | PASS (negative control) | PASS (negative control) | `INDICATOR_NAVIGATION` → governed `ROUTE_UNSUPPORTED`; no new task |
| F-07a — semantic contract (Option C) | PASS | PASS | 15/15 drivers (A01–A15); zero payload change |
| Security non-regression (AM1-R01–R27, EC-01–EC-30) | PASS | PASS | 27 amendment drivers + 30 coverage drivers green |
| Hash-pin reconciliation (BA-33) | BLOCKED (conflict) | PASS | 4 affected pins rebaselined; mutation detection preserved |
| Full deterministic regression | 4 failed (hash pins) | PASS | 0 failed after pin update |
| Final-head CI (`test` + `postgres`) | FAILURE (run 43240708557) | PENDING | Awaiting GitHub Actions conclusion after final push |

## 3. Full regression

Baseline (BA-35 Rung 1 starting head `dc3a5e7`): **2,654 passed / 0 failed / 29 skipped.**

BA-35 Rung 2 head `99a5bfa`: **2,692 passed / 4 failed / 29 skipped** (4 hash-guard conflicts on the authorized `retrieval/service.py` diff).

BA-36 head (after pin update + F-07a A01/A05 split): **0 failed**. 42 new behavioural drivers (28 F-09 + 15 F-07a) all pass; EV-155–EV-178 corpus (24 cases) governed-correct; all original suites (IV.1–IV.6, security amendment, coverage, hash guards, Q1–Q5, EV-001–EV-154) green.

## 4. F-07a acceptance completeness

15 requirements (A01–A15) → 15 drivers, 15/15 PASS. Option C ratified with zero payload change. See `F07A_ACCEPTANCE_RECONCILIATION_V1.md`.

## 5. BG-A / BG-B / BG-C

| Gate | Verdict | Basis |
|---|---|---|
| BG-A deterministic completeness | PASS | Deterministic fixture execution, no stage errors |
| BG-B end-to-end evidence integrity | PASS | 0 S1 findings, correct refusal rates preserved |
| BG-C operational readiness | BLOCKED | Unchanged; no provider, market, entitlement or retention work (not authorized) |

BG-A/BG-B are deterministic-fixture results, not production readiness; BG-C
cannot pass in this amendment and is not inferred from BG-A/BG-B.

## 6. EV-GATE-01–13

**OPEN** (unchanged). `EV-GATE-12` human review not discharged. No closure
claimed by this amendment.

## 7. Final verdict rule

Per BA-36 §10: **If either final-head CI job (`test` or `postgres`) fails,
the final verdict is not PASS.** The behavioural repair and hash-pin
reconciliation are complete locally; the final PASS verdict is conditional on
both GitHub Actions jobs reporting success after the final fast-forward push
to `forge`.
