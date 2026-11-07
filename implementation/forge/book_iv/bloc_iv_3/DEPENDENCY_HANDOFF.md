# BOOK IV / BLOC IV.3 — DEPENDENCY AND HANDOFF
## CONTEXT PACKAGER — BA-28 RUNG 1

**Base HEAD:** `23b2b9e19f1b1dee59c4aa9379a35a1dfed981b7`
**Contract:** `CONTEXT_CONTRACT_V1` (proposed)
**Status:** Planning complete; implementation not started.

---

## 1. POSITION IN BOOK IV

```
IV.1 interpreter
  -> IV.2 authorized retrieval
  -> IV.3 authorized context package
  -> IV.4 LLM gateway
  -> IV.5 answer compiler/validator
  -> IV.6 evaluation
```

IV.3 is the only boundary permitted to hand context to IV.4. IV.4 must never
receive the raw `AuthorizedRetrievalBundle`, canonical bodies or retrieval
records.

---

## 2. INPUT CONTRACT

### 2.1 Required

- `AskCerebusQueryPlan` from IV.1;
- `AuthorizedRetrievalBundle` from IV.2;
- matching `plan.plan_id == bundle.query_plan_id`;
- explicit `ContextBudget` or the documented default;
- `CONTEXT_CONTRACT_V1`.

### 2.2 Optional and already authorized

`AuthorizedContextDetail`:

- intelligence facts keyed to a snapshot already present in
  `bundle.intelligence_refs`;
- evidence statistics keyed to an evidence id already present in
  `bundle.evidence_refs`.

IV.3 performs no lookup, load, provider call or policy evaluation. A detail id
outside the bundle refuses with `CONTEXT_DETAIL_UNAUTHORIZED`.

### 2.3 Explicitly absent

- raw canonical bodies;
- source code or internal-method prose;
- denied ids or hidden-object existence;
- current provider values when `NOT_CONFIGURED`;
- durable historical store;
- Book VI entitlement projection;
- unrestricted corpus text;
- real tokenizer/billing counts.

---

## 3. OUTPUT CONTRACT

`AuthorizedContextPackage` contains:

- contract version, plan ID, bundle ID and `PKG.` identity;
- frozen section order;
- typed items with source status, epistemic label, layer, exposure, generation,
  trust class, allowlisted facts, optional untrusted text, provenance and token
  units;
- omissions with bounded codes;
- all upstream limitations/refusals that affect meaning;
- token accounting;
- manifest with included/omitted sections, authorized object ids, section
  digests, trust-boundary hash and deterministic digest.

The package contains no answer, recommendation, order intent, eligibility
verdict, entitlement grant, computed market number or canonical status.

---

## 4. DOWNSTREAM OWNERSHIP

| Consumer | Receives | Must not do |
|---|---|---|
| IV.4 LLM gateway | Package only | Re-read bundle/raw corpus; execute untrusted text; add facts |
| IV.5 answer compiler | Package + its control contract | Recompute values, promote labels, drop no-go/refusals, treat `GENERAL_KNOWLEDGE` as CEREBUS truth |
| IV.6 evaluation | Packages, manifests, fixture outputs, refusal codes | Convert a packaging score into canonical status |
| Book V | Package display projection | Widen exposure, remove negative evidence, invent setup authority |
| Book VI | Its own entitlement decision | Expect IV.3 to project or infer entitlement |
| Book VII | Research/index/statistical promotion | Treat IV.3's unresolved states as verified |
| Book VIII | Release evidence | Infer production GO from a green package suite |

### 4.1 IV.4

IV.4 may assemble instructions around the package but must preserve the
control/untrusted split. It cannot convert a source passage into a control
instruction. It cannot use the package's manifest as an authorization grant.

### 4.2 IV.5

IV.5 may explain only facts whose epistemic label and evidence join permit the
statement. It must preserve:

- `EVIDENCE_INSUFFICIENT` / `MISSING_EVIDENCE`;
- `EVIDENCE_CONFLICT` / `INCOMPARABLE_EVIDENCE`;
- `PROVIDER_NOT_CONFIGURED` / `HISTORICAL_UNAVAILABLE`;
- `NO_GO_ACTIVE`, `SETUP_BLOCKED`, `SETUP_NOT_ELIGIBLE`;
- `RESEARCH_ONLY_NOT_PRODUCTION`, `AUTOMATION_NOT_APPROVED`;
- `POLICY_DENIED`, `CONTEXT_BUDGET_EXCEEDED`, `CONTEXT_EXPOSURE_VIOLATION`;
- historical generation and layer separation.

No answer compiler may turn an L3 statistic into an L1 setup result.

### 4.3 IV.6

Evaluation must cover:

- deterministic package/manifest identity;
- the 20 Q3 fixtures;
- mandatory no-go survival under trimming;
- injection payload isolation;
- internal/denied ID exclusion;
- two-principal exposure isolation where an upstream context exists;
- no semantic or historical substitution for missing evidence.

### 4.4 Book VII

Book VII owns:

- real semantic index quality;
- provider tokenizer/billing accuracy;
- governed statistical bodies and N/population/period;
- small-N policy;
- research promotion.

None is closed by IV.3 fixtures.

---

## 5. DETAIL PROJECTION CONTRACT

### 5.1 `AuthorizedIntelligenceFact`

Allowed only when:

1. `snapshot_id` is already authorized in the bundle;
2. the upstream Book III read was policy-guarded;
3. the field path is on the allowlist (`state`, `levels`, `path`, `setup`,
   `quality`, `no_go`, `version`, `cutoff`);
4. no raw provider payload, code or internal method text is attached.

If the snapshot detail is absent, the package carries the snapshot reference,
quality, no-go and refusal only, plus `DETAIL_NOT_SUPPLIED`.

### 5.2 `AuthorizedEvidenceStatistic`

Allowed only when:

1. `evidence_id` is already authorized in the bundle;
2. metric/event/population/period/N come from an authoritative source;
3. `sample_size is None` means “not provided”, never zero;
4. `small_n_flag` is `TRUE`/`FALSE` only with a governed threshold ref;
5. no number is inferred from a query, model, semantic passage or history.

If absent, the package retains claim/evidence identity and marks N/threshold
unresolved.

---

## 6. OPEN DEPENDENCIES AND EFFECTS

| Gap | Class | Effect on IV.3 | Owner | Closure evidence |
|---|---|---|---|---|
| No provider tokenizer | F4/R18 | estimator only; no billing/accuracy claim | Book VII / provider | authorized tokenizer conformance |
| Missing statistical bodies | F4/R41 | N/population may be unresolved | Book I / Book VII | governed evidence detail |
| No small-N policy | F4/R43 | flag remains unresolved | Book I research / Book VII | ratified threshold |
| `market_data: NOT_CONFIGURED` | global | no current values | Operator / WP-3 | live provider + parity |
| No durable history | global | no historical reconstruction | Book II durability / Book VI | durable store + restore drill |
| No Book VI entitlement projection | global | package cannot commercialize | Book VI | capability projection |
| `III.5-DEFECT-1` | global | strict card operations refuse | Book I governance | schema ADR/repair |
| Real semantic index absent | global | support stays bounded/untrusted | Book VII | approved index + leakage tests |

No gap is silently converted into a positive result.

---

## 7. FROZEN BASELINE

| File | SHA-256 |
|---|---|
| `app/forge/ask_cerebus/interpreter/plan.py` | `c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b` |
| `app/forge/ask_cerebus/retrieval/bundle.py` | `b38b356e01b349fe0110ce7ebd518fd1b3e9d1c82a7f8b979ac088019acc3455` |
| `app/forge/ask_cerebus/retrieval/refs.py` | `bbe1b937d6aa0bd7d0c26c8e0f7f5ba7dfa2ecee7f816dc9461b620d0961daa2` |
| `app/forge/ask_cerebus/retrieval/trace.py` | `6f8f08009da67975017de9c86263a52d0a72753afacf58f74aff7a91ec92e44d` |
| `app/forge/ask_cerebus/retrieval/service.py` | `d4ef64f9d3f994b08c331b48a2e720aa345f92af02d8b32a2d0feb9707d5fd83` |
| `app/forge/ask_cerebus/retrieval/enums.py` | `7c4604af7f8fc9eb3c9461d4ec938f85b99daa10b46c35422c4909f764e0279e` |
| `app/forge/ask_cerebus/retrieval/versions.py` | `b49f9c51439e6da1e8b46138660dbda6bc61c1103946f51ada93424237693132` |
| `app/forge/retrieval/service.py` | `0da911be828a0d5747b8cfe022ab20df3cd8187865ecb42232ddb4177339ade0` |
| `app/forge/retrieval/query.py` | `7bf0d614c2467b2d69700a6531fbc22bd6e713c2609ec498838cf62d9c2ce60d` |
| `app/forge/retrieval/objects.py` | `1114e4712175be974594094b05a8fdee6938c8b07ce533283cedac8e9b28403f` |
| `app/forge/policy.py` | `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc` |
| `app/forge/service/policy_enforcement.py` | `9ccc3b72f77fca0cb3fd0685128fd96a2f0ce8ca975b532d96646d285476e381` |
| `app/forge/intelligence_api/requests.py` | `b2e484023dc55d1fafd90136a6654f07ba713ddfd8ca7d8da2b0ca4499237146` |
| `app/forge/intelligence_api/contracts.py` | `7d8f90adf8aeca993b94d473f61fe16ea13170a1cd977cb47fb186d64697d4f0` |
| `app/forge/intelligence_api/policy_gate.py` | `d805aa915383417eed0ef08581b2400f978a928f0d875460afb5559ad75c9ba9` |
| `app/forge/setup_engine/registry.py` | `1b900b6b93b9df6ca6d5c1173ac8c07b1b7e3d7b7404b40eed2443df10999807` |
| `app/forge/service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

No source, route, migration or provider file is modified by IV.3 planning.

---

## 8. FAILURE PROPAGATION

| Upstream state | Package behavior |
|---|---|
| `PROVIDER_NOT_CONFIGURED` | Current section contains no values; limitation retained |
| `HISTORICAL_UNAVAILABLE` | No substitution; limitation retained |
| `EVIDENCE_INSUFFICIENT` | `MISSING_EVIDENCE`; number omitted |
| `EVIDENCE_CONFLICT` | Both refs/statuses; no winner |
| `INCOMPARABLE_EVIDENCE` | Separate identities; no manufactured conflict |
| `POLICY_DENIED` | Safe code only; no IDs/payload |
| `NO_GO_ACTIVE` | Mandatory limitation; cannot be trimmed |
| `RESEARCH_ONLY_NOT_PRODUCTION` | Setup remains research; no production grant |
| `AUTOMATION_NOT_APPROVED` | Manual state retained; no execution permission |
| `UNRESOLVED_IDENTITY` | No invented object; limitation retained |
| `DETAIL_NOT_SUPPLIED` | Ref preserved; no value synthesized |

---

## 9. IMPLEMENTATION PLAN FOR RUNG 2

1. Freeze `CONTEXT_CONTRACT_V1` and the 92 named tests.
2. Implement schema/enums first, then selector/compression/budget/labels/trust,
   then manifest/service.
3. Build 20 fixtures and a deterministic generator.
4. Prove canonical-first selection, mandatory no-go survival, injection
   isolation, exposure exclusion and deterministic identities.
5. Run focused 92, 20-fixture reproduction, IV.1 60, IV.2 72, Book III 96,
   provider suites and full repository.
6. Commit fixtures, implementation, tests, repairs, evidence/ratification and
   CI receipt append-only.
7. Do not implement IV.4, an LLM, a tokenizer provider, a vector store, routes,
   persistence or migrations.

---

## 10. READINESS VERDICT

**READY — IV.3 Rung 2 may implement the deterministic `CONTEXT_CONTRACT_V1`.**

**Not ready for:**

- live current context;
- provider-accurate token accounting;
- complete statistical bodies;
- commercial entitlement;
- durable historical context;
- production LLM use;
- Book IV closure.

**Stop condition:** planning only. No IV.3 source, test or fixture is authorized
by this rung.
