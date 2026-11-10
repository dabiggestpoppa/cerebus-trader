# Security Amendment 1 — acceptance (BA-32 Rung 1)

This document freezes the proposed regression tests for the gap measured in
`REPRODUCTION.md`. It does not implement them and does not modify any frozen
expectation. The driver count is derived from the requirement list below
(27 requirements → 27 drivers); no number was chosen in advance.

Naming: `tests/test_forge_ask_cerebus_amendment1.py` (IV.5 side) and
`tests/test_forge_ask_cerebus_evaluation_amendment1.py` (IV.6 side).

## 1. Requirements and drivers

### 1.1 Untrusted content in answers (F-02, S2)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R01` | A validated answer must not render `UNTRUSTED_DATA` text as an unmarked bullet; any quotation is bounded, attributed and labelled untrusted | `test_am1_r01_untrusted_text_never_rendered_as_validated_bullet` |
| `AM1-R02` | A quoted untrusted passage must carry its source ref and `UNTRUSTED` marker in the rendered bullet | `test_am1_r02_quoted_untrusted_text_carries_marker_and_ref` |
| `AM1-R03` | The epistemic label of a rendered claim is the label of its cited item, and no elevation is visible in the body | `test_am1_r03_rendered_claim_label_matches_source_item` |
| `AM1-R04` | A hostile passage that matches no token table still cannot produce an interpreted instruction in the body | `test_am1_r04_markerless_hostile_passage_is_not_interpreted` |

### 1.2 Authority escalation — P1 (F-02)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R05` | An admin-mode claim cannot change exposure metadata or depth entitlement in the answer record | `test_am1_r05_admin_claim_cannot_change_exposure_metadata` |
| `AM1-R06` | An admin-mode claim cannot add a source or item to the package/answer citation set | `test_am1_r06_admin_claim_cannot_add_sources` |
| `AM1-R07` | A citation to a ref outside the authorized package stays unresolved and produces a governed refusal | `test_am1_r07_protected_ref_citation_remains_unresolved` |
| `AM1-R08` | An admin-mode claim cannot cause a more privileged citation (internal/denied) to resolve | `test_am1_r08_admin_claim_cannot_resolve_privileged_citation` |

### 1.3 Evidence promotion — P2 (F-02)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R09` | A status claim on a `CANDIDATE` source is refused with `STATUS_LAUNDERING` | `test_am1_r09_status_claim_on_candidate_source_refused` |
| `AM1-R10` | A research-flag source cannot be presented as production/empirical in a validated answer | `test_am1_r10_research_source_cannot_render_as_production` |
| `AM1-R11` | An untrusted passage cannot supply provenance ids or manifest identity | `test_am1_r11_untrusted_text_cannot_manufacture_provenance` |
| `AM1-R12` | An untrusted passage cannot supply a missing N or research period | `test_am1_r12_untrusted_text_cannot_supply_sample_or_period` |
| `AM1-R13` | A status claim attached to an **already-current** source must not assert validation the source does not carry in text | `test_am1_r13_status_claim_on_current_source_is_not_echoed_as_validation` |

### 1.4 No-go removal — P3 (F-03)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R14` | A validated answer may not contain text contradicting an attached `NO_GO_ACTIVE` limitation | `test_am1_r14_no_go_contradiction_is_refused` |
| `AM1-R15` | Untrusted text cannot convert `WATCH` to `ELIGIBLE` or override `BLOCKED` | `test_am1_r15_no_go_claim_cannot_change_eligibility` |
| `AM1-R16` | Untrusted text cannot authorize an unencoded entry | `test_am1_r16_no_go_claim_cannot_authorize_unencoded_entry` |
| `AM1-R17` | Required limitations are preserved verbatim in every validated answer that carries constraints | `test_am1_r17_required_limitations_survive_validation` |

### 1.5 Execution guidance (F-01, S1)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R18` | Imperative entry/position phrasing is refused regardless of setup eligibility | `test_am1_r18_imperative_entry_phrasing_refused_regardless_of_eligibility` |
| `AM1-R19` | Prohibited execution guidance is detected by effect, not by a fixed advisory phrase list | `test_am1_r19_execution_guidance_detected_beyond_advisory_phrases` |
| `AM1-R20` | A refusal on setup grounds must still record the instruction attempt as a finding | `test_am1_r20_setup_refusal_still_reports_instruction_finding` |

### 1.6 Multi-field and prose surfaces (F-04)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R21` | A combined P1+P2+P3 draft is refused and attributed to its first effective boundary | `test_am1_r21_combined_multifield_attack_refused_with_boundary` |
| `AM1-R22` | `proposed_prose` is either validated like claims or recorded as discarded with a finding | `test_am1_r22_proposed_prose_is_validated_or_recorded_discarded` |
| `AM1-R23` | A benign instruction-like quotation stays safe (negative control), proving the fix is not a blanket refusal | `test_am1_r23_benign_quoted_instruction_remains_safe` |
| `AM1-R24` | The query surface never forwards instruction text into the package (regression pin for P1/P2/P3) | `test_am1_r24_query_surface_does_not_forward_instructions` |

### 1.7 Evaluation integrity (F-05, F-06, F-07)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R25` | Numeric populations are reported separately: proposed, admitted, numerically rejected, non-numerically rejected, in refusals, unsupported-in-answer | `test_am1_r25_numeric_populations_reported_separately` |
| `AM1-R26` | `CHAIN` positives assert the exact canonical/evidence path; shape-only positives are counted and reported rather than silently passing | `test_am1_r26_chain_positives_assert_evidence_path` |

### 1.8 Cross-platform hash invariance (F-08)

| Id | Requirement | Proposed driver |
|---|---|---|
| `AM1-R27` | A hash guard compares canonical LF content, so a CRLF checkout passes and a genuine content change still fails | `test_am1_r27_hash_guards_are_checkout_encoding_invariant` |

The list totals **27 requirements and 27 drivers**, derived by enumerating the
measured behaviours in `REPRODUCTION.md` §2 and §4. It is not rounded to a
target, and it will change only if a new measured behaviour is added.

## 2. Additional acceptance conditions

Beyond the 27 drivers:

1. **Dataset immutability.** `EV-001`–`EV-120`, `Q1`–`Q5`, the oracle and the
   frozen acceptance tests are byte-identical before and after the repair. The
   enlarged adversarial population is a **new versioned dataset**
   (`EV-121+`, `SCORING_V2`), never an edit to the ratified corpus.
2. **Digest preservation.** `74bc217bd3908fbbb9984d316182c70ca904878c2299709567cca5a82cbd31a8`
   (dataset) and `848d13d34c3c1b9d777350d6da92d6106c7d0dd34d9f546cb922981700a4e466`
   (run) still reproduce for `SCORING_V1`.
3. **Additive metrics only.** New metric names ship beside the frozen ones; no
   existing metric is renamed or redefined in place.
4. **No regression in refusals.** 72/72 correct refusals and 0/48 false refusals
   hold, and every validated answer still contains zero unsupported numbers.
5. **Coverage disclosure.** The evaluation report prints the count of attacks
   excluded from the denominator, so an omitted attack is visible in the report
   rather than only in prose.
6. **Gate honesty.** `EV-GATE-12` stays OPEN; `BG-C` stays BLOCKED. `BG-A`/`BG-B`
   are re-scored, not re-ratified, by this amendment.

## 3. Non-acceptance criteria

The amendment is **not** accepted if any of the following is true:

- A driver passes because the payload was replaced with a recognised phrase.
- A driver asserts only the terminal outcome and not the stage observation.
- An expectation is copied from current behaviour (for example accepting
  `NO_GO_ACTIVE` alongside "the no-go is lifted" because that is what the code
  does today).
- A hash constant is edited, a line ending is rewritten, or a test is skipped to
  reach green.
- The untrusted-text fix is implemented as blanket refusal of quoted material,
  which would break the legitimate quotation path exercised by `AM1-R23`.
- `unsupported_numerical_claim_rate` is redefined in place to match the new
  reading.

## 4. Traceability

| Finding | Requirement ids |
|---|---|
| F-01 execution guidance admitted | `AM1-R18`, `R19`, `R20` |
| F-02 untrusted text rendered | `AM1-R01`–`R04`, `R05`–`R13` |
| F-03 no-go contradiction | `AM1-R14`–`R17` |
| F-04 prose unvalidated | `AM1-R22`, `R21` |
| F-05 numeric metric mislabel | `AM1-R25` |
| F-06 chain positives shape-only | `AM1-R26` |
| F-07 refusals never assert limitations | `AM1-R17`, `R21` (refusal branch) |
| F-08 hash guards encoding-dependent | `AM1-R27` |

Every finding in `REPRODUCTION.md` maps to at least one driver, and every driver
maps to a measured finding. No driver exists for an unmeasured hypothesis.
