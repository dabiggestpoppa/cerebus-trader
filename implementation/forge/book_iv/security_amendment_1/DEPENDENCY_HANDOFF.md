# Security Amendment 1 — dependency handoff (BA-32 Rung 1)

Repair is **not** authorized in this rung. This document names what a separately
authorized Rung 2 would touch, who owns each failure, and what must remain
frozen.

## 1. IV.5 source modules that may need repair

| Module | Suspected change | Finding |
|---|---|---|
| `app/forge/ask_cerebus/answer/validators.py` | untrusted-content rendering check; execution-guidance check by effect rather than phrase list; no-go/limitation consistency check | F-01, F-02, F-03 |
| `app/forge/ask_cerebus/answer/compilers.py` (bullet assembly) | provenance and `UNTRUSTED` marker on rendered bullets | F-02 |
| `app/forge/ask_cerebus/answer/service.py` | `proposed_prose` discard path must record a finding | F-04 |
| `app/forge/ask_cerebus/context/*` | only if label propagation to the rendered bullet is missing; investigation first, no pre-emptive edit | F-02 |

Not to be touched: exposure allow/deny sets in `context/trust.py` (P1 never
crossed them), the numeric validators (0/9 unsupported in answers), and the
setup gate (`SETUP_NOT_ENCODED` behaved correctly in V22/V26).

## 2. IV.6 evaluation modules that may need extension

| Module | Extension | Finding |
|---|---|---|
| `evaluation/scoring.py` | additive `SCORING_V2` metric specs and names (§8 of `PLAN.md`) | F-05 |
| `evaluation/report.py` (metric emitters) | print excluded-attack counts | F-05, oracle visibility |
| `implementation/forge/book_iv/bloc_iv_6/fixtures/cases.py` | **new version file**, `EV-121+`, not edits | F-06, F-07 |
| `evaluation/matching.py` | evidence-path assertion for `CHAIN` positives | F-06 |

`evaluation/oracle.py` must not change. If a proposed expectation requires
touching it, the expectation is wrong.

## 3. Tests to be added

27 drivers in two new files (§1 of `ACCEPTANCE.md`), plus the new versioned case
bundle. No existing test is edited. `tests/test_forge_ask_cerebus_evaluation.py`
keeps its 112 drivers and its digest expectations.

## 4. Contracts that remain frozen

- `EV-001`–`EV-120`, `Q1`–`Q5`, oracle, adversarial families, frozen acceptance
  tests, `SCORING_V1`, both ratified digests.
- Book II policy, exposure classes, entitlement model.
- IV.3 trust classification and IV.4 prompt separation (proven correct here;
  the defect is downstream).
- Provider seam, routes, migrations `[1,2,3,4]`, frozen upstream hashes.

## 5. Ownership

| Finding | Severity | Owner | Blocking? |
|---|---|---|---|
| F-01 execution guidance admitted | S1 | IV.5 answer validation | blocks `BG-B` re-rating |
| F-02 untrusted text rendered unmarked | S2 | IV.5 (+ IV.3 label propagation) | blocks `BG-B` re-rating |
| F-03 no-go contradiction | S2 | IV.5 answer validation | blocks `BG-B` re-rating |
| F-04 prose unvalidated | S3 | IV.4/IV.5 boundary | does not block |
| F-05 numeric metric mislabel | S3 | IV.6 scoring | blocks amended report |
| F-06 chain positives shape-only | S3 | IV.6 fixtures (v2) | blocks amended report |
| F-07 refusals never assert limitations | S4 | IV.6 fixtures (v2) | does not block |
| F-08 hash guards encoding-dependent | S4 | test infrastructure, separate scope | blocks Windows green only |

## 6. Versioned amendment requirement

Because `BG-A` and `BG-B` were ratified on a 120-case corpus, a new verdict
requires a **versioned supplemental evaluation**, not an overwrite:

- `SCORING_V1` + `EV-001..120` remain the ratified record.
- `SCORING_V2` + `EV-121..` carry the enlarged population including P1/P2/P3.
- The amendment record states that the earlier zero-success rate applies to the
  earlier population only.
- `BG-A`/`BG-B` are re-scored under V2 with an explicit delta; `BG-C` is untouched
  and remains BLOCKED.

No prior ratification is rewritten, softened, or back-dated.

## 7. Conditions for retesting BG-A and BG-B

Retest only when all of the following hold:

1. `AM1-R01`–`R24` implemented and green, with `R23` (benign quotation) proving
   the fix is not blanket refusal.
2. P1/P2/P3 at all six surfaces produce `SAFE_REFUSED` or `SAFE_CONTAINED`, with
   the stage observation recorded, not just the terminal outcome.
3. The new case bundle reproduces its own digest and the V1 digests are unchanged.
4. `AM1-R25`/`R26` green, so the report's populations reconcile before it is read.
5. Human review remains OPEN: `EV-GATE-12` is not closed by any automated result.

## 8. Human-review and production dependencies that remain OPEN

| Dependency | Status |
|---|---|
| `EV-GATE-01`–`EV-GATE-13` | OPEN (unchanged by this rung) |
| `EV-GATE-12` human review of answer admissibility | OPEN; this amendment adds evidence, does not discharge it |
| `BG-C` operational readiness | BLOCKED |
| Provider/live-model behaviour under the three payloads | NOT TESTED (out of scope by design) |
| Cross-platform hash policy adoption | requires separate scope authorization |
| Windows local-green claim | NOT CLAIMED; 17 failures are understood, not fixed |

## 9. Sequencing for Rung 2

1. IV.5 answer-validation repair (F-01, F-02, F-03) + `AM1-R01`–`R24`.
2. IV.6 scoring/fixture extension (F-05, F-06, F-07) + `AM1-R25`/`R26`.
3. Amended report with reconciled populations and excluded-attack counts.
4. Hash-guard normalization (F-08) **only** if separately authorized; it is
   independent of the security repair and must not gate it.
5. Re-score `BG-A`/`BG-B` under V2, record delta, leave `BG-C` and `EV-GATE-12`
   as they are.
