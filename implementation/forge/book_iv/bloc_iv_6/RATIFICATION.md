# IV.6 — Ratification

## 1. What is ratified

Rung 2 of Bloc IV.6 is ratified as **delivered and evidenced**, at the head that
carries this file:

- the evaluation contract and its five independently versioned sub-contracts;
- the frozen 120-case corpus (`EV-001`–`EV-120`) with dataset digest
  `74bc217bd3908fbbb9984d316182c70ca904878c2299709567cca5a82cbd31a8`;
- the independent oracle (no import of `interpreter`, `retrieval`, `context`,
  `llm_gateway` or `answer`, enforced by AST inspection in `test_r007` and
  `test_x001`);
- the two-mode harness (CHAIN over the real public composition, SEALED over the
  frozen package) with no network call;
- all 20 declared metrics with numerator, denominator, eligible population and an
  honest non-applicable path;
- the red-team boundary classifier and its attribution owners;
- the 102 requirement implementations and the 112 dedicated drivers;
- the regression impact map, upstream pin check and replay equality.

## 2. The three verdicts, kept separate

| Gate | Verdict | Meaning |
|---|---|---|
| `BG-A` | **PASS** | the evaluation package executes every case at one head with no stage exception |
| `BG-B` | **PASS** | over the frozen corpus, authorization, source identity, numerical truth, no-go and validated-answer semantics hold with zero S1 findings and zero false refusals |
| `BG-C` | **BLOCKED** | provider, privacy, live data, entitlement, history, abuse controls and thresholds are absent and unratified |

`BG-A` and `BG-B` are deterministic-fixture results. They are not production
readiness and are not a launch decision. `BG-C` cannot pass in this rung and no
attempt was made to close it by fixture success.

## 3. What this ratification does not claim

1. It does not claim the IV.5 injection filter is complete. Three probe payloads
   were not refused by any existing control and were reduced to their recognised
   forms; see `EVIDENCE.md` §5.1.
2. It does not claim cross-session or cross-request extraction control
   (`EV-GATE-06`), commercial entitlement (`EV-GATE-04`), live current-state
   evaluation (`EV-GATE-07`) or durable replay (`EV-GATE-08`).
3. It does not ratify a false-refusal threshold, a materiality/cutoff policy, a
   citation-surface contract or refusal-precedence authority
   (`EV-GATE-02`, `03`, `11`, `13`).
4. It does not claim human review occurred; `human_review_agreement` is
   `BLOCKED` with an empty review set (`EV-GATE-12`).
5. It does not claim semantic retrieval or provider quality; CHAIN cases run on
   deterministic fakes and assert composition, not recall.

## 4. Frozen-integrity attestation

- Books I–III and IV.1–IV.5 are unmodified. The ten pinned upstream blobs are
  reproduced by `git hash-object` semantics in `test_x006`; all ten match.
- `app/forge/service/routes.py` and `app/forge/policy.py` are unchanged and are
  both pinned; no route was added (`test_x010`).
- The four SQL migrations are exactly `001`–`004`; none was added or edited.
- No provider configuration, no real LLM call, no live market data, no Book V UI
  and no Book VI entitlement code was touched.

## 5. Finding register

No S1, S2, S3 or S4 finding is open against the frozen corpus at this head. The
gaps listed in §3 are external dependencies recorded as open gates, not
evaluation findings, and each names its owner in `FEASIBILITY_GATE.md`.

## 6. Ratification statement

Bloc IV.6 is ratified as **evaluation infrastructure complete and internally
consistent**, with `BG-A` `PASS` and `BG-B` `PASS` on frozen fixtures, and with
`BG-C` deliberately `BLOCKED`. Release of ASK CEREBUS remains governed by
`EV-GATE-01`–`EV-GATE-13`; a green deterministic corpus is evidence about the
measuring instrument, never permission to ship.
