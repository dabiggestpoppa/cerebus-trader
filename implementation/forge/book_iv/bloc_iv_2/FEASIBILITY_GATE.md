# BOOK IV / BLOC IV.2 — FEASIBILITY GATE
## HYBRID RETRIEVAL & EVIDENCE ROUTING — BA-27 RUNG 1

**Base HEAD:** `238c4da970f6d213053d6cae0c679d1dda404912`

Classification is per requirement, not per aspiration. A green deterministic
test can satisfy an IV.2 contract while the capability behind it remains open.

| Class | Meaning | Count |
|---|---|---|
| **F1** | Directly supported by existing Book I/II/III contracts | 19 |
| **F2** | Implementable through new deterministic IV.2 logic | 39 |
| **F3** | Requires a later Book IV/VI/VII implementation | 3 |
| **F4** | Missing canonical authority, real source data or governed infrastructure | 3 |
| **Total** | | **64** |

---

## 1. PER-REQUIREMENT CLASSIFICATION

### F1 — directly supported (19)

| ID | Requirement | Existing authority |
|---|---|---|
| R1 | Exact canonical id | Book I `RetrievalService.exact` / index |
| R2 | Safe-header selection | `RetrievalHeader`, `filter_headers` |
| R3 | Exact version/generation | `RetrievalObject.canonical_version`, index generation |
| R5 | Typed relationship traversal | `related_ids`, `navigate()` |
| R21 | Claim identity | `ClaimIdentity`, `StructuredFields.claim_identity` |
| R22 | Model/generation version | `canonical_version`, `conflict.generation` |
| R24 | Evidence status/provenance | `EvidenceStatus`, `ProvenanceLink` |
| R27 | Current routing | `SnapshotRequest`, `IntelligenceGateway` |
| R28 | Level routing | `Layer`, level-aware III.6 views |
| R29 | Setup context | `SetupRegistry`, `CanonicalSetupCard` |
| R31 | Instrument view | III.6 instrument view contracts |
| R32 | JPY basket context | III.6 basket view contract |
| R40 | Identity comparison | `ClaimIdentity`, `compare_claim_identity` |
| R44 | Supersedes/contradicts | `ConflictMetadata` |
| R46 | Failed/null findings | Status-bearing retrieval records |
| R47 | Parked/superseded/no-go | `EvidenceStatus`, setup card statuses |
| R49 | Negative status/generation | Retrieval record status + generation |
| R51 | Pre-retrieval authorization | Book II policy + enforcement service |
| R52 | Deny-before-load | `ForgePolicyEnforcementService.guard` |

### F2 — deterministic IV.2 logic (39)

| ID | Requirement | New deterministic logic |
|---|---|---|
| R4 | Alias expansion | Canonical alias table → exact query terms; no promotion |
| R6 | Unresolved outcome | Bounded `UNRESOLVED_IDENTITY` result |
| R7 | No fuzzy invention | Exact-only resolver; no nearest neighbour |
| R8 | Semantic port | `SemanticIndexPort` protocol |
| R9 | Authorized corpus | Port receives only policy-allowed headers/ids |
| R10 | No semantic authority | Field-level prohibition on identity/numbers/status |
| R11 | Deterministic fake | Fixture-backed deterministic candidate list |
| R13 | Support-only passage | Precedence tier + support classification |
| R14 | Six-tier order | `PrecedenceTier` comparator |
| R15 | Structured outranks | Tier ordering across all candidates |
| R16 | No overwrite | Canonical fact wins; passage retained as disagreement |
| R17 | Visible disagreement | `SOURCE_DISAGREEMENT` limitation |
| R18 | Score not authority | Score confined to tier-5 tie-break |
| R19 | No promotion | Status copied, never recomputed |
| R20 | Claim/evidence path | Orchestrated `navigate()` join |
| R26 | Missing evidence | `EVIDENCE_INSUFFICIENT`, no number |
| R33 | Unresolved fields | Completeness check before III.6 request |
| R34 | P90/PHI | Generation-tagged refs retained |
| R35 | ST/Base80 | Manual/automation separation retained |
| R36 | Session/clock/Markov/Fib | Scope tags retained, no migration |
| R37 | BTC separation | Distinct canonical ids |
| R38 | No lineage merge | Separate refs and claims |
| R39 | No newest fallback | `UNAVAILABLE_GENERATION` preserved |
| R41 | Matched conflict | Both claims, downgraded conclusion |
| R42 | Incomparable separation | Identity comparator |
| R43 | No majority/similarity winner | Prohibited winner rule |
| R45 | Conflicts visible | Both evidence statuses retained |
| R48 | No positive bias | Uniform candidate policy and fixture coverage |
| R50 | Negative ≠ signal | Negative refs carry no actionability |
| R54 | ID guess no leak | Uniform refusal, no existence metadata |
| R55 | Semantic neighbour policy | Authorized id set only |
| R56 | Citation traversal policy | Same guard on every hop |
| R58 | Trace plan/contract | Trace binds plan id + contract version |
| R59 | Authorized refs only | Trace built after policy release |
| R60 | Rejection counts | `RejectionClass` counters |
| R61 | Three trace classes | Internal / consumer / refusal schemas |
| R62 | No forbidden content | Trace field allowlist |
| R63 | Exposure-safe projection | Consumer trace projection |
| R64 | Digest/min retention | Canonical digest, bounded fields |

### F3 — later implementation (3)

| ID | Requirement | Why later | Owner | Closure evidence |
|---|---|---|---|---|
| R25 | OOS/reproduction status | Evidence cards do not yet carry a complete, governed OOS/reproduction verdict surface for all claims | Book IV.5 / Book VII | Ratified evidence field and promotion semantics; displayed without inference |
| R30 | Historical snapshot routing | Typed requests exist, but durable historical snapshot retention/retrieval is not a closed III.6 capability at this head | Book III / Book VI | Historical store with explicit model version, cutoff and snapshot id; retrieval test |
| R57 | Enumeration resistance | Per-request policy filtering exists; abuse-rate and enumeration governance belong to evaluation/operations | Book IV.6 / Book VIII | Rate/abuse controls plus repeated-query audit evidence |

### F4 — missing authority or infrastructure (3)

| ID | Requirement | Missing condition | Owner | Closure evidence |
|---|---|---|---|---|
| R12 | Real semantic index | No authorized embedding provider, vector service, index provenance or leakage review | Book VII / platform | Approved adapter, deterministic index snapshot, privacy/leakage tests |
| R23 | Population/sample/period/event | Facets are optional and several canonical claim bodies do not populate all governed fields | Book I corpus / Book VII | Canonical records with authoritative metric, population, sample, period and event fields |
| R53 | Depth ≠ entitlement | Depth is a planner signal; commercial exposure requires Book VI capability projection that is absent | Book VI | Entitlement resolution mapped to Book II capability atoms, with isolation tests |

---

## 2. BLOCKED CONDITIONS AND NON-CLOSURE

| Gate | Blocked requirement(s) | What remains open | Not implied by green tests |
|---|---|---|---|
| G1 | R12 | Production semantic retrieval quality, index freshness, embedding cost | That semantic search is production-ready |
| G2 | R23 | Complete statistical bodies for every claim | That every numerical question can be answered |
| G3 | R25 | OOS/reproduction verdicts | That a research claim is reproduced |
| G4 | R30 | Historical snapshot availability | That history is substitutable for current |
| G5 | R53 | Commercial entitlement enforcement | That researcher depth equals paid access |
| G6 | R57 | Abuse/enumeration governance | That repeated queries are safe at scale |

No F3/F4 item may be silently satisfied by a fixture, fake provider or
placeholder. The contract outcome is a bounded refusal or limitation.

---

## 3. RUNG 2 ENTRY CRITERIA

Implementation may begin only when:

1. This gate, `PLAN.md`, `ACCEPTANCE.md` and `DEPENDENCY_HANDOFF.md` are
   committed and pushed.
2. Starting HEAD remains an ancestor of `forge` (fast-forward only).
3. IV.1 remains frozen at 60/60 and 12 fixtures.
4. No F3/F4 capability is claimed as delivered.
5. The 72 exact test names and 64 requirements remain unchanged; any change is
   a new planning ratification, not a silent edit.

---

## 4. EXIT CRITERIA

Rung 2 evidence must report separately:

- F1/F2 requirements implemented and tested.
- F3/F4 requirements that return bounded refusals.
- Any fixture blocked by absent authority.
- Regression results for Book I/II/III and IV.1.
- CI result at the pushed head.

**Verdict:** plan is feasible for the deterministic IV.2 contract. Production
hybrid retrieval is **not** claimed feasible at this head; three capabilities
require later authority and three require later implementation.
