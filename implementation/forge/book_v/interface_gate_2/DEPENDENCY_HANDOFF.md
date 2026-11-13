# DEPENDENCY_HANDOFF.md

**BA-39 Rung 1 — Book V Interface Contract Hardening — Dependency Handoff**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `b7f595ea417954e94ac15409a626915cb50ef8dc`
**Mode:** Audit and planning only.

## 1. Ratified upstream DTO contracts (Book IV — read-only)

Book V consumes the following Book IV DTO surfaces as read-only inputs. It
does not extend, retype, or add fields to them.

| Contract | Source (Book IV bloc) | Status | Book V may use? |
|---|---|---|---|
| `ValidatedAnswer` DTO | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| `GovernedAnswerRefusal` DTO | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| `answer_id` | IV.5 `app/forge/ask_cerebus/answer/record.py` | Ratified (V1) | Yes |
| `CitationRef` | IV.5 `app/forge/ask_cerebus/answer/schema.py` | Ratified (V1) | Yes |
| Evidence status / epistemic label | IV.3 `context/enums.py` | Ratified (V1) | Yes |
| Model generation | IV.2 `retrieval/refs.py` (`CanonicalRef.generation`) | Ratified (V1) | Yes |
| Answer depth | IV.5 `answer/enums.py` (`AnswerDepth`) | Ratified (V1) | Yes |
| Setup eligibility | IV.5 `answer/enums.py` (`SetupVerdict`) | Ratified (V1) | Yes |
| Refusal limitations (`limitations` field) | IV.5 `GovernedAnswerRefusal.limitations` | Ratified (V1, F-07a Option C) | Yes |
| Safe provenance | IV.3 `ContextItem` / IV.5 `CitationRef` | Ratified (V1) | Yes |
| Error states | IV.5 `AnswerOutcome.GOVERNED_REFUSAL` | Ratified (V1) | Yes |

Book V must not consume raw `GatewayDraft` provider output or any IV.4/IV.3
surface not exposed through the IV.5 DTO.

## 2. UI trust boundaries (future UI contract)

The future Book V UI must consume only the `BookVInterfaceResponse`
produced by `PresentationAdapter`. It must never:

- Consume `GatewayDraft` directly.
- Read raw context packages (`AuthorizedContextPackage`).
- Read private retrieval records (`AuthorizedRetrievalBundle` internals).
- Read provider credentials.
- Bypass IV.5 validation (`validate_answer`).
- Invent market statistics.
- Recalculate evidence.
- Promote historical data to current (`HISTORICAL`/`SUPERSEDED`/`PARKED`/
  `CANDIDATE`/`RESEARCH_FLAG`).
- Substitute model generations.
- Clear setup no-go states (`NO_GO_ACTIVE` must survive).
- Change user entitlement (`ACCESS_NOT_ENTITLED` enforced).
- Provide unvalidated execution advice.
- Discard material limitations.
- Convert refusals into apparent success.

Any interactive feature must consume a governed interface contract.
No route or network service is authorized in this rung.

## 3. Book VI / VII / VIII dependencies

| Book | Dependency | Gate | Blocks Book V? |
|---|---|---|---|
| Book VI | Commercial entitlement | EV-GATE-04 (OPEN) | Yes (BV-F4-02 deferred) |
| Book VII | Durable historical snapshots | EV-GATE-08 (OPEN) | Yes (BV-F4-04 deferred) |
| Book VII | Real semantic retrieval index | EV-GATE-10 (OPEN) | Yes (BV-F4-05 deferred) |
| Book VIII | Shared abuse store + rate/aggregation | EV-GATE-06 (OPEN) | Yes (BV-F4-06 deferred) |

## 4. F3/F4 stop conditions

The following requirements are **stop conditions** — they must not be
implemented until their respective gates close with evidence:

| Requirement | Stop condition | Gate |
|---|---|---|
| BV-F2-02 | Citation-surface presentation spec not ratified | EV-GATE-02 (OPEN) |
| BV-F2-04 | Live market data not configured | EV-GATE-07 (OPEN) |
| BV-F3-01 | Citation-surface spec not ratified | EV-GATE-02 (OPEN) |
| BV-F3-02 | Materiality policy not ratified | EV-GATE-03 (OPEN) |
| BV-F3-03 | Refusal-precedence ratification pending | EV-GATE-11 (OPEN) |
| BV-F3-04 | Launch threshold table not defined | EV-GATE-13 (OPEN) |
| BV-F4-01 | Live LLM provider not authorized | EV-GATE-01 (OPEN) |
| BV-F4-02 | Book VI commercial entitlement open | EV-GATE-04 (OPEN) |
| BV-F4-03 | Real current-market data feed not licensed | EV-GATE-07 (OPEN) |
| BV-F4-04 | Durable historical snapshot store not built | EV-GATE-08 (OPEN) |
| BV-F4-05 | Real semantic retrieval index not available | EV-GATE-10 (OPEN) |
| BV-F4-06 | Shared abuse store not implemented | EV-GATE-06 (OPEN) |
| BV-F4-07 | Human/operator review execution open | EV-GATE-12 (OPEN) |

## 5. Rung 2 implementation sequence

The next rung (BA-39 Rung 2 or later) may implement only after the
respective gate closes:

1. Citation renderer (BV-F2-02) — after EV-GATE-02 closes
2. Current-state availability indicator (BV-F2-04) — after EV-GATE-07 closes
3. Governance items (BV-F3-01…F3-04) — after product/governance decisions
4. External integrations (BV-F4-01…F4-07) — after respective EV-GATEs close

No rung may implement production deployment, live provider integration,
Book VI entitlement, Book VII market integration, Book VIII security
expansion, or any behavior depending on an OPEN gate or BG-C.

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED
