# BOOK IV / BLOC IV.2 — DEPENDENCY AND HANDOFF
## BA-27 RUNG 1 — PLANNING

**Base HEAD:** `238c4da970f6d213053d6cae0c679d1dda404912`
**Contract:** `RETRIEVAL_CONTRACT_V1` (proposed)

---

## 1. POSITION IN BOOK IV

```
IV.1 interpreter  →  IV.2 retrieval  →  IV.3 context packager
                                      →  IV.4 LLM gateway
                                      →  IV.5 answer compiler/validator
                                      →  IV.6 evaluation
```

IV.2 is a reference-producing boundary, not an answer boundary. It hands
downstream components **references, bounded authorized excerpts, status,
limitations and refusals** — never a free-form conclusion, eligibility verdict,
entitlement grant, order intent or current market claim.

---

## 2. UPSTREAM CONTRACTS CONSUMED

| Upstream | Contract | IV.2 obligation |
|---|---|---|
| IV.1 | `AskCerebusQueryPlan` v1 | Preserve intent, ids, scope, depth, evidence flags and every ambiguity |
| Book I | `RetrievalService`, `RetrievalQuery`, `RetrievalHeader`, `RetrievalObject`, `ProvenanceChain` | Read-only use; no index build or canonical write |
| Book II | `ForgePrincipal`, `AuthorizationContext`, `PolicyResourceMetadata`, `guard()` | Sole authorization authority; no second matrix |
| Book III | `SnapshotRequest`/views, `IntelligenceGateway`, `SnapshotKey` | Typed requests only; no invented version, cutoff, clock or hash |
| III.5 | `SetupRegistry`, `CanonicalSetupCard` | Verbatim setup id/version/status; surface refusals preserved |
| Book IV.1 | Plan outcome and ambiguities | Never remove or downgrade an ambiguity |

---

## 3. DOWNSTREAM HANDOFF

### 3.1 IV.3 — Context packager

Receives `AuthorizedRetrievalBundle` only after policy release containing:

- `canonical_refs` with id, type, version, status, layer, market, exposure and
  support classification.
- `claim_refs` and `evidence_refs` with identity dimensions, evidence status
  and provenance references.
- `intelligence_refs` with snapshot id/hash, view, quality outcome and no-go
  state, or the governed refusal.
- `lineage_refs` preserving generation.
- `semantic_passages` with object id, bounded excerpt, quote scope and support
  classification.
- `negative_refs` with original status and generation.
- `limitations`, `refusals`, `trace` and `selected_generation`.

IV.3 must not re-rank a canonical fact below a semantic passage, expand
entitlement, synthesize a missing number or turn a negative research reference
into a signal.

### 3.2 IV.4 — LLM gateway

**May not receive raw retrieval results.** IV.4 receives only IV.3's minimized
context pack. IV.2 therefore does not expose internal-method text, code,
unbounded bodies, denied ids or hidden-object existence to any prompt path.

### 3.3 IV.5 — Answer compiler/validator

Consumes authoritative claim/evidence and snapshot references. A numerical
statement is admissible only when the bundle carries an authoritative evidence
join and a support classification that permits it. `EVIDENCE_CONFLICT`,
`EVIDENCE_INSUFFICIENT`, `PROVIDER_NOT_CONFIGURED`, `HISTORICAL_UNAVAILABLE`
and `INCOMPARABLE_EVIDENCE` are constraints on the answer, not suggestions.

### 3.4 IV.6 — Evaluation

Uses retrieval traces, the 18 golden fixtures, refusal evidence and rejection
reason classes. Evaluation must test isolation two-account style, hidden-object
enumeration, historical substitution and provider-unavailable behavior. A
retrieval score cannot promote canonical status.

### 3.5 Book VII — Research and retrieval promotion

Owns later real semantic indexing, research promotion, evidence-body expansion
and retrieval build promotion. IV.2 may not treat a Book VII promotion as
already granted.

---

## 4. HANDOFF SCHEMA

Minimum handoff fields, frozen for Rung 2:

| Field | Type | Rule |
|---|---|---|
| `query_plan_id` | string | Exact IV.1 id; no recomputation |
| `retrieval_contract_version` | enum | `RETRIEVAL_CONTRACT_V1` |
| `bundle_id` | string | Deterministic digest of authorized payload |
| `canonical_refs` | ordered tuple | Tier, then id, then generation |
| `claim_refs` | ordered tuple | No claim without identity dimensions |
| `evidence_refs` | ordered tuple | Status and provenance preserved |
| `intelligence_refs` | ordered tuple | Snapshot identity or bounded refusal |
| `lineage_refs` | ordered tuple | Generation preserved; no merge |
| `semantic_passages` | ordered tuple | Authorized ids only; bounded quote scope |
| `negative_refs` | ordered tuple | Original status and generation |
| `limitations` | bounded codes | Include IV.1 ambiguities unchanged |
| `refusals` | bounded codes | Governed codes only |
| `trace` | internal + consumer | No protected text in consumer view |
| `selected_generation` | object | Index generation + source fingerprint |

No probability, confidence percentage, win rate, target completion rate,
expectancy, eligibility verdict, position size or order intent is permitted in
the schema.

---

## 5. OWNERSHIP BOUNDARIES

| Decision | Owner | IV.2 role |
|---|---|---|
| What was asked | IV.1 interpreter | Consume only |
| What is canonically true | Book I | Read only |
| Who may see it | Book II | Request decision; never decide |
| What the market state is | Book III | Route; never synthesize |
| How context is minimized | IV.3 | Supply refs and constraints |
| What the answer says | IV.5 | Supply evidence constraints |
| What is promoted | Book VII | Never self-promote |
| What is evaluated | IV.6 | Supply trace and fixtures |

No component may use IV.2 to overwrite Book I truth. A retrieval record is a
finding surface, not a competing canonical source.

---

## 6. FAILURE AND REFUSAL PROPAGATION

| Condition | IV.2 result | Downstream effect |
|---|---|---|
| No canonical match | `UNRESOLVED_IDENTITY` | No invented object |
| Evidence absent | `EVIDENCE_INSUFFICIENT` | No number |
| Evidence conflict | `EVIDENCE_CONFLICT` | Both refs, downgraded conclusion |
| Different identities | `INCOMPARABLE_EVIDENCE` | No manufactured contradiction |
| Provider absent | `PROVIDER_NOT_CONFIGURED` | No current market claim |
| Historical unavailable | `HISTORICAL_UNAVAILABLE` | No current substitution |
| Required fields absent | `REQUIRED_FIELDS_UNRESOLVED` | No III.6 request |
| Policy denied | `EXPOSURE_FORBIDDEN` | No payload or existence leak |
| Index absent/stale | `RETRIEVAL_UNAVAILABLE` | Fail closed, no partial bundle |
| Plan unsupported | `UNSUPPORTED_PLAN_CONTRACT` | No retrieval |

Refusals are data, not exceptions thrown across the boundary. Each carries a
bounded code and only the minimum safe context.

---

## 7. STOP CONDITIONS FOR RUNG 2

Stop implementation and report rather than inventing if:

1. A canonical id has no index record.
2. A required snapshot field has no governed source.
3. A provider is `NOT_CONFIGURED`.
4. Evidence body/status is missing for a requested number.
5. A historical generation is unavailable.
6. Policy returns deny or the engine fails.
7. A dependency would require an embedding service, LLM, network call,
   migration or provider connection.
8. A protected upstream module would need modification.

---

## 8. FROZEN BASELINE HASHES

EOL-normalized SHA-256 of the contracts read at this head:

| File | SHA-256 |
|---|---|
| `app/forge/ask_cerebus/interpreter/plan.py` | `c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b` |
| `app/forge/retrieval/service.py` | `0da911be828a0d5747b8cfe022ab20df3cd8187865ecb42232ddb4177339ade0` |
| `app/forge/retrieval/query.py` | `7bf0d614c2467b2d69700a6531fbc22bd6e713c2609ec498838cf62d9c2ce60d` |
| `app/forge/retrieval/objects.py` | `1114e4712175be974594094b05a8fdee6938c8b07ce533283cedac8e9b28403f` |
| `app/forge/policy.py` | `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc` |
| `app/forge/service/policy_enforcement.py` | `9ccc3b72f77fca0cb3fd0685128fd96a2f0ce8ca975b532d96646d285476e381` |
| `app/forge/intelligence_api/requests.py` | `b2e484023dc55d1fafd90136a6654f07ba713ddfd8ca7d8da2b0ca4499237146` |
| `app/forge/intelligence_api/policy_gate.py` | `d805aa915383417eed0ef08581b2400f978a928f0d875460afb5559ad75c9ba9` |
| `app/forge/setup_engine/registry.py` | `1b900b6b93b9df6ca6d5c1173ac8c07b1b7e3d7b7404b40eed2443df10999807` |

Rung 2 must pin these hashes in tests and fail if any protected contract drifts
without a new planning ratification.

---

## 9. COMMIT AND VERIFICATION HANDOFF

Rung 1 delivers exactly:

```
implementation/forge/book_iv/bloc_iv_2/PLAN.md
implementation/forge/book_iv/bloc_iv_2/ACCEPTANCE.md
implementation/forge/book_iv/bloc_iv_2/FEASIBILITY_GATE.md
implementation/forge/book_iv/bloc_iv_2/DEPENDENCY_HANDOFF.md
```

No source, test, migration, route or provider file is part of this commit.
Fast-forward push to `forge`; no amend, squash, rebase, reset or force-push.
CI must be green in both `test` and `postgres` at the pushed head.

**Rung 2 entry verdict:** ready to implement the deterministic contract; not
ready to claim production hybrid retrieval, live current intelligence or
commercial entitlement enforcement.
