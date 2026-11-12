# IMPLEMENTATION_EVIDENCE

**BA-35 Rung 2 — Historical-Lineage Amendment 1, Rung 2 corrective implementation.**
**Branch:** `forge` · **Authoritative source:** `app/forge/ask_cerebus/retrieval/service.py` and
`app/forge/ask_cerebus/evaluation/harness.py`. **Append-only record.**

## 1. IV.2 code change

**File:** `app/forge/ask_cerebus/retrieval/service.py`, `AskCerebusRetrievalService.retrieve`.

**Before (defect):** every `HISTORICAL_RESEARCH` plan was routed to Book III
market/snapshot intelligence, so a documentation question was treated as a
market-data request:

```python
if plan.requires_live_intelligence or plan.time_scope.value in (
    "CURRENT", "AS_OF", "HISTORICAL_RESEARCH",
):
```

**After (repair):** intelligence (Book III market/snapshot) routing is
requested only when the question actually needs live or point-in-time market
data. Historical research questions (definition, identity, lineage, statistic)
are answerable from canonical model identity, status, lineage and
Claim/Evidence records; they do not need a market snapshot.
`requires_evidence` signals canonical Claim/Evidence retrieval, not Book III
intelligence, so it never opens this branch for history.

```python
needs_intelligence = bool(
    plan.requires_live_intelligence
    or plan.time_scope.value in ("CURRENT", "AS_OF")
)
if needs_intelligence:
```

**Actual intelligence predicate (after):**
`requires_live_intelligence OR time_scope in {CURRENT, AS_OF}`.

`HISTORICAL_RESEARCH` is removed from the trigger. `CURRENT`/`AS_OF` (genuine
live-data requests) and `requires_live_intelligence` (already exactly
`time_scope is CURRENT`) are preserved, so no snapshot requirement is removed
from queries that genuinely need one.

**Controls honoured:** no authorization widening, no extra retrieval, no
invented evidence, no status promotion, no generation substitution, no
current-state bypass, Book I source facts unchanged.

## 2. IV.6 harness change

**File:** `app/forge/ask_cerebus/evaluation/harness.py`.

**Before (defect):** `_chain_gateway` returned `None` when admission produced
no `task` (an `AdmissionFailure`). `_run_chain` then called
`validate_answer(None, package)`, which raised `TypeError`, converting a
governed refusal into an evaluation `ERROR`.

**After (repair):** `_chain_gateway` returns the `AdmissionFailure` instead of
`None`. `_run_chain` detects it and routes it through `validate_answer(draft,
package)` (IV.5 holds the real draft), producing a real
`GovernedAnswerRefusal` so the oracle observes `REFUSED`/`GOVERNED_REFUSAL`
matching product composition. No `None` reaches `validate_answer`; no
`GatewayDraft` is fabricated; no unexpected exception is mislabeled as a
refusal.

## 3. H1–H3 before / after

| Probe | Before (bundle → package → admit → harness) | After (bundle → package → admit → harness) |
|---|---|---|
| H1 `Show me the P90 historical state.` | `REQUIRED_FIELDS_UNRESOLVED/SNAPSHOT_CONTEXT_MISSING` → REFUSED → `UPSTREAM_REFUSED` → `TypeError`/`ERROR` | `PARTIAL` (no refusal) → PARTIAL → `Admission(task=HISTORICAL)` → `VALIDATED_ANSWER` |
| H2 `Show me the Base80 state.` | same as H1 | `VALIDATED_ANSWER` |
| H3 `Show me the Markov legacy state.` | same as H1 | `VALIDATED_ANSWER` |

H1–H3 now reach the expected governed answer path; zero `ERROR` outcomes.

## 4. F-10 negative control

`INDICATOR_NAVIGATION` is a valid interpreter intent with no IV.4 task
(`task_from_intent` returns `None`). Product composition returns a governed
`ROUTE_UNSUPPORTED` refusal; the harness now preserves that governed outcome
instead of raising `ERROR`. No new IV.4 task is implemented (not authorized
for this rung). Verified by `test_f09_r18_invalid_task_bounded`.

## 5. All 28 F-09 drivers

`tests/test_forge_ask_cerebus_historical_lineage.py`, R01–R28: **28/28 passed,
0 skipped, 0 xfail.**

- R01–R03: P90 / Base80 / Markov reach gateway task `HISTORICAL`, never `ERROR`.
- R04–R12: explanation at BEGINNER / OPERATOR / RESEARCHER preserves canonical
  model id, declared generation, `HISTORICAL` label and `HISTORICAL_GENERATION`
  limitation.
- R13–R14: `MOD.LEGACY.SUPERSEDED.V1` stays `SUPERSEDED`; no generation
  substitution (P90 stays `P90.ORIGINAL`, never `PHI`).
- R15: unsupported P90 statistic refuses `INSUFFICIENT_EVIDENCE` (not
  `CURRENT_DATA_UNAVAILABLE`, not an answer).
- R16: current-state request for a historical model refuses
  `CURRENT_DATA_UNAVAILABLE`, not a historical answer.
- R17: actionable historical setup is gated `SETUP_NOT_ENCODED`, never an
  executable setup.
- R18: `INDICATOR_NAVIGATION` yields a bounded `ROUTE_UNSUPPORTED`, never
  `ERROR`.
- R19: no historical answer implies current production eligibility.
- R20–R23: citations resolve to declared model/generation; `RESEARCH_LAB`
  exposure preserved; no additional provider call; no additional retrieval.
- R24–R28: all 12 intents reach a task or governed refusal; no new false
  refusal; deterministic replay; frozen EV-001–EV-154 corpus intact; security
  drivers green.

## 6. All 24 EV-155–EV-178 cases

`implementation/forge/book_iv/bloc_iv_6/fixtures_v3/` — dataset digest
`ee9cbf30fd4b66f53de4554d82f5379d53d7df1b7ea2c8f6d7bf27498bd22657`.

| Band | Cases | Outcome |
|---|---|---|
| EV-155–157 definition | P90/Base80/Markov | `VALIDATED_ANSWER`, generation preserved |
| EV-158–160 identity | P90/Base80/Markov | `VALIDATED_ANSWER`, names canonical id + generation |
| EV-161–163 lineage | P90/Base80/Markov | `VALIDATED_ANSWER`, carries lineage ref + generation |
| EV-164–166 comparison | + `MOD.BTC.TRACKER.V1` | `VALIDATED_ANSWER`, both identities, no generation substitution |
| EV-167–169 historical evidence | P90/Base80/Markov | `GOVERNED_REFUSAL` `INSUFFICIENT_EVIDENCE` |
| EV-170–172 unsupported statistic | P90/Base80/Markov | `GOVERNED_REFUSAL` `INSUFFICIENT_EVIDENCE`, never a number |
| EV-173–175 current state | P90/Base80/Markov | `GOVERNED_REFUSAL` `CURRENT_DATA_UNAVAILABLE` |
| EV-176–178 actionable setup | P90/Base80/Markov | `GOVERNED_REFUSAL` `SETUP_NOT_ENCODED` |

Depth distribution: BEGINNER 8, OPERATOR 8, RESEARCHER 8 (each depth covers
all eight forms).

## 7. Security non-regression

Original IV.5 acceptance, IV.6 acceptance, EC-01–EC-30 coverage and the 27
security-amendment drivers remain green. The repair grants no new provider or
authorization privileges. The only test affected by the authorized IV.2 source
diff is the hash-pin guard for `retrieval/service.py`; that conflict is
documented in `RATIFICATION_SUPPLEMENT_V1.md` (Section 12) and is not a
regression.

## 8. Frozen integrity

Unchanged: Book I canonical catalog, Book II provider ports, IV.1 interpreter,
IV.3 context package, IV.4 task mappings, IV.5 answer validation, original IV.6
oracle, EV-001–EV-154, Q1–Q5 fixtures, original ratification documents,
BA-33 hash helper/constants, routes, SQL migrations, `.gitattributes`.

The IV.2 behavioural amendment has a clearly identified source diff
(`retrieval/service.py`, intelligence trigger) and this versioned ratification
supplement.

## 9. Defect / repair history

| Defect | Stage | Root cause | Repair |
|---|---|---|---|
| F-09 | IV.2 retrieval | `HISTORICAL_RESEARCH` forced Book III intelligence for pure documentation | Narrowed intelligence trigger to `CURRENT`/`AS_OF`/live-intelligence only |
| F-09b | IV.6 harness | `_chain_gateway` dropped `AdmissionFailure` → `validate_answer(None, …)` → `TypeError`/`ERROR` | Carry `AdmissionFailure` through; route via `validate_answer` → `GovernedAnswerRefusal` |
| F-10 | IV.6 harness | `INDICATOR_NAVIGATION` unmapped → harness `ERROR` | Preserved governed `ROUTE_UNSUPPORTED` (negative control; no new task) |
