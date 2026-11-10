# BA-35 RUNG 1 — DEPENDENCY HANDOFF
## Owner determination, minimal diff, versioning and authorization conditions

---

## 1. ACTUAL REPAIR OWNER

Determined from observed stage behaviour (`REPRODUCTION.md` §2–§7), not from the
BA-34 attribution.

| Candidate | Verdict | Evidence |
|---|---|---|
| IV.1 intent semantics | **Not the owner** | Intent `HISTORICAL_LINEAGE`, scope `HISTORICAL_RESEARCH`, `requires_live_intelligence=False`, identity and generation all correct |
| IV.2 retrieval-to-task mapping | **PRIMARY OWNER** | Canonical refs resolve, then the intelligence branch emits `REQUIRED_FIELDS_UNRESOLVED` for every `HISTORICAL_RESEARCH` plan and marks the bundle as carrying a refusal |
| IV.3 package metadata | **Not the owner** | It honours the upstream refusal exactly as specified; content and manifest are correct |
| IV.4 task admission / routing | **Not the owner** | `task_from_intent` maps to `RouteTask.HISTORICAL`; `GatewayService.generate` returns a governed `UPSTREAM_REFUSED` |
| IV.5 answer eligibility | **Not the owner (never reached)** | No draft is produced, so no validator runs |
| Evaluation-harness composition | **SECONDARY OWNER** | `_chain_gateway` discards `AdmissionFailure`; `validate_answer(None, …)` raises `TypeError` ⇒ `ERROR` |

Two findings are therefore recorded:

- **F-09** — S3, owner **IV.2** (`retrieval/service.py`, intelligence trigger).
- **F-09b** — S3, owner **IV.6 evaluation harness** (composition of a governed
  refusal into an error). Fixing F-09 does not remove F-09b: an unmapped intent
  (`INDICATOR_NAVIGATION`, **F-10**) still produces `ERROR` in the harness today.

---

## 2. MINIMAL AUTHORIZED SOURCE DIFF PROPOSAL (Rung 2)

### 2.1 IV.2 — one condition

`app/forge/ask_cerebus/retrieval/service.py`, in `retrieve`:

```python
# before
if plan.requires_live_intelligence or plan.time_scope.value in (
    "CURRENT", "AS_OF", "HISTORICAL_RESEARCH",
):
# after
needs_intelligence = bool(
    plan.requires_live_intelligence
    or plan.time_scope.value in ("CURRENT", "AS_OF")
    or (
        plan.time_scope.value == "HISTORICAL_RESEARCH"
        and (plan.requires_evidence or plan.intent is Intent.STATISTIC_EVIDENCE)
    )
)
if needs_intelligence:
```

Effect: explanation/lineage/identity/comparison questions keep
`HISTORICAL_GENERATION` + `EVIDENCE_INSUFFICIENT` limitations and flow on;
historical **statistics** still request intelligence and still refuse without a
provider; `CURRENT`/`AS_OF` are untouched.

No other IV.2 change. No new limitation code, no new refusal code, no reordering
of the existing limitation tuple (append-only ordering preserved).

### 2.2 IV.6 — carry the refusal

`app/forge/ask_cerebus/evaluation/harness.py`:

```python
admitted = admit(package)
if not hasattr(admitted, "task"):
    return admitted            # was: return None
```

and in `_run_chain`, when the gateway object is an `AdmissionFailure`, produce the
corresponding governed refusal (or extend `validate_answer` to build a safe
record from an admission failure instead of raising). The oracle must observe
`REFUSED`, matching product composition.

### 2.3 Not touched

Book I canonical data, Book II policy and port, IV.1, IV.3, IV.5, the existing
IV.6 oracle, EV-001–EV-154, Q1–Q5, migrations, routes, hash helper/constants.

---

## 3. VERSIONING REQUIREMENTS

- The IV.2 change alters **behaviour**, not the retrieval contract shape:
  `RETRIEVAL_CONTRACT_V1` may remain, because no field, enum or bundle invariant
  changes; only which requests trigger a pre-existing branch.
- If the reviewer prefers a version marker, `RETRIEVAL_CONTRACT_V2` is added
  **additively** with V1 still accepted, so frozen Q2 fixtures continue to
  reproduce byte-identically.
- The harness change touches evaluation only; no answer contract version changes.
- F-07a, if repaired, **does** need a new contract version (see §6).

---

## 4. FROZEN INTEGRITY

Must remain byte-identical and re-asserted in the Rung 2 drivers:

| Artefact | Control |
|---|---|
| EV-001–EV-120 digest `74bc217b…cbd31a8` | EC-27 |
| EV-121–EV-144 + manifest digest | EC-27 |
| EV-145–EV-154 digest `aa7caee0…3eed2` | EC-27 / corpus `verify()` |
| Q1–Q5 fixtures and `FIXTURE_MANIFEST.json` | hash guards |
| Frozen Q2 expectations (`expected/Q2-*.json`) | retrieval fixture tests |
| IV.1/IV.3/IV.5 source | R27 name-and-digest check |
| Book II `providers/llm.py` | R27 |
| Migrations `001`–`004`, routes | change-detection test |
| Hash helper, constants, `.gitattributes` | BA-33 guards, 17/17 in both encodings |

Critical nuance for Rung 2: the frozen **Q2-06** fixture already shows a P90
lineage plan with `refusals: []` and `trace.outcome: PARTIAL`, because its plan
scope is not `HISTORICAL_RESEARCH`. The IV.2 fix must reproduce that same result
for an IV.1-assigned historical scope, which is exactly the contradiction this
rung measures.

---

## 5. TEST AND DATASET HANDOFF

- New fixtures: `bloc_iv_6/fixtures_v3/` (EV-155–EV-178) with its own manifest
  digest; V1 and V2 corpora untouched.
- New driver file: `tests/test_forge_ask_cerebus_historical_lineage.py`
  (R01–R28), separate from the coverage drivers.
- IV.6 acceptance surface: 112 original + 30 coverage + 28 historical = 170
  drivers, with the original oracle still the adjudicator for V1/V2.
- No expectation may be derived from the system under test; each EV-155+ case
  declares its evidence path from the frozen Book I catalog, in the style of
  `evaluation/evidence_path.py`.

---

## 6. F-07a REPRESENTATION OPTIONS

| Option | What it means | Cost / risk | Verdict |
|---|---|---|---|
| **A. Normalize inside IV.5** | Populate `limitations` with the refusal's own reason | Changes frozen answer payloads and Q5 hashes; conflates upstream context limits with refusal reason | Reject for V1 |
| **B. Versioned derived projection** | Add `refusal_limitations` (or a projection object) under `ASK_ANSWER_CONTRACT_V2` | Clean separation; needs a new contract version and dual-read window; `answer_id` unaffected (it hashes inputs, not payload) but Q5 byte hashes change | **Recommended, deferred** |
| **C. Keep both surfaces, ratify the contract** | Ratify: `limitations` = upstream context limitations; `code` + `findings` + `detail` = refusal reason; Book V reads those | Zero risk, no byte change; requires documentation and a consumer rule | **Recommended now** |
| **D. Defer to Book V** | Wait for a governed UI requirement | Leaves 31 refusals ambiguous for any consumer | Acceptable only with C ratified |

**Recommendation:** ratify **C** now (it is a documentation/contract act, no
payload change), and schedule **B** only when Book V needs a single field, under
`ANSWER_CONTRACT_V2` with both versions readable. A is rejected because it
mutates frozen identities to fix a naming problem.

Current Book V state: **no consumer exists** — `GovernedAnswerRefusal` is
referenced only inside `app/forge/ask_cerebus/answer/`; nothing outside the bloc
reads `limitations`. So there is no live breakage today, and no urgency to change
frozen payloads.

---

## 7. IV.6 REGRESSION DEPENDENCIES

- The harness change must not alter any sealed-case result: SEALED modes never
  call `admit`, so the 48 V1 positives and 72 refusals must reproduce exactly.
- V2 `chain_evidence_path_correctness` (10/10) and `citation_support_correctness`
  (10/10) must stay at 10/10; their cases are `CHAIN`, so a harness change is the
  highest-risk edit in Rung 2 and needs a byte-for-byte replay check.
- Full suite baseline for Rung 2: **2,654 passed / 0 failed / 29 skipped** plus
  the new drivers; any drop is a stop condition.

---

## 8. BOOK V CONSUMER REQUIREMENTS

For a future governed UI, Book V needs exactly:

1. one field naming the authoritative refusal reason (today: `code`);
2. one field naming the restrictions inherited from context (today:
   `limitations`), clearly labelled as inherited;
3. a stable rule when the two disagree (`code` wins for the reason; both are
   shown, never merged);
4. no protected identifiers in either surface;
5. a version marker so a projection change is visible.

---

## 9. CONDITIONS FOR IMPLEMENTATION AUTHORIZATION

Rung 2 may start only when the operator authorizes:

1. **IV.2** — the single intelligence-trigger condition change (frozen bloc;
   explicit authorization required).
2. **IV.6 harness** — carrying admission failures instead of dropping them.
3. Additive corpus EV-155–EV-178 and drivers R01–R28.
4. F-07a decision: ratify C now, defer B to Book V (default proposal).

Still not authorized by this rung: Book I evidence creation, Book II policy
change, IV.1/IV.3/IV.5 edits, provider configuration, BG-C, `EV-GATE-01`–`13`,
human review, production.

---

## 10. READINESS VERDICT

Rung 2 is **ready to be authorized**: the defect is one condition, the task
already exists, the evidence already resolves, the restriction already survives,
and the acceptance surface is derived (28 requirements, 24 cases). The only
genuine blocker is authorization to touch frozen IV.2 — everything else is
evaluation-local.
