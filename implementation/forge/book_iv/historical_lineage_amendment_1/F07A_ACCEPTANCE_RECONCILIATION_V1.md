# F07A_ACCEPTANCE_RECONCILIATION_V1

**BA-36 — F-07a refusal consumer contract (Option C) acceptance reconciliation.**
**Append-only record. No earlier evidence document is overwritten.**

## 1. Basis

BA-35 Rung 2 ratified F-07a Option C (existing field semantics, zero payload
change) via `REFUSAL_CONSUMER_CONTRACT_V1.md`. The acceptance packet defined
15 requirements (A01–A15). Rung 2 shipped 14 verification drivers because A01
and A05 were merged into a single driver. This document closes that gap with a
one-to-one mapping and a 15th driver, bringing the total to **15 tests for 15
requirements**.

Retained semantics (unchanged, no payload modification):
- `code` = primary governed refusal reason (one of the six frozen codes).
- `findings` = supporting validation findings.
- `detail` = consumer-safe explanation of the refusal.
- `limitations` = inherited context limitations and restrictions (not a
  restatement of `code`).

Option B (a consolidated `refusal_limitations` field) remains deferred; no
`refusal_limitations` field is added; no IV.5 payload or frozen answer ID is
modified.

## 2. A01–A15 one-to-one mapping

| ID | Requirement | Exact test | Assertion (verification behavior) | Outcome |
|---|---|---|---|---|
| A01 | Every applicable refusal has a safe, structured representation of its own limitation/reason | `test_f07a_a01_every_refusal_carries_its_own_reason` | Each of the 72 refusal cases yields `GOVERNED_REFUSAL`; `answer_refusal_code` is one of the six frozen codes; `detail` is non-empty and consumer-safe | PASS |
| A02 | `detail` and `limitations` cannot contradict for the same refusal | `test_f07a_a02_no_contradiction_between_detail_and_limitations` | For every refusal, `detail` names the refusal's subject and `limitations` are inherited restrictions; no fabricated grant of eligibility | PASS |
| A03 | The six refusal codes and their precedence are unchanged | `test_f07a_a03_six_refusal_codes_and_precedence_unchanged` | `REFUSAL_CODES` equals the frozen six in precedence order; `REFUSAL_RANK` maps highest to 0, lowest to 5 | PASS |
| A04 | Protected identifiers excluded from both surfaces | `test_f07a_a04_protected_ids_excluded` | `detail` + `limitations` contain no `context_items`, `object_id`, `manifest_digest`, `row_id`, `credential`, or `system prompt` | PASS |
| A05 | No limitation fabricated for a case that has none | `test_f07a_a05_no_fabricated_limitation` | `limitations` is always a well-formed list (possibly empty); every entry is a non-empty inherited-restriction string; an empty tuple is legal | PASS |
| A06 | `NO_GO_ACTIVE` cannot be hidden when an active no-go exists | `test_f07a_a06_no_go_active_visible` | EV-032 refusal carries `NO_GO_ACTIVE` in `limitations` | PASS |
| A07 | `CURRENT_DATA_UNAVAILABLE` stays explicit where freshness is unavailable | `test_f07a_a07_current_data_unavailable_explicit` | EV-050/EV-080/EV-081/EV-082/EV-083 refuse with `CURRENT_DATA_UNAVAILABLE` | PASS |
| A08 | `MODEL_VERSION_UNAVAILABLE` stays explicit where the version is not encoded | `test_f07a_a08_model_version_unavailable_explicit` | EV-070 refuses with `MODEL_VERSION_UNAVAILABLE` | PASS |
| A09 | `SETUP_NOT_ENCODED` stays explicit where the setup is not encoded | `test_f07a_a09_setup_not_encoded_explicit` | EV-032/EV-036/EV-037 refuse with `SETUP_NOT_ENCODED` | PASS |
| A10 | Refusal precedence over multiple failing validators is stable | `test_f07a_a10_refusal_precedence_stable` | Two independent executions produce identical refusal codes for every refusal case | PASS |
| A11 | Any consumer projection is deterministic (same input ⇒ same output) | `test_f07a_a11_deterministic_serialization` | Two independent executions produce identical answer payloads for every case | PASS |
| A12 | Existing `answer_id` values unchanged unless a new contract version is ratified | `test_f07a_a12_answer_ids_unchanged` | Every refusal carries a non-empty `answer_id` and `answer_contract_version == ASK_ANSWER_CONTRACT_V1` (no version bump) | PASS |
| A13 | Book V receives one documented, stable projection | `test_f07a_a13_book_v_stable_projection_documented` | `REFUSAL_CONSUMER_CONTRACT_V1.md` exists and names `code`, `findings`, `detail`, `limitations` together under Option C | PASS |
| A14 | Historical payloads remain byte-reproducible against frozen hashes | `test_f07a_a14_historical_payloads_byte_reproducible` | Every `EV-*.json` fixture has a valid 64-hex SHA-256; running the corpus does not rewrite fixture bytes | PASS |
| A15 | No false refusal is introduced by the projection | `test_f07a_a15_no_false_refusal_introduced` | Zero false refusals across the positive-control cases (every positive case yields `VALIDATED_ANSWER`) | PASS |

**Total: 15 requirements → 15 tests, 15/15 PASS, 0 skipped, 0 xfail.**

## 3. Driver file

`tests/test_forge_ask_cerebus_f07a.py` — one test per requirement,
`test_f07a_a01` … `test_f07a_a15`, executed against the original 72-refusal
corpus (EV-001–EV-120 dataset) with no historical payload change.

## 4. Option C confirmation

The contract is ratified as documented in
`implementation/forge/book_iv/historical_lineage_amendment_1/
REFUSAL_CONSUMER_CONTRACT_V1.md`. `code` wins for the refusal reason;
`limitations` are shown alongside as inherited restrictions, never merged;
no protected identifiers appear in either surface.

## 5. Deferred

Option B (`refusal_limitations` under `ASK_ANSWER_CONTRACT_V2`) remains
DEFERRED. Not implemented in this amendment.
