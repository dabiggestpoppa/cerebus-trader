# BOOK_V_CHAPTER_MAP.md

**BA-39 Rung 1 — Book V Interface Contract Hardening — Chapter Inventory**

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting SHA:** `b7f595ea417954e94ac15409a626915cb50ef8dc`
**Mode:** Audit and planning only.

## 1. Actual frozen Book V chapter inventory

Book V has no separate chapter directory. The "frozen Book V chapters" are
the four planning documents under
`implementation/forge/book_v/entry_gate_1/`, ratified at BA-37:

| Chapter (document) | Intended responsibility | Status |
|---|---|---|
| `BOOK_IV_CLOSURE_AUDIT.md` | Book IV closure audit, six-bloc contract inventory, open findings register, EV-GATE register, BG-A/BG-B/BG-C verdicts | Frozen (BA-37) |
| `BOOK_V_READINESS_GATE.md` | Book V admission conditions, F1/F2/F3/F4 feasibility classification, GO/CONDITIONAL GO decision, implementation sequence | Frozen (BA-37) |
| `CONTRACT_HANDOFF.md` | Exact allowable DTO surfaces, refusal presentation semantics (F-07a Option C), citation/provenance requirements, entitlement boundaries, versioning expectations, IV.5/IV.6 ownership boundaries, implementation sequence, hard boundaries | Frozen (BA-37) |
| `ACCEPTANCE.md` | Requirement totals (25: 10 F1 + 4 F2 + 4 F3 + 7 F4), proposed test names, cross-cutting drivers, golden scenario inventory, traceability matrix, non-acceptance conditions, acceptance decision | Frozen (BA-37) |

## 2. Component ownership

| Component | Owner | Book V may? | Implemented? |
|---|---|---|---|
| Read-only DTO consumption layer | Book V | Yes (F1) | ✅ BA-38 (PresentationAdapter) |
| Refusal presentation component | Book V | Yes (F2-01) | ✅ BA-38 (PresentationAdapter + model) |
| Depth-aware answer layout | Book V | Yes (F2-03) | ✅ BA-38 (PresentationAdapter + model) |
| Citation renderer (bounded, attributed) | Book V | Yes but gated (F2-02) | ⏸️ Blocked by EV-GATE-02 |
| Current-state availability indicator | Book V | Yes but gated (F2-04) | ⏸️ Blocked by EV-GATE-07 |
| Citation-surface presentation spec | Product/UX | No (F3-01) | ⏸️ Blocked by EV-GATE-02 |
| Materiality / false-refusal threshold | Product owner | No (F3-02) | ⏸️ Blocked by EV-GATE-03 |
| Refusal-precedence ratification | Product/Governance | No (F3-03) | ⏸️ Blocked by EV-GATE-11 |
| Launch threshold table | Product owner | No (F3-04) | ⏸️ Blocked by EV-GATE-13 |
| Live LLM provider integration | Gateway owner + operator | No (F4-01) | ⏸️ Blocked by EV-GATE-01 |
| Book VI commercial entitlement | Book VI | No (F4-02) | ⏸️ Blocked by EV-GATE-04 |
| Real current-market data feed | Data owner | No (F4-03) | ⏸️ Blocked by EV-GATE-07 |
| Durable historical snapshot store | Book VII | No (F4-04) | ⏸️ Blocked by EV-GATE-08 |
| Real semantic retrieval index | Book VII | No (F4-05) | ⏸️ Blocked by EV-GATE-10 |
| Shared abuse store + rate/aggregation | Book VIII | No (F4-06) | ⏸️ Blocked by EV-GATE-06 |
| Human/operator review | Operator reviewer | No (F4-07) | ⏸️ Blocked by EV-GATE-12 |

## 3. Existing vs missing implementation

### Existing (BA-38, ratified)

| Component | Module | Requirements covered |
|---|---|---|
| Presentation adapter | `app/forge/book_v/presentation/adapter.py` | BV-F1-01…BV-F1-10, BV-F2-01, BV-F2-03 |
| Presentation model | `app/forge/book_v/presentation/model.py` | BV-F1-01…BV-F1-10, BV-F2-01, BV-F2-03 |
| Contract versions | `app/forge/book_v/presentation/versions.py` | All admitted |
| Acceptance drivers | `tests/test_forge_book_v_presentation.py` | 24 tests |
| Golden scenarios | `implementation/forge/book_v/golden/scenarios.py` | 19 scenarios |
| Golden verification drivers | `tests/test_forge_book_v_golden.py` | 19 tests |
| Adversarial drivers | `tests/test_forge_book_v_adversarial.py` | 14 tests |

### Missing (gated, not implemented)

| Component | Blocked by | Gate status |
|---|---|---|
| Citation renderer | EV-GATE-02 | OPEN |
| Current-state availability indicator | EV-GATE-07 | OPEN |
| Citation-surface presentation spec | EV-GATE-02 | OPEN |
| Materiality / false-refusal threshold | EV-GATE-03 | OPEN |
| Refusal-precedence ratification | EV-GATE-11 | OPEN |
| Launch threshold table | EV-GATE-13 | OPEN |
| Live LLM provider | EV-GATE-01 | OPEN |
| Book VI entitlement | EV-GATE-04 | OPEN |
| Market data feed | EV-GATE-07 | OPEN |
| Durable snapshots | EV-GATE-08 | OPEN |
| Semantic retrieval index | EV-GATE-10 | OPEN |
| Abuse store | EV-GATE-06 | OPEN |
| Human review | EV-GATE-12 | OPEN |

## 4. Dependency mapping

| Component | Upstream dependency | Cross-book dependency | Gate |
|---|---|---|---|
| Presentation adapter | IV.5 `ValidatedAnswer`/`GovernedAnswerRefusal` | None | None |
| Citation renderer | IV.5 `CitationRef` | None | EV-GATE-02 |
| Current-state indicator | IV.2/IV.3 freshness | None | EV-GATE-07 |
| Citation-surface spec | — | None | EV-GATE-02 |
| Materiality threshold | — | None | EV-GATE-03 |
| Refusal-precedence ratification | IV.5 `REFUSAL_PRECEDENCE` | None | EV-GATE-11 |
| Launch threshold table | IV.6 `scoring.py` | None | EV-GATE-13 |
| Live LLM provider | IV.4 `LLMProvider` port | None | EV-GATE-01 |
| Book VI entitlement | IV.2 `AuthorizationContext` | Book VI | EV-GATE-04 |
| Market data feed | IV.2 intelligence routing | None | EV-GATE-07 |
| Durable snapshots | — | Book VII | EV-GATE-08 |
| Semantic retrieval index | IV.2 retrieval | Book VII | EV-GATE-10 |
| Abuse store | — | Book VIII | EV-GATE-06 |
| Human review | IV.6 `review.py` | None | EV-GATE-12 |

## 5. Recommended implementation sequence (per CONTRACT_HANDOFF §7)

1. ✅ Read-only DTO consumption layer (F1-01…F1-10) — BA-38 complete
2. ✅ Refusal presentation component (F2-01) — BA-38 complete
3. ✅ Depth-aware layout (F2-03) — BA-38 complete
4. ⏸️ Citation renderer (F2-02) — blocked by EV-GATE-02 (OPEN)
5. ⏸️ Current-state availability indicator (F2-04) — blocked by EV-GATE-07 (OPEN)
6. ⏸️ Governance items (F3-01…F3-04) — blocked by product/governance decisions
7. ⏸️ External integrations (F4-01…F4-07) — blocked by respective EV-GATEs

Chapters 1–3 can proceed under the existing CONDITIONAL GO. Chapters 4–7
require gate closure or governance decisions before implementation.

## 6. Chapters that can proceed under CONDITIONAL GO

Only the deterministic, offline, fixture-backed components:

- Presentation adapter (read-only DTO projection) — ✅ implemented
- Refusal presentation component — ✅ implemented
- Depth-aware layout — ✅ implemented

No chapter requiring live provider, market data, entitlement, snapshots,
semantic index, abuse store, or human review can proceed under CONDITIONAL
GO.
