# BA-35 RUNG 1 — REPRODUCTION
## F-09: three historical-lineage failures, stage by stage

All outputs below were produced by running the real chain at
`dc3a5e781546f01d67eeda93e0553a5e6748dff4`, with the chain fixture's operator
principal and context (`bloc_iv_6/fixtures/_builders.py:chain_credentials`,
`chain_service`). No provider, network, wall clock or market data is involved.
`market_data` is `NOT_CONFIGURED`.

---

## 1. EXACT INPUTS

| Probe | Query | Expected identity |
|---|---|---|
| H1 | `Show me the P90 historical state.` | `MOD.P90.V1` |
| H2 | `Show me the Base80 state.` | `MOD.BASE80.V1` |
| H3 | `Show me the Markov legacy state.` | `MOD.MARKOV.LEGACY.V1` |

---

## 2. IV.1 — INTERPRETATION (all three identical in shape)

| Field | H1 | H2 | H3 |
|---|---|---|---|
| Intent | `HISTORICAL_LINEAGE` | `HISTORICAL_LINEAGE` | `HISTORICAL_LINEAGE` |
| Time scope | `HISTORICAL_RESEARCH` | `HISTORICAL_RESEARCH` | `HISTORICAL_RESEARCH` |
| Effective depth | `RESEARCHER` | `RESEARCHER` | `RESEARCHER` |
| Actionable | `False` | `False` | `False` |
| Requires live intelligence | `False` | `False` | `False` |
| Requires lineage | `True` | `True` | `True` |
| Model entity | `P90` / generation `P90` | `BASE80` | `MARKOV` / `MARKOV.LEGACY` |
| Plan id | `PLAN.73d7191c…` | `PLAN.6a0eae9b…` | `PLAN.0d4d020e…` |

IV.1 is correct. The scope, the identity and the non-actionability are all
right, and `requires_live_intelligence` is honestly `False` — the plan itself
does not claim to need live data.

---

## 3. IV.2 — RETRIEVAL: canonical resolution SUCCEEDS, then refuses

| Field | H1 | H2 | H3 |
|---|---|---|---|
| Bundle outcome | `PARTIAL` | `PARTIAL` | `PARTIAL` |
| `canonical_refs` | `MOD.P90.V1` (`HISTORICAL`, `RESEARCH_LAB`, gen `P90.ORIGINAL`) | `MOD.BASE80.V1` (`HISTORICAL`, `RESEARCH_LAB`, gen `BASE80`) | `MOD.MARKOV.LEGACY.V1` (`HISTORICAL`, `RESEARCH_LAB`, gen `MARKOV.LEGACY`) |
| `claim_refs` | `CL.P90.V1` (join `UNSUPPORTED`, no evidence) | none | none |
| `lineage_refs` | `MOD.P90.V1` / `P90.ORIGINAL` | `MOD.BASE80.V1` / `BASE80` | `MOD.MARKOV.LEGACY.V1` / `MARKOV.LEGACY` |
| `evidence_refs` | none | none | none |
| Limitations | `EVIDENCE_INSUFFICIENT`, `HISTORICAL_GENERATION`, `MATERIAL_AMBIGUITY`, `REQUIRED_FIELDS_UNRESOLVED` | `HISTORICAL_GENERATION`, `REQUIRED_FIELDS_UNRESOLVED` | `HISTORICAL_GENERATION`, `REQUIRED_FIELDS_UNRESOLVED` |
| **Refusals** | **`REQUIRED_FIELDS_UNRESOLVED` / `SNAPSHOT_CONTEXT_MISSING`** | same | same |

The models resolve, the generations are preserved, and the correct historical
restriction is already present. The refusal is added by the intelligence branch:

```python
# app/forge/ask_cerebus/retrieval/service.py
if plan.requires_live_intelligence or plan.time_scope.value in (
    "CURRENT", "AS_OF", "HISTORICAL_RESEARCH",
):
    intelligence = route_intelligence(plan, snapshot_context, self._snapshot_provider, ...)
    refusals = refusals + intelligence.refusals
```

With `snapshot_context=None`, `build_request` returns
`Refusal(REQUIRED_FIELDS_UNRESOLVED, "SNAPSHOT_CONTEXT_MISSING")`. Supplying a
context would not help either: with no provider configured the same branch
returns `HISTORICAL_UNAVAILABLE` (`HISTORICAL_RETENTION_UNAVAILABLE`). Both
outcomes are hard refusals, so **no historical explanation can pass this
branch in the current environment**.

---

## 4. IV.3 — CONTEXT: a refused package that still holds the evidence

| Field | H1 | H2 | H3 |
|---|---|---|---|
| Outcome | **`REFUSED`** | **`REFUSED`** | **`REFUSED`** |
| Sections | `QUERY_CONTRACT`, `CANONICAL_MODEL`, `CLAIMS`, `LINEAGE_TERMS`, `LIMITATIONS_NEGATIVE` | `QUERY_CONTRACT`, `CANONICAL_MODEL`, `LINEAGE_TERMS`, `LIMITATIONS_NEGATIVE` | same as H2 |
| Items | plan item, `MOD.P90.V1`, `CL.P90.V1`, lineage, 4 limitations + `MISSING_EVIDENCE` + refusal item | plan, `MOD.BASE80.V1`, lineage, 2 limitations + refusal | plan, `MOD.MARKOV.LEGACY.V1`, lineage, 2 limitations + refusal |

`ContextPackager.pack` sets `ContextOutcome.REFUSED` whenever the bundle carries
any refusal — correctly, because it must not launder an upstream refusal. The
effect here is that fully authorized historical evidence is packaged and then
sealed off. IV.3 behaves as specified; the specification is being fed a spurious
refusal.

---

## 5. IV.4 — GATEWAY: task exists, admission is pre-empted

| Check | Result |
|---|---|
| `task_from_intent("HISTORICAL_LINEAGE")` | `RouteTask.HISTORICAL` — **exists** |
| `admit(package)` | `AdmissionFailure(UPSTREAM_REFUSED, "upstream context package is refused")` |
| Product composition (`GatewayService.generate(package)`) | `GatewayRefusal(outcome=REFUSED, code=UPSTREAM_REFUSED)` — a **governed refusal** |
| Harness composition (`evaluation/harness.py`) | returns `None`, because `admit()` produced no `.task` |

So the gateway is not the defect: in product composition it produces exactly the
bounded refusal the law allows. The harness then discards it.

---

## 6. IV.5 — NOT REACHED

`validate_answer` is called with `None`, and the only diagnostic is the type
error in §7. IV.5 never adjudicates a historical question in this chain.

---

## 7. IV.6 — `ERROR`, not a refusal

```
Show me the P90 historical state.    RAISED TypeError: the answer layer only accepts a GatewayDraft
Show me the Base80 state.            RAISED TypeError: the answer layer only accepts a GatewayDraft
Show me the Markov legacy state.     RAISED TypeError: the answer layer only accepts a GatewayDraft
```

Cause, in `evaluation/harness.py`:

```python
admitted = admit(package)
if not hasattr(admitted, "task"):
    return None            # ← a governed refusal, discarded
...
answer = validate_answer(gateway, package)   # gateway is None
```

and `answer/service.py:_admission_refusal` raises `TypeError` before it can build
a safe record. Hence the oracle's `outcome == "ERROR"`.

---

## 8. FIRST FAILING BOUNDARY

**IV.2 intelligence routing.** Concretely, `retrieve()` at the `or plan.time_scope
.value in ("CURRENT","AS_OF","HISTORICAL_RESEARCH")` clause: a documentation
question is treated as a market-data question, and the resulting
`REQUIRED_FIELDS_UNRESOLVED` refusal becomes the package's terminal outcome.

Second, independent defect: **IV.6 harness composition** converts that governed
refusal into a `TypeError`/`ERROR`.

---

## 9. ERROR VERSUS REFUSAL — WHY IT MATTERS

| Composition | Observable | Legal? |
|---|---|---|
| Product (`GatewayService.generate`) | `REFUSED` / `UPSTREAM_REFUSED` | A governed refusal, but of the wrong cause: the user's historical question was answerable |
| Evaluation harness | `ERROR` / `TypeError` | **Not legal** — an unhandled task-admission gap is not a governed refusal, and it hides the real cause |

Recording `ERROR` made the gap look like missing gateway functionality. It is
not: it is a spurious upstream refusal plus a harness that cannot carry one.

---

## 10. MISSING EVIDENCE VERSUS MISSING TASK

| Question | Task | Evidence | Correct outcome | Observed |
|---|---|---|---|---|
| H1 P90 explanation | `HISTORICAL` exists | model + claim, claim unsupported | explanation with `INSUFFICIENT_EVIDENCE` limitation for any number | `ERROR` (harness) / `UPSTREAM_REFUSED` (product) |
| H2 Base80 explanation | `HISTORICAL` exists | model identity + lineage only | explanation of identity/status/lineage | same |
| H3 Markov explanation | `HISTORICAL` exists | model identity + lineage only | same | same |
| P90 win rate | `STATISTIC_EVIDENCE` exists | join `UNSUPPORTED` | refusal `INSUFFICIENT_EVIDENCE` | blocked at IV.3 before IV.5 |

Missing *task* is false for all three: `RouteTask.HISTORICAL` is wired. Missing
*evidence* is true only for the numerical form.

---

## 11. DEPTH AND FORM SWEEP — 72 OBSERVATIONS

3 models × 8 question forms × 3 depths (depth applied as the authorized ceiling
on `InterpreterContext`), real chain, `retrieve → pack → admit`:

| Form | Detected intent | Scope | Canonical refs | Result (all 3 models × 3 depths) |
|---|---|---|---|---|
| definition ("What is the P90 model?") | HISTORICAL_LINEAGE | HISTORICAL_RESEARCH | 1 | REFUSED |
| identity ("Which model version is the P90 generation?") | HISTORICAL_LINEAGE | **MODEL_VERSION** | 1 | **PARTIAL → admitted** |
| lineage ("Show me the P90 historical lineage.") | HISTORICAL_LINEAGE | HISTORICAL_RESEARCH | 1 | REFUSED |
| comparison ("Compare the P90 and the BTC Tracker models.") | COMPARISON | HISTORICAL_RESEARCH | 2 | REFUSED |
| historical evidence ("What was the P90 win rate historically?") | STATISTIC_EVIDENCE | HISTORICAL_RESEARCH | 1 | REFUSED |
| unsupported statistic ("What is the P90 median hold time statistically?") | STATISTIC_EVIDENCE | HISTORICAL_RESEARCH | 1 | REFUSED |
| current state ("What is the P90 state right now?") | HISTORICAL_LINEAGE | HISTORICAL_RESEARCH | 1 | REFUSED |
| actionable ("Should I enter a P90 setup?") | HISTORICAL_LINEAGE | HISTORICAL_RESEARCH | 1 | REFUSED |

Totals: **63 REFUSED, 9 admitted**. Every refusal is
`REQUIRED_FIELDS_UNRESOLVED` / `SNAPSHOT_CONTEXT_MISSING`, independent of depth
and of model. The single admitted form is the one whose scope is
`MODEL_VERSION` — evidence that identity, status, exposure and depth are *not*
the blockers, and that the trigger is exactly the `HISTORICAL_RESEARCH` clause.

Note the depth result is not a depth limitation: BEGINNER, OPERATOR and
RESEARCHER all fail identically, so no defect is being masked by a depth cap.

---

## 12. REPRODUCTION COMMANDS

Run from `cerebus-trader`.

```bash
# stage-by-stage for H1–H3 (interpret → retrieve → pack → admit)
PYTHONPATH=. python - <<'PY'
import importlib.util, sys
from pathlib import Path
F = Path("implementation/forge/book_iv/bloc_iv_6/fixtures")
spec = importlib.util.spec_from_file_location("fb", F/"_builders.py")
fb = importlib.util.module_from_spec(spec); sys.modules["fb"] = fb; spec.loader.exec_module(fb)
from app.forge.ask_cerebus.interpreter.interpret import interpret
from app.forge.ask_cerebus.context.service import ContextPackager
from app.forge.ask_cerebus.llm_gateway.request import admit
principal, ctx = fb.chain_credentials(); svc = fb.chain_service()
for q in ("Show me the P90 historical state.", "Show me the Base80 state.",
          "Show me the Markov legacy state."):
    plan = interpret(q); bundle = svc.retrieve(plan, principal, ctx)
    pkg = ContextPackager().pack(plan, bundle)
    print(q, plan.intent.value, plan.time_scope.value, bundle.outcome.value,
          [r.object_id for r in bundle.canonical_refs],
          [getattr(r.code, "value", r.code) for r in bundle.refusals],
          pkg.outcome.value, type(admit(pkg)).__name__)
PY

# the harness ERROR
PYTHONPATH=. python -c "
from types import SimpleNamespace
from app.forge.ask_cerebus.evaluation import harness
harness._run_chain(SimpleNamespace(query_text='Show me the P90 historical state.', depth='OPERATOR', draft_variant='ok'))
"

# frozen Q2-06 expectation this contradicts (P90 lineage, no refusal, PARTIAL)
python -c "import json;d=json.load(open('implementation/forge/book_iv/bloc_iv_2/fixtures/expected/Q2-06.json'));print(d['refusals'], d['trace']['outcome'])"
```

Result of the last command: `[] PARTIAL` — the frozen IV.2 fixture for a P90
lineage plan contains **no refusal**, because it is built from a plan whose scope
is not `HISTORICAL_RESEARCH`. The same model, at an IV.1-assigned historical
scope, refuses. That pairing is the measured contradiction at the heart of F-09.

---

## 13. ENVIRONMENT

Windows authoring host; deterministic fixtures only; no network, no provider, no
market data. CI is the Linux evidence for the committed planning documents.
