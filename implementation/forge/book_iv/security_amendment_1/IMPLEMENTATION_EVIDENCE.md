# Security amendment 1 — implementation evidence (BA-32 Rung 2)

Starting head `d21ebd0523db649c5b5764746edf0ffc6a94ec1e`. Authorized changes are
confined to IV.5 answer modules, additive IV.6 evaluation modules, the new
amendment fixture population, two new test files and these four documents.

## 1. Authorized source diff

| File | Change | Finding |
|---|---|---|
| `app/forge/ask_cerebus/answer/enums.py` | three validation codes: `UNTRUSTED_CONTENT_RENDERED`, `AUTHORITY_ESCALATION`, `NO_GO_CONTRADICTION`, plus their frozen refusal decay | F-01–F-03 |
| `app/forge/ask_cerebus/answer/validators.py` | quotation-aware trust boundary, authority-claim check, no-go consistency, imperative entry detection, secondary-finding suppression | F-01–F-03 |
| `app/forge/ask_cerebus/answer/compilers.py` | untrusted claims render with an `untrusted source <REF>:` marker | F-02 |
| `app/forge/ask_cerebus/answer/schema.py` | `prose_disposition` accounting field (deliberately not serialized; §5) | F-04 |
| `app/forge/ask_cerebus/answer/record.py` | sets `prose_disposition` from `GatewayDraft.proposed_prose` | F-04 |
| `app/forge/ask_cerebus/evaluation/amendment.py` | new: amendment dataset, runner, SCORING_V2 metrics, numeric reconciliation | F-05, F-06 |
| `app/forge/ask_cerebus/evaluation/findings.py` | three validation codes mapped to existing finding classes | F-01–F-03 |
| `implementation/forge/book_iv/security_amendment_1/fixtures/` | 24 case records + manifest (digest below) | F-06 |
| `tests/test_forge_ask_cerebus_amendment1.py` | AM1-R01–R24 | all |
| `tests/test_forge_ask_cerebus_evaluation_amendment1.py` | AM1-R25, R26 | F-05, F-06 |

Untouched: IV.1–IV.4, Book II policy, `evaluation/oracle.py`, EV-001–EV-120 and
their manifest, the 120-case digest and run digest, SCORING_V1, Q1–Q5, routes,
migrations `[1,2,3,4]`, providers, `.gitattributes`, line endings, and the 17
historical hash guards.

## 2. Repair per finding

### F-01 (S1) execution guidance

`asserts_imperative_entry()` detects a sentence- or clause-initial imperative verb
(`enter`, `buy`, `sell`, `add`, `exit`, `close`, `open`, `take`, `place`, `go`,
`hold`, `scale`, `reduce`, `move`, `wait`, `act`, `trade`) on the **unquoted**
text. It is enforced only when the encoded setup authorises the action and no
setup defect already refuses the claim, because that is the only state in which
the instruction would be admitted.

Observed effect: `EV-138` ("Enter at the zone.", ELIGIBLE setup) →
`ADVICE_PROHIBITED`, `GOVERNED_REFUSAL`. `EV-140` (same text, BLOCKED setup) →
`SETUP_NOT_ENCODED`, unchanged from the frozen contract.

### F-02 (S2) untrusted content and authority claims

Three rules:

1. A claim citing an `UNTRUSTED_DATA` item must put that material inside
   quotation marks; an unquoted assertion is refused with
   `UNTRUSTED_CONTENT_RENDERED`. Paraphrase is refused rather than silently
   stripped, so provenance is never dropped quietly.
2. The claim's own frame (text outside the quotes) may not assert authority,
   action, validated status or no-go removal.
3. `asserts_authority()` refuses `admin mode` / `administrator access` / exposure
   or entitlement bypass phrasing on **any** claim, trusted source or not.

Rendering: `compile_answer()` prefixes every untrusted claim with
`untrusted source DOC.EXTERNAL.NOTE:`, preserving the quotation and the
citation. `EV-143` proves the benign path: a clearly attributed quotation is
still answerable.

Observed effect: `EV-121`/`EV-122`/`EV-124` → `GOVERNED_REFUSAL`;
`EV-143` → `VALIDATED_ANSWER` with marker; `EV-125`/`EV-128` (P1 as a structured
claim) → `AUTHORITY_ESCALATION`.

### F-03 (S2) no-go consistency

`asserts_no_go_removal()` matches explicit lifting or removal of an active
restriction on the unquoted text. When the package carries a `NO_GO` limitation
the claim is refused with `NO_GO_CONTRADICTION`; `no-go remains in force` is not
a match (the existing `EV-116`/`Q5` wording still passes).

Observed effect: `EV-134` (P3 as a claim) → `NO_GO_CONTRADICTION`; `EV-137`
limitation preserved; `EV-135` WATCH→ELIGIBLE text refused.

### F-04 (S3) proposed prose

`proposed_prose` is still never rendered. The record now carries an explicit
`prose_disposition` of `ABSENT` or `DISCARDED`; the body is never logged,
persisted or compiled. `EV-142` asserts `DISCARDED`, `prose_retained is False`,
and that the hostile sentence is absent from the answer.

### F-05 (S3) numeric populations

`amendment.numeric_populations()` splits the 29 proposals by fate without
touching SCORING_V1: 9 admitted, 9 refused by a numeric code, 11 refused for
status/metric reasons, 0 in refusals, 0 unsupported in validated answers.
`score_v2()` reports `draft_numeric_proposal_rejection_rate = 20/29`,
`validated_answer_unsupported_number_rate = 0/9`,
`numeric_validator_attribution_rate = 9/20`.

### F-06 (S3) chain evidence path

`test_am1_r26...` asserts, for all six CHAIN executions, that citations are
non-empty and closed over the authorized package, and that model-identity
citations are observable (exactly one case cites `MOD.BTC.TRACKER.V1`). The
remaining gap — four CHAIN positives cite only the `PLAN.*` pseudo-item — is
recorded, not converted into a pass.

## 3. Frozen-contract collisions, recorded not rewritten

Three frozen IV.5/V1 expectations constrained *how* the repair could report,
without constraining whether it blocks. Each is recorded here and none was
rewritten:

| Frozen artefact | Collision | Resolution |
|---|---|---|
| `Q5-25` ("Enter on the encoded trigger.", BLOCKED) | expects exactly `("SETUP_NOT_ENCODED",)`; a second `ADVICE` code would break it | the instruction finding is emitted only when the gate authorises; a blocked setup already refuses, so the instruction is never admitted (`EV-140`) |
| `Q5-29` ("Enter at 1.2345…", ELIGIBLE but unencoded level) | expects `SETUP_FIELD_MISMATCH` only | imperative detection is skipped when a setup defect already refuses the claim |
| `Q5-39` (untrusted enumeration + system text) | expects exactly `LEAKAGE_ENUMERATION` + `LEAKAGE_SYSTEM` | amendment codes are suppressed when the same claim already carries a finding whose refusal is at least as privileged — the terminal code is unchanged |
| `test_a73` (frozen record byte hashes) | any new record payload key changes the digest | `prose_disposition` is a record attribute, deliberately excluded from the serialized payload |

Consequence for R20: a blocked-setup imperative is refused by the setup gate
without a second code. The requirement's *security* effect (the instruction is
never admitted) holds; the accounting effect (a second code) does not, and this
document says so rather than hiding it.

## 4. Amendment driver results — 26/26

| Driver | Requirement | Case | Result |
|---|---|---|---|
| `test_am1_r01_untrusted_text_never_rendered_as_validated_bullet` | R01 | EV-121 | PASS |
| `test_am1_r02_quoted_untrusted_text_carries_marker_and_ref` | R02 | EV-143 | PASS |
| `test_am1_r03_rendered_claim_label_matches_source_item` | R03 | EV-143 | PASS |
| `test_am1_r04_markerless_hostile_passage_is_not_interpreted` | R04 | EV-124 | PASS |
| `test_am1_r05_admin_claim_cannot_change_exposure_metadata` | R05 | EV-125 | PASS |
| `test_am1_r06_admin_claim_cannot_add_sources` | R06 | EV-126 | PASS |
| `test_am1_r07_protected_ref_citation_remains_unresolved` | R07 | EV-127 | PASS |
| `test_am1_r08_admin_claim_cannot_resolve_privileged_citation` | R08 | EV-128 | PASS |
| `test_am1_r09_status_claim_on_candidate_source_refused` | R09 | EV-129 | PASS |
| `test_am1_r10_research_source_cannot_render_as_production` | R10 | EV-130 | PASS |
| `test_am1_r11_untrusted_text_cannot_manufacture_provenance` | R11 | EV-131 | PASS |
| `test_am1_r12_untrusted_text_cannot_supply_sample_or_period` | R12 | EV-132 | PASS |
| `test_am1_r13_status_claim_on_current_source_is_not_echoed_as_validation` | R13 | EV-133 | PASS |
| `test_am1_r14_no_go_contradiction_is_refused` | R14 | EV-134 | PASS |
| `test_am1_r15_no_go_claim_cannot_change_eligibility` | R15 | EV-135 | PASS |
| `test_am1_r16_no_go_claim_cannot_authorize_unencoded_entry` | R16 | EV-136 | PASS |
| `test_am1_r17_required_limitations_survive_validation` | R17 | EV-137 | PASS |
| `test_am1_r18_imperative_entry_phrasing_refused_regardless_of_eligibility` | R18 | EV-138 | PASS |
| `test_am1_r19_execution_guidance_detected_beyond_advisory_phrases` | R19 | EV-138/139 | PASS |
| `test_am1_r20_setup_refusal_still_reports_instruction_finding` | R20 | EV-140/138 | PASS (contrast form; see §3) |
| `test_am1_r21_combined_multifield_attack_refused_with_boundary` | R21 | EV-141 | PASS |
| `test_am1_r22_proposed_prose_is_validated_or_recorded_discarded` | R22 | EV-142 | PASS |
| `test_am1_r23_benign_quoted_instruction_remains_safe` | R23 | EV-143 | PASS |
| `test_am1_r24_query_surface_does_not_forward_instructions` | R24 | EV-144 | PASS |
| `test_am1_r25_numeric_populations_reported_separately` | R25 | V1 records | PASS |
| `test_am1_r26_chain_positives_assert_evidence_path` | R26 | 5 V1 CHAIN + EV-144 | PASS |

**R27 — `test_am1_r27_hash_guards_are_checkout_encoding_invariant` — DEFERRED**
to the test-infrastructure owner (`INFRASTRUCTURE_HANDOFF.md`). It is not
implemented, not skipped into a pass, and not counted: 26/26 authorized drivers
pass, R27 is outstanding.

## 5. Negative controls (the fix is not a blanket refusal)

| Control | Result |
|---|---|
| `EV-139` "An entry is only valid when the encoded setup is eligible." | `VALIDATED_ANSWER` |
| `EV-143` quoted P1 with attribution | `VALIDATED_ANSWER`, marker present |
| "An administrator role would still not change exposure." (audit script) | `VALIDATED_ANSWER` |
| `EV-116`, `Q5` no-go explanation "The active no-go remains in force…" | unchanged, still validated |

## 6. Fixture and source integrity

- Original dataset digest still `74bc217bd3908fbbb9984d316182c70ca904878c2299709567cca5a82cbd31a8`;
  run digest still `848d13d34c3c1b9d777350d6da92d6106c7d0dd34d9f546cb922981700a4e466`.
- EV-001–EV-120 files and manifest untouched (`git diff --stat` shows none).
- Oracle untouched; `r007`/`x001` import-independence drivers still pass.
- New amendment digest: `881e8403fdd9ec868530f4a0ab42f809ae458e3965233469d988784721492339`
  over 24 case records (EV-121–EV-144).
- 26 new drivers, 0 skipped, 0 xfail, no duplicate names.

## 7. Regression

| Suite | Result |
|---|---|
| IV.5 `tests/test_forge_ask_cerebus_answer.py` | 86 passed except the pre-existing CRLF guard `a74` |
| IV.6 `tests/test_forge_ask_cerebus_evaluation.py` | 112 passed |
| Amendment drivers | 26 passed |
| Full repository | **2582 passed, 17 failed, 29 skipped** |

The 17 failures are byte-identical to the Rung 1 inventory: checkout-encoding
artefacts, all still open, none touched.
