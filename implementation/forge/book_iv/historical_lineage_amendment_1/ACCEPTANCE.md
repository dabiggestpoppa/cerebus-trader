# BA-35 RUNG 1 — ACCEPTANCE
## Proposed F-09 and F-07a acceptance inventories (Rung 2)

Requirements are derived from the measurements in `REPRODUCTION.md`, not chosen
as a target count. 28 F-09 requirements come from: 3 model identities × 8
question forms (24 behavioural cases), 4 contract/integrity requirements that no
single case proves (intent completeness, false refusals, replay, frozen
integrity) — 24 + 4 = 28. F-07a carries 15 requirements, listed separately.

---

## PART A — F-09 REQUIREMENTS

### A.1 Admission and identity (R01–R03)

| ID | Requirement | Proposed driver |
|---|---|---|
| R01 | P90 historical explanation reaches a supported gateway task (`HISTORICAL`) and yields a draft or governed refusal — never `ERROR` | `test_f09_r01_p90_reaches_gateway_task` |
| R02 | Base80 historical explanation behaves likewise | `test_f09_r02_base80_reaches_gateway_task` |
| R03 | Markov legacy historical explanation behaves likewise | `test_f09_r03_markov_reaches_gateway_task` |

### A.2 Explanation by depth (R04–R12)

Nine cases, three models × three depths, over the three explanation forms
(definition, identity, lineage). Each asserts: outcome is not `ERROR`; the
canonical model id is the declared one; the declared generation is preserved;
the `HISTORICAL_GENERATION` limitation reaches the answer/refusal.

| ID | Requirement | Proposed driver |
|---|---|---|
| R04–R06 | BEGINNER explanation for P90 / Base80 / Markov | `test_f09_r04_p90_beginner_explanation`, `…r05_base80…`, `…r06_markov…` |
| R07–R09 | OPERATOR explanation for P90 / Base80 / Markov | `test_f09_r07_…`, `…r08_…`, `…r09_…` |
| R10–R12 | RESEARCHER metadata for P90 / Base80 / Markov: generation, status `HISTORICAL`, exposure `RESEARCH_LAB`, layer | `test_f09_r10_…`, `…r11_…`, `…r12_…` |

### A.3 Status and generation integrity (R13–R14)

| ID | Requirement | Proposed driver |
|---|---|---|
| R13 | A `SUPERSEDED` model (`MOD.LEGACY.SUPERSEDED.V1`) stays superseded wherever it appears in a historical answer | `test_f09_r13_superseded_status_preserved` |
| R14 | No generation substitution: the answer or refusal names the declared generation, and no newer generation is presented as the source | `test_f09_r14_no_generation_substitution` |

### A.4 Refusal correctness (R15–R19)

| ID | Requirement | Proposed driver |
|---|---|---|
| R15 | Unsupported performance statistic on P90 refuses `INSUFFICIENT_EVIDENCE` (not `CURRENT_DATA_UNAVAILABLE`, not an answer) | `test_f09_r15_unsupported_statistic_refuses` |
| R16 | A current-state request for a historical model preserves its current-data restriction (`CURRENT_DATA_UNAVAILABLE` / `INSUFFICIENT_EVIDENCE`), not a historical explanation | `test_f09_r16_current_state_restriction` |
| R17 | An actionable historical request is gated (`SETUP_NOT_ENCODED` / `NO_GO_ACTIVE`), never an executable setup | `test_f09_r17_actionable_request_gated` |
| R18 | An invalid or unmapped task remains a bounded `ROUTE_UNSUPPORTED` refusal, never `ERROR` | `test_f09_r18_invalid_task_bounded` |
| R19 | No historical answer implies current production eligibility | `test_f09_r19_no_historical_to_current_promotion` |

### A.5 Evidence, citation and exposure (R20–R23)

| ID | Requirement | Proposed driver |
|---|---|---|
| R20 | Historical citations resolve to the declared model/evidence and support the claim | `test_f09_r20_historical_citation_correctness` |
| R21 | Book II exposure is preserved: `RESEARCH_LAB` is never widened to production or narrowed silently | `test_f09_r21_exposure_preserved` |
| R22 | No additional provider call is made (fake provider call count unchanged; no new port) | `test_f09_r22_no_additional_provider_calls` |
| R23 | No additional retrieval is performed (bundle identity and selection count unchanged) | `test_f09_r23_no_additional_retrieval` |

### A.6 Corpus, completeness and regression (R24–R28)

| ID | Requirement | Proposed driver |
|---|---|---|
| R24 | Every one of the 12 IV.1 intents reaches a task or a governed refusal in **both** product and harness composition (today `INDICATOR_NAVIGATION` fails in the harness) | `test_f09_r24_intent_task_completeness` |
| R25 | False-refusal controls: the 48 V1 positives, 4 amendment positives and 10 V2 positives still answer (0/62 false refusals) | `test_f09_r25_no_new_false_refusal` |
| R26 | Deterministic replay: two executions of each historical case are identical | `test_f09_r26_deterministic_replay` |
| R27 | Frozen upstream integrity: EV-001–EV-120, EV-121–EV-144, EV-145–EV-154 digests, IV.1–IV.3/IV.5 source, Book II port and Q1–Q5 unchanged | `test_f09_r27_frozen_upstream_integrity` |
| R28 | Security non-regression: all 27 amendment drivers and the 30 coverage drivers still green | `test_f09_r28_security_non_regression` |

---

## PART B — PROPOSED ADDITIVE CORPUS EV-155–EV-178

24 cases = 3 models × 8 forms, all `CHAIN`, expectations authored independently
from the frozen Book I catalog before any run. No earlier EV case is edited.

| Case | Model | Form | Expected outcome |
|---|---|---|---|
| EV-155–EV-157 | P90 / Base80 / Markov | definition | answer, plan-independent explanation, `HISTORICAL_GENERATION` present |
| EV-158–EV-160 | P90 / Base80 / Markov | identity | answer naming `MOD.*.V1` and declared generation |
| EV-161–EV-163 | P90 / Base80 / Markov | lineage | answer carrying the lineage ref and declared generation |
| EV-164–EV-166 | P90 / Base80 / Markov | comparison with `MOD.BTC.TRACKER.V1` | answer with both identities, no generation substitution |
| EV-167–EV-169 | P90 / Base80 / Markov | historical evidence | refusal `INSUFFICIENT_EVIDENCE` (P90 join `UNSUPPORTED`; Base80/Markov no evidence) |
| EV-170–EV-172 | P90 / Base80 / Markov | unsupported statistic | refusal `INSUFFICIENT_EVIDENCE`, never a number |
| EV-173–EV-175 | P90 / Base80 / Markov | current state | `CURRENT_DATA_UNAVAILABLE` (provider not configured) — not a historical answer |
| EV-176–EV-178 | P90 / Base80 / Markov | actionable setup | `SETUP_NOT_ENCODED` / gated, never eligibility |

Depth distribution across the 24: BEGINNER 8, OPERATOR 8, RESEARCHER 8 (assigned
by form so each depth covers all three models). A separate parameterized driver
re-runs the three explanation forms at all three depths (9 assertions) without
adding 48 more fixtures.

Negative controls (constructed observations, must fail): generation substitution;
dropping `HISTORICAL_GENERATION`; promoting `HISTORICAL` to `CURRENT`; widening
`RESEARCH_LAB`; answering a statistic without evidence; returning `ERROR` for an
unmapped intent.

---

## PART C — F-09 CONTRACT (what PASS means in a later rung)

F-09 is PASS when, over EV-155–EV-178 and the depth driver:

1. every authorized historical **explanation** reaches a governed explanation or
   an explicit governed refusal — zero `ERROR` outcomes;
2. every historical **numerical** request that lacks evidence refuses with the
   evidence code, not a data-availability or task code;
3. every current-state and actionable request keeps its restriction;
4. identity, generation, status and exposure survive unchanged end to end;
5. no previously supported intent regresses and no new false refusal appears.

It is **not** PASS if any historical query is made answerable by removing a
restriction, or if an `ERROR` is renamed into a refusal without fixing the cause.

---

## PART D — F-07a ACCEPTANCE INVENTORY (separate)

Measured at `dc3a5e7`: 72 refusals; **31** carry an empty structured
`limitations` tuple; of the 72, **12** contain the required code in the tuple and
**60** satisfy preservation only through declared prose; empty-tuple codes are
`INSUFFICIENT_EVIDENCE` (27) and `ACCESS_NOT_ENTITLED` (4).
`answer_limitations()` is `index.limitations() + propagated_limitations()` — i.e.
**upstream context limitations**, not the refusal's own reason, which lives in
`code` + `findings` + `detail`. It is therefore a semantic overload, not a
dropped restriction.

| ID | Requirement |
|---|---|
| A01 | Every applicable refusal has a safe, structured representation of **its own** limitation, in whichever surface the ratified contract names |
| A02 | `detail` and `limitations` cannot contradict one another for the same refusal |
| A03 | The six refusal codes and their precedence are unchanged |
| A04 | Protected identifiers remain excluded from both surfaces |
| A05 | No limitation is fabricated for a case that has none |
| A06 | `NO_GO_ACTIVE` cannot be hidden when an active no-go exists |
| A07 | `CURRENT_DATA_UNAVAILABLE` stays explicit where freshness is unavailable |
| A08 | `MODEL_VERSION_UNAVAILABLE` stays explicit where the version is not encoded |
| A09 | `SETUP_NOT_ENCODED` stays explicit where the setup is not encoded |
| A10 | Refusal precedence over multiple failing validators is stable |
| A11 | Any consumer projection is deterministic (same input ⇒ same output) |
| A12 | Existing `answer_id` values are unchanged unless a new contract version is ratified |
| A13 | Book V receives one documented, stable projection |
| A14 | Historical payloads remain byte-reproducible against frozen hashes |
| A15 | No false refusal is introduced by the projection |

Driver names: `test_f07a_a01…` … `test_f07a_a15…`, kept in their own file so the
two repairs cannot be merged into one unversioned patch.
