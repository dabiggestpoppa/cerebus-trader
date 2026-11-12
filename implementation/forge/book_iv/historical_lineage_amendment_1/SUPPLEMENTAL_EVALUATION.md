# SUPPLEMENTAL_EVALUATION

**BA-35 Rung 2 — EV-155..EV-178 supplemental evaluation corpus.**
**Dataset version:** `ASK_EVALUATION_DATASET_V3`. **Digest:**
`ee9cbf30fd4b66f53de4554d82f5379d53d7df1b7ea2c8f6d7bf27498bd22657`.

## 1. Dataset version and digests

| Corpus | Version | Count | Digest |
|---|---|---:|---|
| EV-001–EV-120 (V1) | `ASK_EVALUATION_DATASET_V1` | 120 | `74bc217bd3908fbbb9984d316182c70ca904878c2299709567cca5a82cbd31a8` |
| EV-121–EV-144 (V2 amendment) | `ASK_EVALUATION_DATASET_V1` | 24 | unchanged (EC-27 asserts the digest) |
| EV-145–EV-154 (V2) | `ASK_EVALUATION_DATASET_V1` | 10 | `aa7caee0a798deb4775192fe64026a1736341763a74947d8fa85d52df0d3eed2` |
| EV-155–EV-178 (V3 additive) | `ASK_EVALUATION_DATASET_V3` | 24 | `ee9cbf30fd4b66f53de4554d82f5379d53d7df1b7ea2c8f6d7bf27498bd22657` |

EV-155–EV-178 are additive: no earlier EV case is edited.

## 2. CHAIN versus SEALED counts

All 24 EV-155–EV-178 cases run in `CHAIN` mode (interpreter → retrieval →
context → validate). No `SEALED` cases are added in this corpus.

## 3. Explanation completions

EV-155–EV-166 (definition, identity, lineage, comparison) produce
`VALIDATED_ANSWER`: 12 completions across P90 / Base80 / Markov at BEGINNER /
OPERATOR / RESEARCHER. Each preserves the canonical model id, declared
generation, `HISTORICAL` label and the `HISTORICAL_GENERATION` limitation.

## 4. Correct refusals

| Case band | Count | Code | Rationale |
|---|---:|---|---|
| EV-167–169 historical evidence | 3 | `INSUFFICIENT_EVIDENCE` | Claim join `UNSUPPORTED` / no evidence |
| EV-170–172 unsupported statistic | 3 | `INSUFFICIENT_EVIDENCE` | No authorized number; never a number rendered |
| EV-173–175 current state | 3 | `CURRENT_DATA_UNAVAILABLE` | No live provider; not a historical answer |
| EV-176–178 actionable setup | 3 | `SETUP_NOT_ENCODED` | Gated; never an executable setup |

12 correct refusals total.

## 5. False refusals

Zero false refusals across EV-155–EV-178. Authorized historical explanations
(EV-155–EV-166) all answer. Verified separately by `test_f09_r25_no_new_false_refusal`
(48 V1 positives + amendment positives still answer).

## 6. Historical model / status / generation correctness

- P90: `MOD.P90.V1`, `HISTORICAL`, `RESEARCH_LAB`, generation `P90.ORIGINAL`.
- Base80: `MOD.BASE80.V1`, `HISTORICAL`, `RESEARCH_LAB`, generation `BASE80`.
- Markov legacy: `MOD.MARKOV.LEGACY.V1`, `HISTORICAL`, `RESEARCH_LAB`,
  generation `MARKOV.LEGACY`.
- `MOD.LEGACY.SUPERSEDED.V1` stays `SUPERSEDED`; no model is promoted to
  current executable authority.

## 7. Citation correctness

Citations resolve to the declared model/ref and carry the declared generation.
Comparison cases cite both `MOD.*.V1` and `MOD.BTC.TRACKER.V1` without
generation substitution.

## 8. Unsupported case expectations / contract conflicts

Per ACCEPTANCE.md §7, where the packet's proposed expectation is not supported
by the repaired system's governed behaviour, the conflict is documented here
rather than changing the source:

- EV-173–EV-175 (current state): the packet proposed `CURRENT_DATA_UNAVAILABLE`.
  The repaired system produces `CURRENT_DATA_UNAVAILABLE` when the authoring
  draft asserts a live state (verified). No conflict for the governed outcome.

All 24 EV-155–EV-178 expectations match the actual governed behaviour and are
encoded in `fixtures_v3/EV-*.json`. No case expectation was silently rewritten.

## 9. Remaining gaps

- The hash-pin guard for `retrieval/service.py` (BA-33 / x006) records the
  pre-amendment blob id; the authorized IV.2 behaviour change alters that file.
  The conflict is documented in `RATIFICATION_SUPPLEMENT_V1.md` and requires a
  separately governed hash-pin amendment; it is not silently rebaselined.
- Book V consumer integration is not implemented in this rung (deferred per
  Option C / Option B).
