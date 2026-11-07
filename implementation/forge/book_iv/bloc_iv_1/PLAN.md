# BOOK IV / BLOC IV.1 — QUERY INTERPRETER & ROUTER — PLAN.md

**Bloc:** IV.1 · **Book:** IV (Ask CEREBUS) · **Rung:** BA-26 Rung 1
**Mode:** planning only — no code, no LLM, no retrieval, no answer generation
**Starting head:** `1df1b1d7ee63e570539c7af6dad8b99f78ee07dc`
(directive expected `9dcd63b`; that commit is an ancestor and the two later
commits are the authorized shallow-checkout repair and CI receipt)
**Branch:** `forge`

---

## 1. Objective and core law

Convert a user question into a typed, canonical, policy-aware query plan
without answering it.

**The interpreter determines what the user is asking. Canonical knowledge
determines what exists. Book III determines current market facts. Book II
determines access. Evidence determines which numerical claims are supportable.
The LLM explains only what those authorities permit.**

IV.1 owns language → plan. It owns no fact, no eligibility, no exposure
decision and no statistic.

```
text + principal context + query-contract version
  -> deterministic intent/entity/depth/scope/actionability/evidence classification
  -> AskCerebusQueryPlan (immutable, versioned, serializable)
  -> IV.2 retrieval / III.6 snapshot join (downstream, not this Bloc)
```

---

## 2. Phase 0 verification (actual read, not prior reports)

| # | Check | Result |
|---|---|---|
| 1 | Local HEAD == `origin/forge` == `1df1b1d` | PASS |
| 2 | `9dcd63b` ancestry (expected starting head) | PASS |
| 3 | Book I canonical kernel and retrieval aliases present | PASS (`app/forge/canonical.py`, `retrieval/aliases.py`) |
| 4 | Book I freeze manifest / corpus | PASS (untouched) |
| 5 | Book II 50/50 contract hashes, 23/23 planning pins | PASS (reported by prior freeze records; no Book II file changed) |
| 6 | Book III six ratified blocs, 79 modules | PASS (11/12/13/13/16/14) |
| 7 | Book III integration acceptance | PASS (96/96 at this head) |
| 8 | III.6 snapshot/intelligence contracts | PASS (`Snapshot`, `SnapshotRequest`, `IntelligenceGateway`, refusals) |
| 9 | III.1 amendment + `FREEZE_DELTA_V2` | PASS (`PROVIDER_SCHEMAS_V2`, aggregate `6c8d903f…`) |
| 10 | WP-3B supplemental PASS | PASS (`RATIFICATION_WP3B_SUPPLEMENT_V2.md`) |
| 11 | Provider readiness | PASS `market_data: NOT_CONFIGURED`, `required: false` |
| 12 | Frozen router | PASS (`routes.py` hash `145757e0…d190af`) |
| 13 | Migrations | PASS `001`–`004` |
| 14 | Starting CI | PASS run `42383965383` (both jobs) |
| 15 | Working tree | only pre-existing `?? .bu_tmp/` |

No Ask CEREBUS package exists yet; `app/forge/ask_cerebus/` is absent.
No Book IV implementation is authorized by this rung.

---

## 3. Frozen requirement inventory (R1–R53)

Nine chapters from
`planning/forge/books/BOOK_IV_ASK_CEREBUS_PLAN_V1.md` § *BLOC IV.1*, plus the
six frozen Acceptance IV.1 bullets. Requirements are numbered for binding
traceability; they do not replace the frozen chapter text.

### Ch IV.1.1 — Intent taxonomy (R1–R12)

| ID | Requirement |
|---|---|
| R1 | Classify definition/explanation |
| R2 | Classify model description |
| R3 | Classify current state |
| R4 | Classify level/coordinate |
| R5 | Classify setup/operator context |
| R6 | Classify statistic/evidence |
| R7 | Classify comparison |
| R8 | Classify historical lineage |
| R9 | Classify methodology/research |
| R10 | Classify indicator/vault navigation |
| R11 | Classify troubleshooting |
| R12 | Classify general market knowledge |

### Ch IV.1.2 — Entity resolution (R13–R20)

| ID | Requirement |
|---|---|
| R13 | Resolve instruments to canonical Book I/III ids |
| R14 | Resolve model families to canonical model ids |
| R15 | Resolve setup identities to canonical setup ids |
| R16 | Resolve canonical terms and aliases without rewriting them |
| R17 | Resolve L1/L2/L3 layer vocabulary |
| R18 | Resolve timeframe/session vocabulary |
| R19 | Resolve generation/version references |
| R20 | Guard identity collisions (BTC Game ≠ BTC Tracker) |

### Ch IV.1.3 — Depth selection (R21–R24)

| ID | Requirement |
|---|---|
| R21 | `BEGINNER` classification |
| R22 | `OPERATOR` classification |
| R23 | `RESEARCHER` classification |
| R24 | Cap effective depth at the principal's authorized maximum without granting entitlement |

### Ch IV.1.4 — Temporal scope (R25–R30)

| ID | Requirement |
|---|---|
| R25 | `CURRENT` classification requiring Book III current intelligence |
| R26 | `AS_OF` classification with explicit cutoff |
| R27 | `HISTORICAL_RESEARCH` classification |
| R28 | `MODEL_VERSION` classification with pinned version |
| R29 | `GENERAL` classification with no live requirement |
| R30 | Never substitute historical/corpus knowledge for current data; never silently use latest version |

### Ch IV.1.5 — Actionability detector (R31–R33)

| ID | Requirement |
|---|---|
| R31 | Detect entry/target/stop/position/“what should I do” language |
| R32 | Mark `requires_setup_context` for actionable requests |
| R33 | Never approve an action, produce a verdict or imply eligibility |

### Ch IV.1.6 — Numerical-claim detector (R34–R36)

| ID | Requirement |
|---|---|
| R34 | Detect requests for rate/probability/WR/N/correlation/median/tier boundary/target rate/expectancy/timing/backtest statistics |
| R35 | Set `requires_evidence = true` for research statistics |
| R36 | Distinguish an authorized deterministic current measurement from a research claim; still never answer it |

### Ch IV.1.7 — Historical-generation detector (R37–R40)

| ID | Requirement |
|---|---|
| R37 | Recognize P90 historical generations |
| R38 | Recognize Atomic/ST/Base80 and Wednesday/Afternoon generations |
| R39 | Recognize earlier Markov and Fib generations |
| R40 | Preserve original generation identity; never promote historical to current by terminology overlap |

### Ch IV.1.8 — Ambiguity policy (R41–R47)

| ID | Requirement |
|---|---|
| R41 | `RESOLVED` outcome when one interpretation is unambiguous |
| R42 | `RESOLVED_WITH_EXPLICIT_SCOPE` when scope is disambiguated by the request |
| R43 | `MATERIAL_AMBIGUITY` when candidate interpretations change the authorized answer |
| R44 | `UNSUPPORTED_IDENTITY` when no canonical identity exists |
| R45 | `UNAVAILABLE_GENERATION` when a historical generation cannot be resolved |
| R46 | Preserve candidate identities and structured reasons |
| R47 | Never fabricate confidence percentages; never silently substitute a different model or instrument |

### Ch IV.1.9 — Typed query plan (R48–R53)

| ID | Requirement |
|---|---|
| R48 | Emit `AskCerebusQueryPlan` with the frozen fields |
| R49 | Carry resolved model/setup ids separately from raw entities |
| R50 | Carry market and layer without inventing either |
| R51 | Carry time scope, requested depth and effective depth |
| R52 | Carry live/evidence/lineage requirement flags and actionability |
| R53 | Plan is immutable, versioned, deterministically serializable and carries ambiguities/requested fields |

---

## 4. Typed query plan

Frozen fields (directive §3), no additions that carry authority:

| Field | Type | Rule |
|---|---|---|
| `intent` | `Intent` enum (12 values) | exactly one primary intent; secondary intents in `requested_fields` only if explicitly named |
| `entities` | `tuple[EntityRef, ...]` | ordered, deduplicated, unresolved candidates preserved |
| `model_ids` | `tuple[str, ...]` | canonical ids only; empty when unresolved |
| `setup_ids` | `tuple[str, ...]` | canonical ids only; empty when unresolved |
| `market` | `str \| None` | from canonical instrument identity, never guessed |
| `layer` | `Layer \| None` | L1/L2/L3/CROSS_LAYER; `None` when not stated |
| `time_scope` | `TimeScope` enum (5 values) | frozen vocabulary |
| `requested_depth` | `Depth` enum | what the user asked for |
| `effective_depth` | `Depth` enum | `min(requested, max_authorized)`; computed, never an entitlement grant |
| `requires_live_intelligence` | `bool` | true iff `time_scope is CURRENT` |
| `requires_evidence` | `bool` | true for research statistics |
| `requires_lineage` | `bool` | true for historical/generation/AS_OF questions |
| `actionable` | `bool` | request asks for an action/decision |
| `requested_fields` | `tuple[str, ...]` | bounded field names the user asked for (e.g. `state`, `levels`, `invalidation`) |
| `confidence` | `PlanConfidence` enum | `CERTAIN`, `EXPLICIT_SCOPE`, `AMBIGUOUS`, `UNSUPPORTED` — never a number |
| `ambiguities` | `tuple[Ambiguity, ...]` | structured codes + candidates + material flag |
| `query_contract_version` | `str` | e.g. `ASK_QUERY_CONTRACT.V1` |
| `plan_id` | `str` | deterministic hash of the plan content + contract version |

Inputs (not plan fields): authenticated principal scope, policy fingerprint,
maximum authorized depth (supplied by Book II/VI enforcement), and the
query-contract version. The interpreter never reads entitlements itself; it
receives an already-authorized ceiling.

Invariants:

1. No field accepts a caller-supplied verdict, eligibility, exposure,
   execution class, statistic, probability or snapshot id.
2. `effective_depth` cannot exceed the injected `max_authorized_depth`.
3. `requires_live_intelligence` and `time_scope` cannot disagree.
4. `requires_evidence` cannot be false for a detected research statistic.
5. `actionable` and `requires_setup_context` are separate fields.
6. Serialization is canonical JSON (sorted keys, no floats, no wall clock),
   so identical inputs yield identical `plan_id`.

---

## 5. Entity resolution strategy

Deterministic, ordered, non-fuzzy:

1. **Exact canonical id** (`MOD.*`, `SET.*`, `CL.*`, `EV.*`, `TERM.*`) parsed
   by `app/forge/canonical.py::CanonicalId`; invalid → `UNSUPPORTED_IDENTITY`.
2. **Exact canonical symbol** through the Book I/III instrument registry
   (`EURUSD`, `XAUUSD`, `BTCUSD`, `USDJPY`, `AUDJPY`, `EURJPY`).
3. **Source-backed alias** through `InstrumentRegistry` provider mappings and
   `retrieval/aliases.py::HISTORICAL_ALIASES` — exact, case-insensitive, no
   similarity threshold, no embedding.
4. **Family vocabulary** with explicit members (`XAU Game`, `EUR Weekly`,
   `BTC Tracker`, `JPY Carry`, `Fib`, `P90`, `ST`).
5. **Unresolved** → keep the raw phrase as an unresolved `EntityRef` with
   `UNSUPPORTED_IDENTITY`; never invent an id.

Collision rules (acceptance-critical):

- **BTC Game ≠ BTC Tracker.** `BTC Game` is research/artifact vocabulary, not
  launch-canonical; it must resolve only to its own research identity or to
  `UNSUPPORTED_IDENTITY` — never to BTC Tracker.
- **Historical P90 ≠ current P90.** A P90 phrase without a generation marker
  is `MATERIAL_AMBIGUITY` or `HISTORICAL_RESEARCH` with generation candidates;
  it is never upgraded to current.
- **ST manual framework ≠ automated Setup Card.** The plan records
  `MANUAL_OPERATOR` doctrine and never marks automation.
- **XAU Game interpretation ≠ eligible XAU trade.** Model description is not
  setup eligibility; `actionable` stays false for explanatory questions.
- **Fib historical rekey ≠ approved production setup.** Fib/Range Birth
  remains research/operator with production gated; the plan says
  `requires_setup_context` but never `ELIGIBLE`.

---

## 6. Depth policy

- `requested_depth` comes from explicit user language (`beginner`, `operator`,
  `researcher`) or the intent's recommended default.
- `max_authorized_depth` is injected from Book II policy/Book VI capability
  projection; the interpreter has no access to entitlements.
- `effective_depth = min(requested_depth, max_authorized_depth)`.
- When capped, `ambiguities` gains a non-material `DEPTH_CAPPED` note and the
  plan never claims the higher mode.
- Depth changes explanation detail only. It cannot change facts, evidence,
  exposure, eligibility, market state or model version.

---

## 7. Temporal policy

| Scope | Trigger | Live? | Lineage? |
|---|---|---|---|
| `CURRENT` | “now”, “today”, “current”, “doing” | yes | no (unless generation named) |
| `AS_OF` | explicit timestamp/cutoff | no | yes |
| `HISTORICAL_RESEARCH` | “historical”, “backtest”, “old”, generation names | no | yes |
| `MODEL_VERSION` | explicit model version/generation | no | yes |
| `GENERAL` | definitions, doctrine, “what is” | no | no |

- `CURRENT` plus unavailable provider still produces the correct plan; IV.2/
  III.6 will return the governed unavailability outcome.
- No historical corpus fact may satisfy a `CURRENT` question.
- No `latest`/`current` version token is accepted as a pinned version; it
  yields `UNKNOWN_VERSION`-class ambiguity.

---

## 8. Actionability and numerical claims

Actionability triggers: enter/exit/hold, buy/sell/short/long, target, stop,
position size, “should I”, “is it safe”, “what do I do”.

- `actionable = true`, `requires_setup_context = true`.
- The plan never carries an eligibility value; only the request for context.
- A model-description question (“what does Gold Game mean?”) is not actionable.

Numerical triggers: win rate, probability, odds, N, sample, correlation,
median, expectancy, tier boundary, target completion, timing distribution,
backtest result, “132% target”.

- `requires_evidence = true`.
- The interpreter does not compute, validate or restate any figure.
- An authorized deterministic current measurement is still only classified;
  whether it may be served is IV.2/III.6/IV.5 work.

---

## 9. Historical generations

Recognized families and their generation markers: P90 (and P90P, PHI
ancestors), Atomic/ST, Base80, Wednesday/Afternoon, earlier Markov states,
earlier Fib generations, Range Birth/Rekey vocabulary.

Rules:

- Preserve the user's generation token in `EntityRef.generation` and in
  `ambiguities` when it cannot be resolved.
- Never rewrite an old term into its modern descendant as if identical.
- A generation that cannot be resolved yields `UNAVAILABLE_GENERATION`; it is
  not silently mapped to the newest model.
- Statistics never migrate between generations; the plan flags lineage and
  evidence but does not carry results.

---

## 10. Ambiguity

`AmbiguityReason` (closed): `AMBIGUOUS_MODEL`, `AMBIGUOUS_INSTRUMENT`,
`AMBIGUOUS_GENERATION`, `AMBIGUOUS_LAYER`, `AMBIGUOUS_DEPTH`, `AMBIGUOUS_TIME`,
`UNSUPPORTED_IDENTITY`, `UNAVAILABLE_GENERATION`, `DEPTH_CAPPED`,
`UNSUPPORTED_STATISTIC`.

Only material ambiguity requests clarification. Immaterial ambiguity is
resolved with explicit scope. No numeric confidence is emitted.

---

## 11. III.6 gateway integration (future)

IV.1 plans, III.6 provides facts. Mapping:

| Plan element | III.6 contract |
|---|---|
| `CURRENT` + instrument/model/layer | `SnapshotRequest` (`instrument_id`, `model_id`, `model_version`, `layer`, `as_of`, `data_cutoff`, `calculation_version`) |
| `AS_OF`/`HISTORICAL_RESEARCH`/`MODEL_VERSION` | `HistoricalRequest` with pinned version/cutoff and `retention_acknowledged` |
| setup context | `SetupContextRequest(setup_id, setup_version, surface)` |
| multi-layer question | `InstrumentViewRequest` |
| JPY basket | `BasketRequest(basket_id="JPY")` |
| live unavailability | III.6 refusals `PROVIDER_NOT_CONFIGURED`, `STALE_DATA`, `DATA_QUALITY_BLOCKED` |

The plan carries no `snapshot_id`/`snapshot_hash`: identity is derived by III.6
from the key, never accepted from a client. No gateway call is implemented in
IV.1.

---

## 12. Proposed package and modules

Path checked against repository conventions (`app/forge/<domain>/`):

```
app/forge/ask_cerebus/interpreter/
  __init__.py        bounded public surface
  versions.py        ASK_QUERY_CONTRACT_V1
  enums.py           Intent, Depth, TimeScope, PlanConfidence, AmbiguityReason
  entities.py        EntityRef, canonical resolution ports
  depth.py           requested/effective depth
  temporal.py        scope classification
  actionability.py   action detection
  numerical.py       statistic detection
  generations.py     generation vocabulary
  ambiguity.py       outcomes and candidate preservation
  plan.py            frozen AskCerebusQueryPlan + canonical serialization
  interpret.py       pure `interpret(text, context) -> AskCerebusQueryPlan`
  refusals.py        bounded interpreter refusals
```

No imports of LLM/provider/network code. Imports only `canonical`,
`retrieval.aliases`, `model_runtime.contract.Layer`, and read-only
`intelligence_api` types where required for compatibility checks.

---

## 13. Proposed tests and fixtures

`tests/test_forge_ask_cerebus_interpreter.py` — **60 tests** (A-01–A-60) in
T1–T12, derived from R1–R53 plus seven adversarial cases. Zero skipped, zero
xfailed. Full inventory and coverage in `ACCEPTANCE.md`.

Golden fixtures: `implementation/forge/book_iv/bloc_iv_1/fixtures/` with
`FIXTURE_MANIFEST.json` and 12 versioned questions (see `ACCEPTANCE.md` §5).
Fixtures assert interpretation only, never market truth.

---

## 14. Non-goals (this Bloc)

- No retrieval, no semantic search, no context packaging.
- No LLM/OpenRouter connection, prompt or answer generation.
- No snapshot fetch, no market calculation, no eligibility evaluation.
- No UI, persistence, migration or route registration.
- No change to Book I/II/III source or tests.
- No IV.2–IV.6 implementation.

---

## 15. Stop conditions

1. A Book I identity/alias is missing or contradictory.
2. A Book II exposure/entitlement decision would have to be made in IV.1.
3. An intent would require inventing a taxonomy value.
4. A generation cannot be represented without promoting it.
5. A current-state plan would require a live provider or fabricated snapshot.
6. A test would need an LLM call to pass.
7. Any upstream frozen file would have to change.

---

## 16. Rung 2 readiness

Ready when: four planning documents committed, 53 requirements and 60 tests
machine-consistent, F1–F4 counts reconciled, no source change, CI green.
Rung 2 may then implement the interpreter package and fixtures only.
