# Security amendment 1 — ratification supplement V1

**Outcome: PARTIAL.**

The F-01–F-07 corrective implementation is complete, tested and ratified for the
scope authorized in this rung. AM1-R27 (cross-platform hash-guard invariance) is
**not implemented** and remains with the test-infrastructure owner. F-08 is
**OPEN**. No statement in this document may be read as 27/27, as a Windows
full-suite pass, or as operational readiness.

Ratified head: the commit ladder in §7. Ratified scope: F-01–F-07, AM1-R01–R26.

## 1. What is ratified

| Item | Status |
|---|---|
| F-01 execution-guidance prohibition (S1) | **REPAIRED** — refused under `ADVICE_PROHIBITED` at every encoded setup state where it could otherwise be admitted |
| F-02 untrusted rendering / authority escalation (S2) | **REPAIRED** — quotation-only, marker on render, unquoted assertion refused |
| F-03 no-go consistency (S2) | **REPAIRED** — `NO_GO_CONTRADICTION` whenever an active no-go is contradicted |
| F-04 proposed-prose disposition (S3) | **REPAIRED** — `DISCARDED` recorded, body never rendered, logged or persisted |
| F-05 numeric population ambiguity (S3) | **REPAIRED** — six separated populations, additive SCORING_V2, frozen SCORING_V1 intact |
| F-06 CHAIN evidence path (S3) | **PARTIAL** — path closure and model-identity observability asserted; per-case model-path expectations for four V1 positives remain unauthored |
| F-07 refusal/limitation coverage (S4) | **PARTIAL** — asserted for the amendment population (EV-137 and 18/18 no-go-carrying refusals); the frozen 72 V1 refusals still assert none and were not rewritten |
| F-08 checkout-encoding hash guards (S4) | **OPEN** — deferred, see `INFRASTRUCTURE_HANDOFF.md` |

## 2. What is explicitly not ratified

- 27/27 amendment requirements. Only 26 are authorized and 26 pass.
- Any Windows or cross-platform green regression. 17 guards still fail on a CRLF
  checkout; the same head passes them on an LF worktree.
- BG-C operational readiness, any `EV-GATE-01`–`13` closure, `EV-GATE-12` human
  review, provider or market-data readiness, entitlement or retention policy.
- Any claim that the original probe bytes were recovered. All three are
  `RECONSTRUCTED_FROM_RECORDED_MEANING`.
- Any reinterpretation of the historical `20/29` draft-numeric figure as a
  final-answer hallucination rate.
- Book V UI, production LLM use, or live market data.

## 3. Evidence basis

- `IMPLEMENTATION_EVIDENCE.md` — authorized diff, per-finding repair, 26 drivers,
  negative controls, frozen-collision register.
- `SUPPLEMENTAL_EVALUATION.md` — 24-case population, digests, numeric
  reconciliation, boundary attribution, residual coverage limits, BG-A/BG-B/BG-C.
- `INFRASTRUCTURE_HANDOFF.md` — the 17-test inventory and the canonical-hashing
  specification.

Verification commands actually run on the ratified head:

```
python -m pytest tests/test_forge_ask_cerebus_answer.py \
                 tests/test_forge_ask_cerebus_evaluation.py -q   -> 197 passed, 1 failed (a74)
python -m pytest tests/test_forge_ask_cerebus_amendment1.py \
                 tests/test_forge_ask_cerebus_evaluation_amendment1.py -q -> 26 passed
python -m pytest -q                                              -> 2582 passed, 17 failed, 29 skipped
```

The single `a74` failure and the 17 full-suite failures are the same
checkout-encoding artefacts inventoried in Rung 1; no new failure was introduced.

## 4. Severity and ownership (unchanged)

| Finding | Severity | Owner | State |
|---|---|---|---|
| F-01 | S1 | IV.5 | REPAIRED |
| F-02 | S2 | IV.5 | REPAIRED |
| F-03 | S2 | IV.5 | REPAIRED |
| F-04 | S3 | IV.5 | REPAIRED |
| F-05 | S3 | IV.6 | REPAIRED |
| F-06 | S3 | IV.6 | PARTIAL |
| F-07 | S4 | IV.6 | PARTIAL |
| F-08 | S4 | Test infrastructure | OPEN |

F-01 remains S1. It was a categorical-prohibition breach that was not an observed
privilege bypass; the severity is not lowered because the repair passed.

## 5. Historical records preserved

V1 keeps its own verdict for its own population: 0 attack successes across 21
attack cases, the 120-case digest and the ratified run digest unchanged. The three
held-out probes were outside that population; the original ratification is not
edited, only supplemented. One unsafe acceptance was found inside V1's
population — a draft numeric claim the IV.5 numerical codes refused for a
different reason than intended — and that is recorded as a repair effect in
`IMPLEMENTATION_EVIDENCE.md` §3 rather than as a change to any V1 result.

## 6. Basis for PARTIAL

A single outstanding binding requirement is sufficient. R27 is outstanding because
the 17 historical guards compare byte content, so a CRLF checkout changes their
identity without changing governed content; repairing that is a test-infrastructure
change of control, not a security repair, and this rung is expressly forbidden
from touching those tests, the baselines, `.gitattributes` or global line endings.

## 7. Commit ladder for this ratification

| Stage | Content |
|---|---|
| 1 | held-out case definitions and fixtures (EV-121–EV-144 + manifest) |
| 2 | IV.5 answer-boundary repairs |
| 3 | additive IV.6 evaluation extension and SCORING_V2 |
| 4 | 26 amendment drivers |
| 5 | (no separate root-cause repair was required; none of the authorized defences needed a follow-up fix) |
| 6 | implementation evidence and supplemental evaluation |
| 7 | infrastructure handoff |
| 8 | final-head CI receipt |

Append-only; fast-forward push; no amend, squash, rebase, reset or force.
