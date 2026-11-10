# Evidence-path coverage V1 (F-06)

Contract: `ASK_EVALUATION_EVIDENCE_PATH_V2`
(`app/forge/ask_cerebus/evaluation/evidence_path.py`).

The V1 matcher asked whether a citation *resolved*. This contract asks whether
the answer travelled the path the question requires:

    query intent -> canonical model -> claim -> evidence -> authorized package
    -> manifest -> final citation

Expectations are declared from the frozen case records and the Book I catalog in
`implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py`. None is read
from a retrieval result, a draft, an answer or an earlier report. The evaluator
imports no interpreter, retrieval, context, gateway or answer module (EC-17
parses its imports with `ast`).

## 1. The V1 CHAIN population, reconciled individually

Five of the 120 V1 cases are CHAIN. All five are positives. Four cited only a
`PLAN.*` pseudo-item; each was reconciled from its frozen query text.

| Case | Question | Reconciled source | Trace | Package | Cited | Verdict |
|---|---|---|---|---|---|---|
| EV-001 | What does rekey mean in the EUR daily model? | Definitional; no canonical model object exists | none | `PLAN.d4acd718…` | `PLAN.d4acd718…` | DEFINITIONAL_PLAN_SOURCE — plan-only is the authorized source |
| EV-002 | What does tier mean in CEREBUS? | CEREBUS vocabulary, not a model | none | `PLAN.b1258aa5…` | `PLAN.b1258aa5…` | DEFINITIONAL_PLAN_SOURCE — plan-only is the authorized source |
| EV-006 | Show me the BTC Tracker state. | `MOD.BTC.TRACKER.V1` | `CL.BTC.TRACKER.V1`, `MOD.BTC.TRACKER.V1` | 3 objects incl. `MOD.BTC.TRACKER.V1` | `MOD.BTC.TRACKER.V1` | CANONICAL_PATH — PASS |
| EV-007 | What does the EUR weekly direction say? | Model state, but Book I has no EUR weekly model | none | `PLAN.26a6eee5…` | `PLAN.26a6eee5…` | CORPUS_ABSENT — recorded, excluded from scoring |
| EV-010 | Explain the JPY basket confirmation. | Model state, but Book I has no JPY carry model | none | `PLAN.c312dc50…` | `PLAN.c312dc50…` | CORPUS_ABSENT — recorded, excluded from scoring |

Two of the four plan-only cases are **correct**: a definitional question about a
term has no canonical object, and a plan-level pseudo-item is the authorized
source. Two are **not** system defects either: the question asks for model state
the frozen catalog does not contain, so no retrieval could select it. Those are
Book I coverage limits, recorded as `CORPUS_ABSENT` and excluded from the
denominator with that reason — not counted as successes and not rewritten into
passing expectations. This is the honest outcome of the reconciliation, and it
is why the corpus below exists: a positive control only proves evidence-path
precision when the canonical object actually exists.

Before this contract, four of five V1 CHAIN positives had **no per-case
canonical expectation** — F-06's original finding. They have one now, and the
two corpus-absent cases are visible as gaps instead of passing silently.

## 2. Additive corpus V2 (EV-145–EV-154)

Digest `aa7caee0a798deb4775192fe64026a1736341763a74947d8fa85d52df0d3eed2`,
10 CHAIN cases, all executed end to end (interpreter, retrieval, context,
gateway, validate). Nine declare a canonical model path; one declares that no
model exists for its question and asserts no substitution.

| Case | Question | Declared canonical source | Trace | Package | Cited | Verdict |
|---|---|---|---|---|---|---|
| EV-145 | Show me the BTC Game state. | `MOD.BTC.GAME.V1` | `CL.BTC.GAME.V1`, `MOD.BTC.GAME.V1` | 3 objects | `MOD.BTC.GAME.V1` | PASS |
| EV-146 | Show me the Gold Game state. | `MOD.XAU.GAME.V1` + `EV.XAU.SUPPORTED.V1` | 3 objects | 4 objects | `MOD.XAU.GAME.V1` | PASS |
| EV-147 | Compare the BTC Game and the BTC Tracker. | `MOD.BTC.GAME.V1` + `MOD.BTC.TRACKER.V1` | 4 objects | 5 objects | `MOD.BTC.GAME.V1` | PASS |
| EV-148 | Show me the ST manual state. | `MOD.ST.MANUAL.V1` | `MOD.ST.MANUAL.V1` | 2 objects | `MOD.ST.MANUAL.V1` | PASS |
| EV-149 | Explain the ST manual. | `MOD.ST.MANUAL.V1` | `MOD.ST.MANUAL.V1` | 2 objects | `MOD.ST.MANUAL.V1` | PASS |
| EV-150 | What does the BTC Tracker show? | `MOD.BTC.TRACKER.V1` | 2 objects | 3 objects | `MOD.BTC.TRACKER.V1` | PASS |
| EV-151 | Show me the Fib range birth state. | `MOD.FIB.RANGE_BIRTH.V1` + `EV.FIB.NEGATIVE.V1` | 3 objects | 4 objects | `MOD.FIB.RANGE_BIRTH.V1` | PASS |
| EV-152 | Show me the BTC Tracker state. | `MOD.BTC.TRACKER.V1` | 2 objects | 3 objects | `MOD.BTC.TRACKER.V1` | PASS |
| EV-153 | Compare the Gold Game and Gold Game V2. | `MOD.XAU.GAME.V1` + `EV.XAU.SUPPORTED.V1` | 3 objects | 4 objects | `MOD.XAU.GAME.V1` | PASS |
| EV-154 | Show me the Gold comparison state. | none — no comparison model exists | none | plan object | `PLAN.9a4e7f5c…` | PASS (no substitution) |

Nine canonical paths and one legitimate plan-only control: **10/10 pass**, and
the ten checks per case include trace selection, package inclusion, manifest
agreement with the package, claim-to-evidence join, citation support, generation
(where declared), and the absence of unauthorized packaged evidence.

## 3. Negative controls (constructed observations, not weakened assertions)

Each control mutates one part of a real observation and must fail.

| Control | Mutation | Failed check(s) |
|---|---|---|
| Wrong model, fluent answer | expected `MOD.BTC.GAME.V1`, observed `MOD.BASE80.V1` | `model_selected_in_trace`, `citation_supports_expected_source` |
| `PLAN.*` substituted for required evidence | citations replaced by a plan id | `not_plan_only`, `citation_supports_expected_source` |
| Right statistic, wrong generation | claim generation `XAU.GAME.2024` against declared `P90.V1` | `generation_matches` |
| Authorized but irrelevant citation | `MOD.BASE80.V1` cited for a Gold Game comparison | `citation_supports_expected_source` |
| Expected evidence missing | `EV.XAU.SUPPORTED.V1` dropped from the package | `evidence_refs_packaged` |
| Retrieved but not packaged | model removed from package and manifest | `model_packaged`, `model_in_manifest` |
| Final answer drops the citation | citations emptied | `citation_supports_expected_source`, `not_plan_only` |
| Unauthorized evidence added | `MOD.XAU.SECRET.V1` packaged without selection | `no_unauthorized_package_evidence` |
| Manifest identity lost | manifest id blanked | `manifest_identity_recorded` |
| Plan-only for a canonical question | whole package replaced by a plan id | `not_plan_only`, `model_packaged` |

A shaped answer citing an unrelated but resolvable object cannot pass: the
citation check is against the declared model or its evidence, not against
resolvability.

## 4. Metric

`chain_evidence_path_correctness` = **10/10** (MEASURED).
Eligible: EV-006, EV-145–EV-153. Excluded with reasons: EV-001 and EV-002
(`DEFINITIONAL_PLAN_SOURCE`), EV-007 and EV-010 (`CORPUS_ABSENT`), EV-154
(`PLAN_ONLY_NO_MODEL`).

`citation_support_correctness` = **10/10** over the same population.

## 5. Finding F-09 — historical-lineage questions never reach admission

While authoring the corpus I probed model-state questions for catalog objects
whose intent is `HISTORICAL_LINEAGE`:

| Query | Intent | Retrieval | Package | Outcome |
|---|---|---|---|---|
| Show me the P90 historical state. | HISTORICAL_LINEAGE | `CL.P90.V1`, `MOD.P90.V1` | 3+ objects | **ERROR** (no validated answer) |
| Show me the Base80 state. | HISTORICAL_LINEAGE | `MOD.BASE80.V1` | 2+ objects | **ERROR** (no validated answer) |
| Show me the Markov legacy state. | HISTORICAL_LINEAGE | `MOD.MARKOV.LEGACY.V1` | 2+ objects | **ERROR** (no validated answer) |

Retrieval and packaging succeed; the gateway admits no task for that intent, so
`_chain_gateway` produces nothing to validate. This is a reachability gap in the
IV.2 task mapping or IV.4 admission path, not a Book I or IV.5 defect, and it is
outside this rung's authorized scope (no IV.1–IV.5 change). It is recorded as
**F-09, S3, owner IV.2/IV.4, OPEN**, with the three probes above as evidence. The
three corpus cases were re-authored onto answerable intents rather than
enshrining an ERROR as expected behaviour; the gap is documented here and in
`EVALUATION_COVERAGE_SUPPLEMENT_V1.md` §5. It is not scored away and not counted
as coverage.

## 6. What this document does not claim

- No V1 expectation was rewritten; the historical record stands.
- No product module changed to make a path pass.
- The two `CORPUS_ABSENT` cases remain uncovered by design: adding an EUR weekly
  or JPY carry model is a Book I corpus decision, not an evaluation change.
- `HISTORICAL_LINEAGE` model descriptions remain unanswerable until F-09 is
  authorized for repair.
