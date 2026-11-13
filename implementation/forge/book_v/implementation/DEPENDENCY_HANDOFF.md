# DEPENDENCY_HANDOFF.md

**BA-38 Rung 2 — Book V Deterministic Interface Foundation — Dependency Handoff**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `55fef69a18fe9da2db81c55a06af413e68b0c28c`

## 1. Upstream dependencies (Book IV — read-only)

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

## 2. Downstream dependencies (Book V → consumers)

Book V produces a `BookVInterfaceResponse` (frozen dataclass with
deterministic `payload()` serialization) for consumption by operator UI or
other read-only consumers. No Book V output is consumed by any production
endpoint in this rung.

| Output | Consumer | Gate dependency |
|---|---|---|
| `BookVInterfaceResponse` (answer shape) | Operator UI (future) | None |
| `BookVInterfaceResponse` (refusal shape) | Operator UI (future) | None |

## 3. Cross-book dependencies

| Book | Dependency | Status | Blocks Book V? |
|---|---|---|---|
| Book VI | Commercial entitlement | EV-GATE-04 OPEN | Yes (BV-F4-02 deferred) |
| Book VII | Durable historical snapshots | EV-GATE-08 OPEN | Yes (BV-F4-04 deferred) |
| Book VII | Real semantic retrieval index | EV-GATE-10 OPEN | Yes (BV-F4-05 deferred) |
| Book VIII | Shared abuse store + rate/aggregation | EV-GATE-06 OPEN | Yes (BV-F4-06 deferred) |

## 4. Gate dependencies (EV-GATE-01 through EV-GATE-13)

All 13 gates are OPEN. Book V deterministic implementation does not depend on
any gate being closed, but the following requirements are blocked:

| Requirement | Blocked by | Gate |
|---|---|---|
| BV-F2-02 (citation renderer) | EV-GATE-02 | OPEN |
| BV-F2-04 (current-state indicator) | EV-GATE-07 | OPEN |
| BV-F3-01 (citation-surface spec) | EV-GATE-02 | OPEN |
| BV-F3-02 (materiality threshold) | EV-GATE-03 | OPEN |
| BV-F3-03 (refusal-precedence ratification) | EV-GATE-11 | OPEN |
| BV-F3-04 (launch threshold table) | EV-GATE-13 | OPEN |
| BV-F4-01 (live LLM provider) | EV-GATE-01 | OPEN |
| BV-F4-02 (Book VI entitlement) | EV-GATE-04 | OPEN |
| BV-F4-03 (market data feed) | EV-GATE-07 | OPEN |
| BV-F4-04 (durable snapshots) | EV-GATE-08 | OPEN |
| BV-F4-05 (semantic index) | EV-GATE-10 | OPEN |
| BV-F4-06 (abuse store) | EV-GATE-06 | OPEN |
| BV-F4-07 (human review) | EV-GATE-12 | OPEN |

## 5. Book V implementation sequence (per CONTRACT_HANDOFF §7)

1. ✅ Read-only DTO consumption layer (F1-01…F1-10) — implemented
2. ✅ Refusal presentation component (F2-01) — implemented
3. ✅ Depth-aware layout (F2-03) — implemented
4. ⏸️ Citation renderer (F2-02) — blocked by EV-GATE-02
5. ⏸️ Current-state availability indicator (F2-04) — blocked by EV-GATE-07
6. ⏸️ Governance items (F3-01…F3-04) — blocked by product/governance decisions
7. ⏸️ External integrations (F4-01…F4-07) — blocked by respective EV-GATEs

## 6. What Book V must NOT do (hard boundaries)

Book V never:

- Consumes raw `GatewayDraft` provider output or IV.4 internals.
- Bypasses `validate_answer` (IV.5).
- Invents or recalculates model statistics.
- Promotes historical evidence (`HISTORICAL`/`SUPERSEDED`/`PARKED`/
  `CANDIDATE`/`RESEARCH_FLAG`) to current.
- Clears a no-go (`NO_GO_ACTIVE` must survive).
- Widens entitlement (`ACCESS_NOT_ENTITLED` enforced; no privileged citation
  leak).
- Interprets missing market data as valid current data.
- Converts a refusal into a successful answer.
- Introduces `ASK_ANSWER_CONTRACT_V2` or `refusal_limitations` without
  separate authorization.
- Assumes Book VI commercial entitlement or BG-C operational readiness.

## 7. Frozen integrity verification

| Item | Status |
|---|---|
| Book IV production source | Unchanged |
| Book II provider boundary | Unchanged |
| Routes | Unchanged |
| Migrations | 001–004, unchanged |
| Credentials | Unchanged |
| Frozen fixtures (EV-001–EV-178, Q1–Q5) | Unmutated |
| New API endpoints | None added |
| Live provider invocation | None |

## 8. Handoff summary

Book V deterministic interface foundation is implemented, tested, and ratified
for offline, deterministic development only. The 12 admitted requirements are
complete. All F3/F4 and gated F2 requirements remain deferred pending their
respective EV-GATE closures and governance decisions. Production release is
not ratified by this rung.

BG-A: PASS · BG-B: PASS · BG-C: BLOCKED
