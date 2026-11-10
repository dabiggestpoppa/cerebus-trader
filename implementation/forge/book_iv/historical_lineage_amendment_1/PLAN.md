# BA-35 RUNG 1 — F-09 HISTORICAL-LINEAGE REACHABILITY
## PLAN (planning and reproduction only)

**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting HEAD:** `dc3a5e781546f01d67eeda93e0553a5e6748dff4`
**Mode:** audit, reproduction and acceptance planning. No production module is
modified by this rung.

---

## 1. FOUNDATION VERIFICATION

Verified against the working tree at the starting head, not from prior reports.

| # | Check | Observed |
|---|---|---|
| 1 | Local HEAD equals `origin/forge` | PASS — both `dc3a5e781546f01d67eeda93e0553a5e6748dff4` |
| 2 | Exact expected starting SHA | PASS |
| 3 | Append-only ancestry | PASS — BA-20…BA-34 commits remain ancestors; no rewrite |
| 4 | BA-34 supplemental ratification | PRESENT — `RATIFICATION_SUPPLEMENT_V2.md` (F-06/F-07 PASS, F-07a/F-09 OPEN) |
| 5 | Full baseline | 2,654 passed / 0 failed / 29 skipped (measured this rung) |
| 6 | IV.1–IV.6 ratifications | PRESENT — 60 `.md` artefacts across `bloc_iv_1`…`bloc_iv_6` + `security_amendment_1` |
| 7 | BA-32 security repairs | PRESENT — 27 amendment drivers, all green in the baseline |
| 8 | BA-33 hash canonicalization | PRESENT — `HASH_RATIFICATION_V1.md`, 17/17 guards in both encodings |
| 9 | Q1–Q5 fixtures | PRESENT — `bloc_iv_5/fixtures/Q5-01…Q5-10` + manifest |
| 10 | EV-001–EV-120 | 120 cases, digest `74bc217bd3908fbbb9984d316182c70ca904878c2299709567cca5a82cbd31a8` |
| 11 | EV-121–EV-144 | 24 amendment cases + manifest, unchanged (EC-27 asserts the digest) |
| 12 | EV-145–EV-154 | 10 cases, digest `aa7caee0a798deb4775192fe64026a1736341763a74947d8fa85d52df0d3eed2` |
| 13 | Original IV.6 independent oracle | PRESENT, unmodified — `evaluation/oracle.py` |
| 14 | Six answer refusals | EXACT — `AnswerRefusalCode` has six members (`enums.py:19-27`) |
| 15 | Gateway task routing | 8 `RouteTask` values; 11 of 12 intents mapped in `task_from_intent` (`INDICATOR_NAVIGATION` unmapped) |
| 16 | Book II provider interface | FROZEN — `app/forge/providers/llm.py`, no change proposed |
| 17 | Routes and migrations | Migrations `001`–`004` only; no route added |
| 18 | `market_data` | NOT_CONFIGURED — no snapshot provider is wired into the chain service; `provider_configured=False` |
| 19 | Final-head CI | Run `42915653656` at `dc3a5e7` — `test` + `postgres` success |
| 20 | Untracked files | NONE (`git status --porcelain --untracked-files=all` empty) |

---

## 2. WHAT F-09 ACTUALLY IS

BA-34 recorded F-09 as "the gateway admits no task". That attribution is wrong,
and this rung measures the correction:

- `task_from_intent("HISTORICAL_LINEAGE")` **returns** `RouteTask.HISTORICAL`.
  The task exists; admission never gets to use it.
- Retrieval **does** resolve the canonical models: `MOD.P90.V1`,
  `MOD.BASE80.V1`, `MOD.MARKOV.LEGACY.V1` are selected with generation
  `P90.ORIGINAL` / `BASE80` / `MARKOV.LEGACY` and exposure `RESEARCH_LAB`.
- Retrieval then emits a **refusal** — `REQUIRED_FIELDS_UNRESOLVED`
  (`SNAPSHOT_CONTEXT_MISSING`) — because every `HISTORICAL_RESEARCH` plan is
  routed to Book III intelligence.
- IV.3 honours that refusal and marks the whole package `REFUSED`, discarding
  the canonical, claim and lineage items it just packaged.
- IV.4 then refuses `UPSTREAM_REFUSED`, correctly.
- The IV.6 harness drops that admission failure and calls
  `validate_answer(None, package)`, which raises `TypeError` — so the oracle
  records `ERROR` instead of a refusal.

So F-09 is **not** a gateway gap. It is an over-broad intelligence trigger in
IV.2, compounded by a harness composition defect that converts a correct
governed refusal into an unhandled error.

---

## 3. INTENT → TASK COMPATIBILITY MATRIX

Measured by running each intent through `interpret → retrieve → pack → admit` on
the chain fixture. Task column is `task_from_intent(intent)`.

| Intent | Scope observed | Route task | Bundle | Canonical refs | Bundle refusals | Package | Admission | Correct? |
|---|---|---|---|---|---|---|---|---|
| DEFINITION | GENERAL | DEFINITION | UNAVAILABLE | 0 | 0 | PARTIAL | Admission | Yes — plan-only/definitional, no canonical object |
| MODEL_DESCRIPTION | GENERAL | DEFINITION | PARTIAL | 1 | 0 | PARTIAL | Admission | Yes |
| CURRENT_STATE | CURRENT | CURRENT_STATE | PARTIAL | 1 | 1 | REFUSED | `UPSTREAM_REFUSED` | Yes — no market provider; governed refusal |
| LEVEL_COORDINATE | GENERAL | CURRENT_STATE | PARTIAL | 1 | 0 | PARTIAL | Admission | Yes |
| SETUP_CONTEXT | GENERAL | SETUP_CONTEXT | UNAVAILABLE | 0 | 0 | PARTIAL | Admission | Yes — setup not encoded is decided in IV.5 |
| STATISTIC_EVIDENCE | GENERAL | STATISTIC_EVIDENCE | PARTIAL | 1 | 0 | PARTIAL | Admission | Yes |
| COMPARISON | GENERAL | COMPARISON | PARTIAL | 2 | 0 | PARTIAL | Admission | Yes |
| HISTORICAL_LINEAGE | HISTORICAL_RESEARCH | **HISTORICAL** | PARTIAL | 1–2 | **1** | **REFUSED** | `UPSTREAM_REFUSED` | **NO — F-09** |
| METHODOLOGY_RESEARCH | GENERAL | RESEARCH | PARTIAL | 1 | 0 | PARTIAL | Admission | Yes |
| INDICATOR_NAVIGATION | GENERAL | **NONE** | UNAVAILABLE | 0 | 0 | PARTIAL | `ROUTE_UNSUPPORTED` | Governed in product; **ERROR in harness** (F-10) |
| TROUBLESHOOTING | GENERAL | DEFINITION | PARTIAL | 1 | 0 | PARTIAL | Admission | Yes |
| GENERAL_MARKET_KNOWLEDGE | (declared) GENERAL | GENERAL | declared | — | — | — | — | Mapping exists in source; no probe query reached it (needs no model entity) |

Two rows break the binding law *"every recognized, authorized intent must reach
a supported task or an explicit governed refusal"*:

- **`HISTORICAL_LINEAGE`** — reaches a supported task but is denied before the
  gateway by an unrelated intelligence requirement. This is the F-09 defect.
- **`INDICATOR_NAVIGATION`** — has no task. In product composition the gateway
  returns a governed `ROUTE_UNSUPPORTED` refusal, which satisfies the law; the
  evaluation harness turns it into `ERROR`. Recorded as **F-10**.

The `CURRENT_STATE` row is the contrast case that proves the diagnosis: it
genuinely needs live intelligence, receives `PROVIDER_NOT_CONFIGURED`, and is
correctly refused. Historical *explanations* do not need that data.

---

## 4. HISTORICAL GENERATION GOVERNANCE

From the frozen Book I catalog (`bloc_iv_2/fixtures/_builders.py`):

| Model | Canonical id | Status | Exposure | Declared generation | Claims | Evidence |
|---|---|---|---|---|---|---|
| P90 | `MOD.P90.V1` | HISTORICAL | RESEARCH_LAB | `P90.ORIGINAL` | `CL.P90.V1` (join `UNSUPPORTED`) | none |
| Base80 | `MOD.BASE80.V1` | HISTORICAL | RESEARCH_LAB | `BASE80` | none | none |
| Markov legacy | `MOD.MARKOV.LEGACY.V1` | HISTORICAL | RESEARCH_LAB | `MARKOV.LEGACY` | none | none |
| Superseded control | `MOD.LEGACY.SUPERSEDED.V1` | SUPERSEDED | — | — | — | — |

Consequences:

- A historical **explanation** is answerable from canonical model identity,
  lineage and declared status. It needs no snapshot and no live data.
- A historical **numerical** request is not answerable: P90's only claim has join
  status `UNSUPPORTED` and no evidence refs. It must refuse, and does — but it
  must refuse for the right reason (`INSUFFICIENT_EVIDENCE`), not because a
  snapshot context is missing.
- `SUPERSEDED` must stay superseded. No route may promote a historical identity
  to current eligibility.
- `HISTORICAL_GENERATION` is already emitted as a limitation by
  `retrieval/lineage.py`, so the restriction survives without the intelligence
  request that currently blocks everything.

---

## 5. PROPOSED MINIMAL REPAIR (Rung 2, not implemented here)

### 5.1 IV.2 — route intelligence only when the question needs market data

Current condition in `AskCerebusRetrievalService.retrieve`:

```python
if plan.requires_live_intelligence or plan.time_scope.value in (
    "CURRENT", "AS_OF", "HISTORICAL_RESEARCH",
):
```

`requires_live_intelligence` is already exactly `time_scope is CURRENT`
(`interpreter/interpret.py`). The extra `or` clause is what forces a Book III
request for every historical plan, including pure documentation.

Minimal correction: trigger intelligence on **evidence or live need**, not on
history alone — keep `CURRENT`/`AS_OF` (a point-in-time state request is a data
request) and drop `HISTORICAL_RESEARCH` unless the plan asks for evidence
(`requires_evidence` or `intent is STATISTIC_EVIDENCE`). Historical explanation
then flows with `HISTORICAL_GENERATION` + `EVIDENCE_INSUFFICIENT` limitations
intact; historical statistics still route and still refuse without a provider.

### 5.2 IV.6 harness — stop converting refusals into errors

`evaluation/harness.py:_chain_gateway` returns `None` on `AdmissionFailure`, and
`_run_chain` then calls `validate_answer(None, package)`. Return the
`GatewayRefusal` (or its admission failure) so the oracle sees `REFUSED`, which
is what the product does. This is evaluation-infrastructure scope, not product
behaviour, and it is the only reason F-09 looked like an ERROR.

### 5.3 Explicitly not proposed

No new provider port, no entitlement widening, no re-retrieval, no invented
evidence, no epistemic-label change, no IV.5 validation bypass, no current-setup
eligibility, no production default provider, no Book I edit. The gateway still
returns `GatewayDraft(status=UNVALIDATED)` or an existing refusal.

---

## 6. SCOPE BOUNDARY

| Bloc | Rung 1 | Rung 2 |
|---|---|---|
| Book I corpus | read only | read only (no new evidence) |
| IV.1 interpreter | read only | **frozen** — intents and scopes are already correct |
| IV.2 retrieval | read only | one condition in the intelligence trigger; needs separate authorization |
| IV.3 context | read only | **frozen** — honours upstream refusals correctly |
| IV.4 gateway | read only | **frozen** — task mapping already correct |
| IV.5 validator | read only | **frozen** — remains truth authority |
| IV.6 evaluation | read only | harness composition + additive corpus EV-155+ |

---

## 7. FALSE-REFUSAL PROTECTION

The repair must not make historical questions answerable by weakening refusal:

- `STATISTIC_EVIDENCE` on P90 keeps its `EVIDENCE_INSUFFICIENT` path (join
  `UNSUPPORTED`) and must refuse with `INSUFFICIENT_EVIDENCE`.
- `CURRENT_STATE` and `AS_OF` keep the intelligence request and keep refusing
  when no provider is configured.
- Actionable historical requests keep `SETUP_NOT_ENCODED`/`NO_GO_ACTIVE` gating.
- Modern-model positives (EV-145–EV-153) must remain answered; their 10/10 path
  metric and the 0/58 false-refusal rate are the controls.

Success is "historical explanation reaches a governed explanation **or** a
justified refusal", never "every historical query answers".

---

## 8. IV.5 VALIDATION PRESERVED

IV.5 stays the truth authority. A historical explanation still passes every
validator: citation resolution, claim support, generation consistency, no-go and
uncertainty. The only change is which items arrive; no validator is relaxed and
no expectation is rewritten. Existing refusal precedence and the six frozen
codes are untouched.

---

## 9. DELIVERABLES

`PLAN.md` (this file), `REPRODUCTION.md`, `ACCEPTANCE.md`,
`DEPENDENCY_HANDOFF.md` — under
`implementation/forge/book_iv/historical_lineage_amendment_1/`.
