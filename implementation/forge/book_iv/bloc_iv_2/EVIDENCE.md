# BOOK IV / BLOC IV.2 — EVIDENCE
## HYBRID RETRIEVAL & EVIDENCE ROUTING — BA-27 RUNG 2

**Base HEAD:** `38b322b562317fdd42ad8ea61a9866b2931966a7`
**Contract:** `RETRIEVAL_CONTRACT_V1`
**Evidence date:** 2026-11-07
**Scope:** Book IV / Bloc IV.2 only

This record contains measured results. It does not close Book IV, the six
F3/F4 capabilities, or production retrieval readiness.

---

## 1. PHASE 0 — FOUNDATION VERIFICATION

| Check | Result |
|---|---|
| `forge` HEAD equals `origin/forge` at start | PASS — `38b322b562317fdd42ad8ea61a9866b2931966a7` |
| Ancestry from IV.1 base `238c4da` | PASS |
| Four IV.2 planning artifacts present and committed | PASS — `PLAN.md`, `ACCEPTANCE.md`, `FEASIBILITY_GATE.md`, `DEPENDENCY_HANDOFF.md` |
| IV.1 ratification | PASS at the starting head |
| IV.1 interpreter suite | 60 passed |
| Book I canonical/retrieval interfaces | Present; consumed without modification |
| `RetrievalService.retrieve`, `.exact`, `.navigate` | Present; composed by IV.2 |
| `RetrievalQuery`, `RetrievalHeader`, `RetrievalObject`, provenance | Present; consumed without modification |
| Book II `guard()` / enforcement semantics | Present; invoked before protected loads |
| III.6 `IntelligenceGateway` typed requests | Present; routed through typed contracts |
| Book III integration suite | 96 passed |
| Amended `PROVIDER_SCHEMAS_V2` | Preserved; no edit |
| Book II hashes and planning pins | Unchanged |
| Book III frozen/versioned baselines | Unchanged |
| Routes and migrations `[1,2,3,4]` | Unchanged |
| Market data provider | `NOT_CONFIGURED`; A-67 passes the governed refusal |
| Starting-head CI | Green on the Rung 1 head |
| `.bu_tmp/` and unrelated files | Preserved; never staged |

Frozen-source diff from `38b322b` across Book I retrieval, Book II policy and
enforcement, III.6 intelligence API, setup engine, canonical corpus, IV.1
interpreter, routes and migrations: **empty**.

Pinned hashes observed at implementation time:

- IV.1 `plan.py` — `c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b`
- Book I `retrieval/service.py` — `0da911be828a0d5747b8cfe022ab20df3cd8187865ecb42232ddb4177339ade0`
- Book II `policy.py` — `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`

---

## 2. IMPLEMENTED MODULE INVENTORY

`app/forge/ask_cerebus/retrieval/` — 16 modules, 1,934 physical lines.

| Module | Responsibility |
|---|---|
| `versions.py` | `RETRIEVAL_CONTRACT_V1`, bundle-id constants, supported versions |
| `enums.py` | Outcomes, limitation/refusal/rejection classes, trace classes |
| `refs.py` | Immutable canonical, claim, evidence, intelligence, lineage, negative, passage, limitation and refusal references |
| `trace.py` | Deterministic internal trace, consumer-safe projection and refusal projection |
| `bundle.py` | Immutable `AuthorizedRetrievalBundle`, canonical JSON and deterministic bundle identity |
| `query_builder.py` | Frozen-plan → typed resolver targets; no plan widening |
| `structured.py` | Safe-header candidate selection, exact resolution, alias expansion, guarded relationship traversal, setup projection |
| `semantic.py` | Replaceable `SemanticIndexPort`, empty port and deterministic fake |
| `precedence.py` | Frozen six-tier precedence comparator |
| `claims.py` | Query → Model → Claim → Evidence → Provenance joins and insufficiency |
| `intelligence.py` | III.6 current/historical/level/setup/instrument/JPY routing and completeness refusal |
| `lineage.py` | Generation-preserving lineage references and unavailable-generation limitations |
| `conflicts.py` | Identity comparison, matched conflict, incomparable separation |
| `negative.py` | Parked, superseded, falsified, no-go and null evidence references |
| `service.py` | Policy-first orchestration, references, traces and final bundle |
| `__init__.py` | Public IV.2 surface |

No canonical object store, policy matrix, embedding provider, vector database,
network client, LLM client or public route was added.

---

## 3. 64/64 REQUIREMENT RECONCILIATION

Every requirement maps to its frozen base driver in `ACCEPTANCE.md`.

| Group | Requirements | Drivers | Result |
|---|---|---|---|
| T1 structured canonical resolution | R1–R7 | A-01–A-07 | 7 passed |
| T2 semantic resolution | R8–R13 | A-08–A-13 | 6 passed |
| T3 canonical priority | R14–R19 | A-14–A-19 | 6 passed |
| T4 claim/evidence joins | R20–R26 | A-20–A-26 | 7 passed |
| T5 Book III intelligence join | R27–R33 | A-27–A-33 | 7 passed |
| T6 generation and lineage | R34–R39 | A-34–A-39 | 6 passed |
| T7 conflict resolution | R40–R45 | A-40–A-45 | 6 passed |
| T8 negative evidence | R46–R50 | A-46–A-50 | 5 passed |
| T9 authorization and exposure | R51–R57 | A-51–A-57 | 7 passed |
| T10 retrieval trace | R58–R64 | A-58–A-64 | 7 passed |
| T11 cross-cutting invariants | R1–R64 | A-65–A-68 | 4 passed |
| T12 frozen-contract integrity | R1–R64 | A-69–A-72 | 4 passed |
| **Total** | **64 unique** | **72** | **72 passed** |

No requirement is unowned. T11/T12 add cross-cutting checks without creating a
second base driver or changing R1–R64.

---

## 4. 72/72 TEST RECONCILIATION

Command:

`python -m pytest tests/test_forge_ask_cerebus_retrieval.py -q -p no:cacheprovider`

Measured result on the final tree: **72 passed in 2.57s**.

- 72 exact executable names A-01–A-72.
- Zero renamed, merged, skipped or xfailed drivers.
- Zero weakened assertions.
- No orphan test and no orphan requirement.
- Tests exercise actual Book I retrieval, Book II enforcement, III.6 request
  contracts and IV.1 plans. Deterministic fakes are confined to the semantic
  boundary and controlled loaders.

---

## 5. EIGHTEEN-FIXTURE REPRODUCTION

Location: `implementation/forge/book_iv/bloc_iv_2/fixtures/`.

- Shared builders: `_builders.py`.
- Generator: `generate.py`.
- Provenance map: `PROVENANCE.md`.
- 18 LF-normalized JSON payloads under `expected/`.
- Manifest: `FIXTURE_MANIFEST.json`, SHA-256
  `df552d4027ab4ec3fc8b332288d9eed7f86b4250099b8e9292abdde3b491219a`.
- A-64 imports the generator, calls `build_all()` and compares every expected
  payload and the manifest **byte-for-byte**.
- Generator output is deterministic; no wall-clock or environment input enters
  a payload or digest.

| Fixture | Outcome | Required limitation(s) |
|---|---|---|
| Q2-01 | RESOLVED | none |
| Q2-02 | RESOLVED | none |
| Q2-03 | RESOLVED | none |
| Q2-04 | PARTIAL | `EVIDENCE_INSUFFICIENT` |
| Q2-05 | PARTIAL | `EVIDENCE_INSUFFICIENT`, `INCOMPARABLE_EVIDENCE` |
| Q2-06 | PARTIAL | `EVIDENCE_INSUFFICIENT`, `HISTORICAL_GENERATION` |
| Q2-07 | PARTIAL | `PROVIDER_NOT_CONFIGURED` |
| Q2-08 | PARTIAL | `NO_GO_ACTIVE`, `NEGATIVE_EVIDENCE` |
| Q2-09 | RESOLVED | XAU WATCH setup context; no eligibility grant |
| Q2-10 | RESOLVED | Fib research-only setup context |
| Q2-11 | RESOLVED | JPY manual setup context |
| Q2-12 | PARTIAL | `EVIDENCE_CONFLICT` only |
| Q2-13 | PARTIAL | `INCOMPARABLE_EVIDENCE`, `EVIDENCE_INSUFFICIENT` |
| Q2-14 | PARTIAL | `HISTORICAL_GENERATION`, `NEGATIVE_EVIDENCE` |
| Q2-15 | PARTIAL | `POLICY_DENIED`, `UNRESOLVED_IDENTITY` |
| Q2-16 | PARTIAL | `POLICY_DENIED` |
| Q2-17 | PARTIAL | `HISTORICAL_UNAVAILABLE` |
| Q2-18 | PARTIAL | `SOURCE_DISAGREEMENT` |

Q2-12 and Q2-13 were separately regenerated during this rung so that the
matched-identity conflict and the different-identity incomparability are
independently demonstrated rather than emitted by one combined model.

No fixture fabricates market history, a statistically verified claim, evidence
verdict, entitlement or current snapshot.

---

## 6. STRUCTURED CANONICAL RESOLUTION

- Candidate selection reads safe `RetrievalHeader` metadata only.
- Exact canonical ids resolve through `RetrievalService.exact` / `retrieve`.
- Model tokens select only their exact canonical namespace; no fuzzy or
  nearest-neighbour identity creation.
- Governed aliases expand exactly and do not promote status, version or
  exposure.
- Relationship hops use `RetrievalService.navigate` under the same policy guard.
- Unknown ids remain `UNRESOLVED_IDENTITY`; no object is synthesized.
- Setup ids project through the frozen setup registry without deriving
  eligibility in IV.2.

Drivers A-01–A-07 pass.

---

## 7. BOOK II DENY-BEFORE-LOAD

Order enforced: candidate header → Book II authorization → permitted body load
→ authorized bundle.

Evidence:

- A-51 proves authorization precedes retrieval composition.
- A-52 uses a recording `record_loader`; a denied direct body request records
  **zero** loads.
- A-53 proves researcher depth does not alter exposure.
- A-54 proves a hidden-id guess yields a uniform refusal with no object id,
  name or existence disclosure.
- A-55 proves a semantic neighbour cannot enter the authorized id set.
- A-56 proves citation traversal is guarded on every hop.
- A-57 proves repeated queries do not accumulate hidden objects.
- A-68 proves policy-engine failure fails closed as `REFUSED`.

No duplicate Book II policy matrix exists.

---

## 8. CLAIM → EVIDENCE → PROVENANCE

The join preserves, where authoritative fields exist:

- claim id;
- model id and generation version;
- metric/result value;
- `ClaimIdentity` dimensions;
- conditioning population, sample size and research period;
- evidence status, support classification and provenance artifact ids;
- supersedes/contradicts references;
- OOS/reproduction absence (`UNAVAILABLE`).

A claim without sufficient evidence yields `EVIDENCE_INSUFFICIENT`; it never
becomes `CANONICAL_VERIFIED`. Absent governed population/sample/period bodies
remain absent rather than inferred (F4/R23). Target-completion rates are not
converted into setup win rates. Drivers A-20–A-26 pass.

---

## 9. BOOK III III.6 GATEWAY BEHAVIOR

Typed routes exercised by A-27–A-33:

- current snapshot;
- levels/coordinates with layer and state;
- setup context with card id, version and parent state;
- historical snapshot with explicit version and cutoff;
- instrument view with quality/source cutoffs;
- JPY basket context where the typed request supports it.

Incomplete fields are refused before request construction. Current data remains
`PROVIDER_NOT_CONFIGURED`; no historical snapshot is substituted for CURRENT.
Historical requests without a provider return `HISTORICAL_UNAVAILABLE`.
No durable snapshot store was created.

Setup states are copied from upstream projections: XAU WATCH, Fib
research-only, JPY manual and active no-go. IV.2 derives no eligibility.

---

## 10. GENERATION AND ALIAS ISOLATION

Preserved without migration or fallback:

- BTC Game vs BTC Tracker;
- P90 / P90P / PHI;
- ST / Atomic and Base80;
- Wednesday/Afternoon, session and clock tags;
- legacy Markov and historical Fib generations;
- XAU Game.

Historical and current references may coexist, but claims remain separate.
Unavailable generations return `UNAVAILABLE_GENERATION`; no newest-model
fallback. Drivers A-34–A-39 and fixtures Q2-05, Q2-06, Q2-14, Q2-17 pass.

---

## 11. CONFLICT AND NEGATIVE EVIDENCE

Identity comparison covers instrument, market, event, conditioning population,
model/version, clock/session, horizon, metric, tolerance and implementation
semantics.

- Same identity + different value → `EVIDENCE_CONFLICT`, both claims/evidence
  retained, conclusion downgraded, no winner.
- Different identity → `INCOMPARABLE_EVIDENCE`, no manufactured contradiction.
- Majority vote and semantic similarity are never truth selectors.
- `supersedes` and `contradicts` metadata remain visible.

Negative evidence retains failed/null, parked, superseded, falsified and no-go
status with original generation and provenance. It is never suppressed and
never becomes a trading recommendation. Drivers A-40–A-50 pass.

---

## 12. SEMANTIC-PORT RESTRICTIONS

- `SemanticIndexPort` is replaceable and receives only policy-authorized ids.
- The deterministic fake is the only implemented index.
- Later candidate re-filtering rejects unauthorized neighbours and counts them.
- Passages are tier-5 support only; they cannot establish identity, version,
  status, numbers, verification, exposure or setup eligibility.
- A canonical value always outranks a semantic passage; disagreement is
  retained as `SOURCE_DISAGREEMENT`.
- A-72 confirms no LLM, embedding provider, vector service or network SDK import
  in the IV.2 package.

No real semantic capability is claimed (F4/R12).

---

## 13. DETERMINISTIC TRACE AND BUNDLE IDENTITY

- `AuthorizedRetrievalBundle` is frozen; reference collections are tuples.
- Canonical JSON uses sorted keys and fixed separators.
- `bundle_id` is SHA-256 over the payload excluding the id; no wall clock,
  random value, process id or mutable collection participates.
- Trace digest is SHA-256 over the canonical internal trace payload.
- Internal, consumer-safe and refusal trace projections are distinct.
- Consumer projections contain only authorized ids and bounded metadata; no
  rejected protected ids, secret text or internal source text.
- Identical plan, policy context and canonical index generation produce an
  identical bundle id (A-64, A-65).

---

## 14. REMAINING F3/F4 DEPENDENCIES

These remain open and are represented by bounded limitations/refusals, not
synthetic success.

| Class | Requirement | Owner | Remaining closure evidence |
|---|---|---|---|
| F3 | R25 OOS/reproduction verdicts | Book IV.5 / Book VII | Governed verdict surface and promotion semantics |
| F3 | R30 durable historical retrieval | Book III / Book VI | Historical store with version, cutoff and retrieval tests |
| F3 | R57 enumeration/abuse governance | Book IV.6 / Book VIII | Rate/abuse controls and repeated-query audit evidence |
| F4 | R12 real semantic index/embeddings | Book VII / platform | Approved adapter, snapshot provenance and leakage tests |
| F4 | R23 governed population/sample/period bodies | Book I corpus / Book VII | Authoritative canonical statistical fields |
| F4 | R53 Book VI entitlement projection | Book VI | Capability projection and isolation tests |

Green IV.2 tests prove deterministic composition and refusal behavior. They do
not prove production vector search, complete statistical authority, commercial
entitlement, historical retention or abuse resistance.

---

## 15. FROZEN INTEGRITY

- Book I canonical corpus: unmodified.
- Book I retrieval implementation: unmodified.
- Book II identity/policy/enforcement: unmodified.
- Book III modules and III.6 gateway: unmodified.
- Book IV.1 interpreter: unmodified.
- Historical fixtures and ratifications: unmodified.
- Routes: unmodified.
- Migrations `[1,2,3,4]`: unmodified.
- Market-data readiness seam: unmodified.
- `.bu_tmp/` and unrelated files: preserved.

No frozen module was edited to force an IV.2 test green.

---

## 16. DEFECT AND REPAIR HISTORY

| Defect found | Repair | Verification |
|---|---|---|
| Model-token matching could select `V1` and `V2` from a shared prefix | Exact namespace/version matching for canonical identities | A-01–A-07; Q2-12/Q2-13 |
| All generation-like tags were treated as historical lineage | Restrict lineage handling to the frozen historical generation set | A-34–A-39 |
| Denied identifiers could leak into limitation `object_id` fields | Consumer-visible denials carry no denied id | A-54; Q2-15 |
| Setup fixture cards lacked `market_scope` | Added authoritative fixture scope fields; no IV.2 eligibility derivation | A-29; Q2-08–Q2-11 |
| Historical route without provider returned current-provider refusal | Return governed `HISTORICAL_UNAVAILABLE` for historical scopes | A-30; Q2-17 |
| Fixture generator's generic `_builders` import collided with another cached test module in the full suite | Load the local builder module by explicit file path under a unique module name | Full regression; A-64 |
| Q2-12 and Q2-13 were byte-identical because one model carried both comparable and incomparable claims | Dedicated matched-conflict and incomparable fixture models | Distinct bundle ids and limitations; A-64 reproduction |

No failing test was skipped, xfailed, renamed or weakened to obtain green
evidence.

---

## 17. FULL REGRESSION

Final tree, measured locally:

| Suite | Result |
|---|---|
| IV.2 retrieval acceptance | 72 passed |
| IV.1 interpreter | 60 passed |
| Book III integration | 96 passed |
| III.1 provider compatibility | 49 passed |
| WP-3B provider integration | 66 passed |
| Full repository | **2210 passed, 29 skipped, 4 warnings in 78.11s** |

The 29 skips are pre-existing environment-gated skips; IV.2 added none. The
four warnings are pre-existing FastAPI `on_event` deprecation warnings. No IV.2
failure remains.

---

## 18. CI STATUS

Local evidence and ratification are committed before the CI receipt, following
the append-only ladder. The pushed-head CI result for `test` and `postgres` is
recorded separately in `CI_RECEIPT.md` after both jobs complete.

This file does not claim a CI result that was not observed.
