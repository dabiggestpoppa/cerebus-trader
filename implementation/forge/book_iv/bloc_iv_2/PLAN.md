# BOOK IV / BLOC IV.2 — HYBRID RETRIEVAL & EVIDENCE ROUTING
## PLAN — BA-27 RUNG 1 (PLANNING ONLY)

**Status:** Planning complete; implementation not started.
**Authority:** Operator-directed BA-27 Rung 1.
**Base HEAD:** `238c4da970f6d213053d6cae0c679d1dda404912`
**Branch:** `forge`
**Scope:** Book IV / Bloc IV.2 only. IV.1 is frozen and ratified.

---

## 0. FOUNDATION VERIFICATION

Verified against the working tree at the base HEAD, not from prior narrative.

| # | Check | Result |
|---|---|---|
| 1 | Local HEAD equals `origin/forge` | PASS — both `238c4da…` |
| 2 | Append-only ancestry from IV.1 ratification | PASS — `6ca573d` → `e4e1de4` → `82735e1` → `7dd9358` → `d1223db` → `238c4da` |
| 3 | Book I canonical schemas and retrieval compiler present | PASS — `app/forge/canonical.py`, `retrieval/{compiler,index,objects,query,service}.py` |
| 4 | Book II identity, authorization and exposure contracts present | PASS — `identity.py`, `policy.py`, `service/policy_enforcement.py` |
| 5 | Book II frozen hashes and planning pins | PASS — no diff under Book II paths; existing pin suite remains authoritative |
| 6 | Six Book III ratifications present | PASS — Book III integration suite previously measured 96/96; no Book III source changed in IV.1 or IV.2 |
| 7 | Book III integration suite | PASS — 96/96 at `d1223db`; IV.1 commits touched no Book III source |
| 8 | IV.1 implementation and ratification | PASS — `RATIFICATION.md` records PASS for IV.1 only |
| 9 | IV.1 tests and fixtures | PASS — 60/60 re-run at final HEAD; Q-01…Q-12 present |
| 10 | Actual `AskCerebusQueryPlan` contract | PASS — read `interpreter/plan.py`; frozen fields below |
| 11 | III.6 gateway, requests, snapshot DTOs, refusal vocabulary | PASS — `IntelligenceGateway`, `SnapshotRequest`, `SnapshotKey`, `GuardedRead` |
| 12 | `PROVIDER_SCHEMAS_V2` | PASS — provider schema registry remains the frozen V2 contract |
| 13 | WP-3B supplemental PASS | PASS — recorded and unchanged |
| 14 | Market data status | `NOT_CONFIGURED` — no live current state is claimable |
| 15 | Migrations | `[1,2,3,4]` present; no migration is added by IV.2 |
| 16 | Book II frozen routes | PASS — no route change in this rung |
| 17 | Starting-head CI | PASS — run `42403893954`, `test` and `postgres` both green |
| 18 | `.bu_tmp/` and unrelated files | PRESERVED — untracked, untouched |

### Frozen IV.1 plan fields consumed by IV.2

`query_contract_version`, `plan_id`, `intent`, `entities`, `model_ids`,
`setup_ids`, `market`, `layer`, `time_scope`, `requested_depth`,
`effective_depth`, `requires_live_intelligence`, `requires_evidence`,
`requires_lineage`, `requires_setup_context`, `actionable`,
`requested_fields`, `confidence`, `ambiguities`.

IV.2 adds no field to this contract and may not reinterpret an ambiguity as a
resolution.

---

## 1. MISSION AND CORE LAW

IV.2 consumes an immutable `AskCerebusQueryPlan` and produces the smallest
authorized `AuthorizedRetrievalBundle` of canonical references, claim/evidence
references, current-intelligence references, lineage references, supporting
passages, negative evidence, limitations, refusals and an exposure-safe trace.

**Structured canonical truth outranks semantic similarity. Authorization
precedes retrieval exposure. Evidence determines which numerical claims can be
supported.**

IV.2 never answers, never computes an eligibility verdict, never grants
entitlement, never manufactures a number and never substitutes a historical
snapshot for current state.

---

## 2. VERIFIED UPSTREAM API MAP

| Surface | Actual contract | IV.2 use |
|---|---|---|
| Book I index | `RetrievalIndex.require()`, `IndexGeneration.header()`, `.record()` | Read-only published generation; no build, no write |
| Book I service | `RetrievalService.retrieve(principal, context, RetrievalQuery, correlation_id)` | Policy-guarded candidate release |
| Exact lookup | `RetrievalService.exact(principal, context, canonical_id)` | Canonical identity resolution |
| Body load | `RetrievalService.load_record(...)` | Only after allow, only for bounded excerpt needs |
| Provenance | `RetrievalService.navigate(...) -> ProvenanceChain` | Claim → Evidence → Artifact join |
| Query | `RetrievalQuery(canonical_id, object_type, market, model_family, status, exposure, layer, source_artifact, provenance_relation, claim_identity, text, include_quarantine, limit)` | Translate plan identity into exact filters |
| Safe metadata | `RetrievalHeader` (`object_id`, `object_type`, `canonical_version`, `status`, `exposure`, `layer`, `market_scope`, `model_family`, `source_artifact_ids`) | Candidate selection before body load |
| Record | `RetrievalObject` with `structured`, `routing`, `leakage`, `conflict`, `support`, `qualifiers`, `related_ids`, `provenance` | Authorized reference and excerpt source |
| Support | `SupportAssessment(supported, classification, evidence_ids, gaps)` | Found vs supported; never a truth upgrade |
| Book II | `ForgePrincipal`, `AuthorizationContext`, `ResourcePolicyMetadata`, `DefaultDenyPolicyEngine` | Sole authorization authority |
| Enforcement | `ForgePolicyEnforcementService.guard(principal, context, action, resource, loader, *args, correlation_id=...)` | Deny-before-load primitive |
| III.6 requests | `SnapshotRequest`, `HistoricalRequest`, `InstrumentViewRequest`, `BasketViewRequest`, `SetupContextRequest` | Typed routing; no invented fields |
| III.6 gateway | `IntelligenceGateway.read(...) -> GuardedRead`, `.read_guarded(...)` | Policy-first current/historical reads |
| Snapshot identity | `SnapshotKey` with `instrument_id`, `model_id`, `model_version`, `layer`, `as_of`, `data_cutoff`, `calculation_version`, `clock_id`, `session_id` | Identity completeness check before request |
| Refusals | `RefusalError` codes incl. `MALFORMED_REQUEST`, `UNKNOWN_VERSION`, `PROVIDER_NOT_CONFIGURED` | Preserve governed refusal vocabulary |
| Setups | `SetupRegistry.resolve(setup_id, version, surface)`, canonical `SETUP.*` ids | Setup-card resolution and surface refusal |
| Setup surface | `SetupSurface.PRODUCTION/OPERATOR/RESEARCH/AUTOMATION`, `SetupEligibility` | Fib research-only and manual-no-automation routing |

No upstream module is modified by this plan.

---

## 3. ARCHITECTURE

Provisional package, subject to repository convention check at Rung 2:

```
app/forge/ask_cerebus/retrieval/
    __init__.py
    versions.py          RETRIEVAL_CONTRACT_V1, supported versions
    enums.py             RetrievalOutcome, PrecedenceTier, RejectionClass,
                         LimitationCode, RefusalCode, TraceClass, EvidenceJoinStatus
    refs.py              CanonicalRef, ClaimRef, EvidenceRef, IntelligenceRef,
                         LineageRef, SemanticPassage, NegativeRef
    bundle.py            AuthorizedRetrievalBundle, immutable payload, bundle_id
    query_builder.py     plan -> RetrievalQuery / resolver targets
    structured.py        exact identity, version, status, relationships
    semantic.py          SemanticIndexPort + DeterministicFakeSemanticIndex
    precedence.py        six-tier ordering and no-overwrite rules
    claims.py            claim/evidence join over ProvenanceChain
    intelligence.py      plan -> typed III.6 request or bounded refusal
    lineage.py           generation-sensitive expansion
    conflicts.py         identity-aware conflict classification
    negative.py          negative-evidence retention
    policy.py            thin adapter over the existing Book II guard
    trace.py             internal audit / consumer-safe / refusal traces
    service.py           orchestration: plan -> bundle
```

### 3.1 Bundle contract

`AuthorizedRetrievalBundle` is frozen and contains only references and
authorized bounded text:

| Field | Meaning |
|---|---|
| `query_plan_id` | Exact IV.1 plan id |
| `retrieval_contract_version` | `RETRIEVAL_CONTRACT_V1` |
| `bundle_id` | `BUNDLE.` + SHA-256 prefix over canonical payload |
| `canonical_refs` | Selected canonical objects: id, type, version, status, layer, market, exposure, support classification |
| `claim_refs` | Claim id, identity dimensions, status, evidence ids |
| `evidence_refs` | Evidence id, status, provenance refs, support gaps |
| `intelligence_refs` | Snapshot id/hash, view, quality outcome, no-go state, refusal |
| `lineage_refs` | Generation-tagged object and claim references, never merged |
| `semantic_passages` | Authorized object id, bounded excerpt, status, quote scope, support class |
| `negative_refs` | Failed, null, parked, superseded, falsified, no-go references |
| `limitations` | Bounded limitation codes with affected reference ids |
| `refusals` | Governed refusal/unavailability outcomes |
| `trace` | Internal audit trace reference and consumer-safe projection |
| `selected_generation` | Index generation and source fingerprint |

**No field may carry a probability, win rate, expectancy, target completion
rate, eligibility verdict, position size or order intent.**

### 3.2 Orchestration order (fixed)

1. Validate plan version and outcome; reject unsupported plan.
2. Resolve structured identities from `model_ids`, `setup_ids`, `entities`.
3. For every candidate, read only `RetrievalHeader`; authorize through the
   existing Book II guard.
4. Load only allowed records needed for references or bounded excerpts.
5. Expand aliases/lineage; never merge generations.
6. Join claims to evidence and provenance through `navigate()`.
7. Route Book III requests only when all required fields are supplied.
8. Run deterministic semantic search over the authorized candidate set.
9. Apply six-tier precedence and identity-aware conflict classification.
10. Attach negative evidence selected by the same policy filter.
11. Emit limitations, refusals and trace; compute deterministic `bundle_id`.

A denial at any step removes the object before its body is read; later stages
cannot resurrect it.

---

## 4. CHAPTER DESIGN AND REQUIREMENT INVENTORY

### IV.2.1 Structured resolver (R1–R7)

- R1 exact canonical id resolution.
- R2 safe-header-only selection before body load.
- R3 exact version/generation; no “latest” token.
- R4 governed alias expansion with no status promotion.
- R5 typed relationship traversal under policy.
- R6 explicit unresolved outcome.
- R7 no fuzzy creation or nearest-match invention.

Identity comes from the plan's canonical ids and the index. Unknown ids return
`UNRESOLVED_IDENTITY`; they are never replaced by a lexically similar object.
Setup ids use `SetupRegistry` verbatim; a version mismatch is
`SETUP_VERSION_DRIFT`, not a silent upgrade. Instrument ids are index-backed;
instrument syntax alone does not establish a snapshot.

### IV.2.2 Semantic resolver (R8–R13)

- R8 replaceable `SemanticIndexPort`.
- R9 search only over policy-authorized retrieval records.
- R10 semantic results cannot establish identity, version, status, win rate,
  probability, eligibility or exposure.
- R11 deterministic fake search for the first implementation.
- R12 real embeddings/vector service require later authorization.
- R13 a passage is supporting evidence only.

The port receives the normalized query, the authorized header set and a limit;
it never receives the full corpus or protected bodies. Implementation-time fake
results are fixture-defined and ordering-stable. No embedding provider, vector
service or network call is authorized in this rung.

### IV.2.3 Canonical priority (R14–R19)

- R14 frozen six-tier order.
- R15 structured canonical fact outranks semantic passage.
- R16 lower tier cannot overwrite higher-tier fact.
- R17 disagreement is recorded, not silently resolved.
- R18 semantic relevance score is not authority.
- R19 no semantic promotion of historical or research status.

Tiers: `DIRECT_CANONICAL`, `LINKED_CLAIM_EVIDENCE`, `CURRENT_INTELLIGENCE`,
`LINEAGE_DOCTRINE`, `SOURCE_DERIVED_PASSAGE`, `GENERAL_KNOWLEDGE`.
Sorting is `(tier, object_id, generation)`; scores are tie-break metadata only
inside tier 5 and are never a global ranking authority.

### IV.2.4 Claim/evidence join (R20–R26)

- R20 exact path Query → Model → Claim → Evidence → Provenance.
- R21 claim identity retained.
- R22 model/version retained.
- R23 metric, conditioning population, sample size, period and event definition
  retained when governed fields provide them.
- R24 evidence status and provenance refs retained.
- R25 OOS/reproduction status reported when available, absent honestly when not.
- R26 missing evidence yields `EVIDENCE_INSUFFICIENT` and no number.

The join uses `RetrievalService.navigate()`; `ProvenanceChain.missing` and
`.denied` become limitations, never reconstructed links. A claim with no
evidence may be referenced as `FOUND_UNSUPPORTED` only if policy allows and the
plan's evidence requirement does not require a verified number. No result may
be labeled `CANONICAL_VERIFIED` without an authoritative evidence join.

### IV.2.5 Book III live intelligence join (R27–R33)

- R27 `CURRENT` maps to `SnapshotRequest` and `IntelligenceGateway`.
- R28 level requests carry layer, level kind and state.
- R29 setup context carries canonical card id, version and parent states.
- R30 historical requests carry explicit model version and cutoff; no
  historical-to-current promotion.
- R31 instrument views carry quality outcome and source cutoffs.
- R32 JPY basket context only where the typed basket request supports it.
- R33 unresolved required fields produce a bounded refusal, never invented
  model version, cutoff, calculation version, clock or snapshot hash.

At this head `market_data: NOT_CONFIGURED`; every `CURRENT` bundle therefore
carries `PROVIDER_NOT_CONFIGURED` and no current market fact. `NO_GO_ACTIVE`
remains a market-state restriction, distinct from missing provider, stale data
or unresolved fields. A historical snapshot is never substituted.

### IV.2.6 Alias and generation routing (R34–R39)

- R34 P90 / P90P / PHI generation preserved.
- R35 ST / Base80 generation preserved; ST manual is never automated.
- R36 session/clock and old Markov/Fib generations preserved.
- R37 BTC Game and BTC Tracker remain distinct identities.
- R38 lineage expansion adds references but never merges claims or statistics.
- R39 an unavailable original generation never resolves to the newest model.

The IV.1 ambiguities (`UNAVAILABLE_GENERATION`, `UNSUPPORTED_IDENTITY`,
`MATERIAL_AMBIGUITY`) are carried into the bundle unchanged; IV.2 may add
limitations but may not remove or downgrade them.

### IV.2.7 Conflict resolution (R40–R45)

- R40 compare identity before contradiction.
- R41 matched identity + conflicting evidence preserves both.
- R42 different identity separates claims; no manufactured contradiction.
- R43 no majority vote or similarity score as numerical winner.
- R44 `supersedes`/`contradicts` metadata retained.
- R45 conflicting evidence remains visible with statuses intact.

Comparison fields: instrument, market, event identity, conditioning population,
model/version, clock/session, horizon, metric definition, tolerance, eligibility
assumptions, research period and implementation semantics. Same identity plus
different supported values is `EVIDENCE_CONFLICT`; different identity is
`INCOMPARABLE_EVIDENCE`, not conflict.

### IV.2.8 Negative evidence (R46–R50)

- R46 failed and null findings are retrievable.
- R47 parked, superseded, falsified and no-go objects are retrievable as
  negative references.
- R48 retrieval never biases toward positive outcomes.
- R49 negative status and generation are retained.
- R50 negative research evidence is not a current trading signal.

Negative evidence passes the same policy filter as positive evidence. Excluding
it from candidate generation is a defect, not an optimization.

### IV.2.9 Entitlement prefilter (R51–R57)

- R51 authorization runs before any retrieval exposure.
- R52 deny-before-load is preserved for every candidate and hop.
- R53 researcher depth never grants exposure.
- R54 guessing a hidden object id does not reveal its existence.
- R55 semantic neighbors cannot bypass policy.
- R56 citation/source URLs cannot bypass policy.
- R57 repeated queries cannot enumerate hidden objects.

Book II remains the only authorization engine. IV.2 contains no second exposure
matrix. Denied entries expose no title, text, status, generation or object
existence beyond the minimum uniform refusal.

### IV.2.10 Retrieval trace (R58–R64)

- R58 trace binds plan id and retrieval contract version.
- R59 trace lists only authorized selected references.
- R60 trace reports rejection counts by reason class.
- R61 internal audit, consumer-safe and refusal traces are distinct.
- R62 trace contains no forbidden object names, protected text or secrets.
- R63 consumer projection is exposure-safe and replay-stable.
- R64 deterministic manifest digest; protected content is not retained.

Trace fields: plan id, contract version, index generation, source fingerprint,
selected ids, evidence/claim ids, snapshot ids when available, selected
generation, rejection counts by `RejectionClass`, outcome, limitations and
digest. Internal trace may include reason classes and generation metadata;
consumer trace carries selected ids and outcome only; refusal trace carries a
governed code and no protected identity.

---

## 5. DETERMINISM

- Canonical JSON: sorted keys, compact separators, UTF-8, LF.
- No wall clock, randomness, iteration-order dependence or locale sorting.
- `bundle_id` = `BUNDLE.` + first 32 hex of SHA-256 over the payload excluding
  the id.
- Ordering: tier, then object id, then generation.
- Same plan + same index generation + same policy context ⇒ byte-identical
  bundle.
- A changed index/source fingerprint changes `selected_generation` and the
  bundle id; it never silently reuses a prior result.

---

## 6. TEST AND FIXTURE STRATEGY

72 executable tests, `A-01`–`A-72`, in
`tests/test_forge_ask_cerebus_retrieval.py`.

| Family | Tests | Requirements |
|---|---|---|
| T1 structured canonical resolution | A-01–A-07 | R1–R7 |
| T2 semantic authorization | A-08–A-13 | R8–R13 |
| T3 ranking and precedence | A-14–A-19 | R14–R19 |
| T4 claim/evidence joins | A-20–A-26 | R20–R26 |
| T5 Book III intelligence join | A-27–A-33 | R27–R33 |
| T6 generation and lineage | A-34–A-39 | R34–R39 |
| T7 conflict resolution | A-40–A-45 | R40–R45 |
| T8 negative evidence | A-46–A-50 | R46–R50 |
| T9 authorization and exposure | A-51–A-57 | R51–R57 |
| T10 retrieval tracing | A-58–A-64 | R58–R64 |
| T11 determinism and failure handling | A-65–A-68 | cross-cutting |
| T12 frozen integrity | A-69–A-72 | cross-cutting |

Every requirement maps to exactly one base driver; T11/T12 add adversarial and
integrity checks. No test may be skipped, xfailed, renamed or weakened. The
exact names are frozen in `ACCEPTANCE.md`.

18 golden scenarios `Q2-01`–`Q2-18` cover exact definition, model description,
supported and unsupported numbers, BTC collision, P90 history, current Gold
without provider, setup no-go, XAU WATCH, Fib research-only, JPY manual
confirmation, same-identity conflict, incomparable identities, negative
research, unauthorized id, unauthorized semantic neighbor, unavailable
historical snapshot and semantic text conflicting with canonical fact.

---

## 7. FEASIBILITY SUMMARY

64 requirements classified in `FEASIBILITY_GATE.md`:

- **F1 — directly supported by Book I/II/III contracts:** 19
- **F2 — implementable through new deterministic IV.2 logic:** 39
- **F3 — requires later Book IV/VI/VII implementation:** 3
- **F4 — missing canonical authority, source data or governed infrastructure:** 3

Green deterministic tests do not close the F3/F4 capabilities. A bounded
refusal satisfies the IV.2 contract without proving production retrieval
readiness.

---

## 8. NON-GOALS AND STOP CONDITIONS

Not authorized in IV.2 Rung 1 or Rung 2 without a later directive:

- LLM calls, OpenRouter, prompt construction or answer generation.
- Embedding providers, vector databases or external semantic services.
- Market-data provider connection or synthetic current values.
- Book I/II/III source changes, migrations or route changes.
- Entitlement grants, eligibility verdicts, execution or order intent.
- Treating a historical snapshot, doctrine or semantic passage as current fact.
- Removing or downgrading IV.1 ambiguity flags.
- Declaring Book IV complete.

Stop if a required fact cannot be obtained through an existing governed
contract. Record the refusal and the missing authority; do not invent it.

---

## 9. READINESS VERDICT

**READY FOR IV.2 RUNG 2 IMPLEMENTATION** under the frozen requirement
inventory, test names and fixtures, with F3/F4 dependencies explicitly open.
No implementation code has been written in this rung.
