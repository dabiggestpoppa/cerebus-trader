# REFUSAL_CONSUMER_CONTRACT_V1

**Ratified contract for the `GovernedAnswerRefusal` consumer surface (F-07a, Option C).**

**Status:** Ratified for BA-35 Rung 2. Zero payload change. Option B
(`refusal_limitations`) remains DEFERRED; `ASK_ANSWER_CONTRACT_V2` is not
implemented.

## 1. Purpose

A governed refusal is a terminal, lawful outcome: the system declines to
answer and says why. Book V (and any future consumer) must read a refusal as a
single governed record composed of four surfaces, never as a single field.

This contract ratifies the existing `app.forge.ask_cerebus.answer.schema`
semantics with no modification to `GovernedAnswerRefusal`, the IV.5 schema,
the IV.5 refusal serializer, frozen answer IDs, historical refusal payloads or
existing golden fixture hashes.

## 2. Field semantics

| Field | Authoritative meaning | Consumer rule |
|---|---|---|
| `code` | Primary governed refusal reason. One of the six frozen `AnswerRefusalCode` values. | The authoritative reason. Read first. |
| `findings` | Supporting validation findings (the validation codes that decayed into `code`). | Inspectable; every failing validator code stays visible. |
| `detail` | Consumer-safe explanation of the refusal. No protected identifiers, no internal row or object references. | Render to the operator; safe for display. |
| `limitations` | Inherited context limitations and restrictions (upstream context limitations, `answer_limitations()`). | Read as inherited restrictions, **not** as a restatement of `code`. |

## 3. Consumer law (binding on Book V)

1. `limitations` is **not** a guaranteed restatement of the refusal's own code.
   A refusal may carry an empty `limitations` tuple while still carrying a
   valid refusal reason through `code` and `detail`. An empty inherited-limitation
   tuple is **not** evidence that the refusal has no reason.
2. The consumer must read the authoritative refusal code (`code`), the safe
   detail (`detail`) and the inherited restrictions (`limitations`) **together**.
3. `code` wins for the refusal reason; `limitations` are shown alongside, never
   merged into the reason.
4. No protected identifiers appear in `code`, `detail` or `limitations`.
5. `detail` and `limitations` must not contradict one another for the same
   refusal.
6. No limitation is fabricated for a case that has none.
7. Refusal precedence over multiple failing validators is stable: the
   highest-precedence code (`REFUSAL_PRECEDENCE`) wins and every failing
   validator code remains inspectable on `findings`.
8. Serialization is deterministic: same input produces the same `answer_id`,
   `code`, `detail`, `findings` and `limitations`.

## 4. The six refusal codes and precedence (unchanged)

Highest precedence first:

1. `ACCESS_NOT_ENTITLED`
2. `AMBIGUOUS_SCOPE`
3. `MODEL_VERSION_UNAVAILABLE`
4. `CURRENT_DATA_UNAVAILABLE`
5. `SETUP_NOT_ENCODED`
6. `INSUFFICIENT_EVIDENCE`

## 5. F-07a acceptance requirement mapping

| ID | Requirement | Contract basis |
|---|---|---|
| A01 | Every applicable refusal has a safe, structured representation of its own limitation | `code` + `detail` name the reason; `limitations` carries inherited restrictions |
| A02 | `detail` and `limitations` cannot contradict for the same refusal | Consumer law #5 |
| A03 | The six refusal codes and their precedence are unchanged | Section 4 |
| A04 | Protected identifiers excluded from both surfaces | Consumer law #4 |
| A05 | No limitation fabricated for a case that has none | Consumer law #6 |
| A06 | `NO_GO_ACTIVE` not hidden when an active no-go exists | `limitations` preserves active restrictions |
| A07 | `CURRENT_DATA_UNAVAILABLE` explicit where freshness unavailable | Section 4, code #4 |
| A08 | `MODEL_VERSION_UNAVAILABLE` explicit where version not encoded | Section 4, code #3 |
| A09 | `SETUP_NOT_ENCODED` explicit where setup not encoded | Section 4, code #5 |
| A10 | Refusal precedence over multiple failing validators stable | Consumer law #7 |
| A11 | Consumer projection deterministic | Consumer law #8 |
| A12 | Existing `answer_id` unchanged unless a new contract version ratified | Zero payload change; `ASK_ANSWER_CONTRACT_V1` retained |
| A13 | Book V receives one documented, stable projection | This document |
| A14 | Historical payloads byte-reproducible against frozen hashes | Zero payload change |
| A15 | No false refusal introduced by the projection | No validation behaviour altered |

## 6. What is not changed

- `GovernedAnswerRefusal` (no field added, removed or retyped).
- IV.5 schema and refusal serializer.
- Frozen answer IDs.
- Historical refusal payloads.
- Existing golden fixture hashes.

## 7. Deferred

Option B — a new consolidated `refusal_limitations` field under
`ASK_ANSWER_CONTRACT_V2` — remains DEFERRED pending a Book V consumer
requirement. It is not implemented in this rung.
