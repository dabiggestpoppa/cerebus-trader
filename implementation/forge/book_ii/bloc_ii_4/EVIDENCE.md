# Book II / Bloc II.4 — Policy & Access Control — EVIDENCE

> Recorded: 2026-10-07
> Status: implementation complete, full gate green, awaiting ratification + push

## 1. Starting HEAD

- Authoritative starting remote HEAD: `cad9cd7cfffc72e78a0f30b8accd01e39bf6cd9a`
  (II.3 final ratification head; verified local == remote == `cad9cd7`, tree clean)
- Planning freeze head `60e067547b9d9165d94e4f074e0db0ba58e59e24` verified ancestor of `cad9cd7` in Phase 0.
- Baseline (Phase 0): **283 passed, 14 skipped** (`python -m pytest -q`). Skips are the
  PG integration module only (`tests/test_forge_postgres_integration.py`, requires
  `FORGE_TEST_DATABASE_URL`; runs in CI).

## 2. Implementation / test HEAD

- Final local HEAD at evidence time: see commit ladder (§16). After ratification and
  push, remote HEAD == final local HEAD (verified via `git ls-remote`).

## 3. Freeze ancestry

`60e0675` (freeze) → `aca9438` (I.1) → `5ce3246` (I.2) → `598b34c` (II.1) →
`772a0d2` (II.2) → `cad9cd7` (II.3) → II.4 ladder (§16). All append-only
(no amend/squash/rebase/reset/force used).

## 4. Dependency ratifications consumed

| Dependency | Status | Head |
|---|---|---|
| I.1 Canonical Registry Kernel | PASS | `aca9438` |
| I.2 Source & Provenance Fabric | PASS | `5ce3246` |
| II.1 Service Skeleton | PASS | `598b34c` |
| II.2 Persistence | PASS | `772a0d2` |
| II.3 Identity & Session | PASS | `cad9cd7` |

## 5. Policy architecture

- Pure kernel: `app/forge/policy.py` — no FastAPI, no SQL, no network, no
  protected-body dependency, no mutable global state (proven by source-scan,
  socket-trap, and module-state tests).
- Enforcement service: `app/forge/service/policy_enforcement.py` —
  `ForgePolicyEnforcementService.authorize()` and `.guard(principal, context,
  action, resource, loader, *args, **kwargs) -> GuardedAccess`.
  DENY ⇒ loader never invoked; ALLOW ⇒ loader invoked exactly once.
- Container seam: `ForgeServiceContainer.policy: PolicyEngine | None`;
  `TypeError("policy must implement the PolicyEngine port")` on bad injection;
  `redacted_diagnostics()['policy_wired']` preserved. No production code assigns
  `policy` yet — wiring belongs to later surface blocs.
- One central policy authority (the engine's frozen matrix). No scattered
  `if exposure == ...` checks exist anywhere else.

## 6. Action model

`PolicyAction`: `VIEW | QUERY | OPERATE | ADMINISTER`. Unknown action string ⇒
`DENY / UNKNOWN_ACTION`. In V1 the read matrix grants VIEW/QUERY only;
OPERATE/ADMINISTER fail closed (`ENTITLEMENT_MISSING`) for every capability.

## 7. Resource metadata model

`ResourcePolicyMetadata(resource_type, resource_id, exposure)` — safe, content-free
metadata. `resource_type` bounded by `PolicyResourceType` (CANONICAL_OBJECT,
ARTIFACT, CAPABILITY, SERVICE_ENDPOINT); `resource_id` opaque non-empty string;
`exposure` a `ProductExposure` or `None`. Authorizing never requires the protected
body; malformed metadata raises `ValueError` (fail closed).

## 8. Authorization-context seam

`AuthorizationContext` — immutable `frozenset[str]` of exact-match capability atoms;
constructed only from trusted service input via `.of()` / `.empty()`. `.has()` is
exact-match only (no wildcard/substring/prefix). Non-frozenset construction raises
`ValueError`; malformed context at `decide()` ⇒ `MALFORMED_CONTEXT` DENY.
Registered atoms: `corpus.read.public`, `corpus.read.member`,
`model.read.operator`, `evidence.read.research`, `admin.research`,
`admin.commerce`, `forge.internal`. No FREE/PRO/PREMIUM atoms. No price, billing,
plan, provider ID, or raw-request authority anywhere in the seam. Book VI later
produces this object from commercial state; II.4 defines only the consumption
contract.

## 9. Exposure matrix (central authority)

| Exposure | Anonymous | Auth, no capability | member cap | operator cap | research cap | internal cap |
|---|---|---|---|---|---|---|
| PUBLIC_TEACHING | ALLOW (VIEW/QUERY) | ALLOW (VIEW/QUERY) | ALLOW | ALLOW | ALLOW | ALLOW |
| SUBSCRIBER_MODEL | DENY | DENY | ALLOW | ALLOW | ALLOW | ALLOW |
| OPERATOR_ONLY | DENY | DENY | DENY | ALLOW | ALLOW | ALLOW |
| RESEARCH_LAB | DENY | DENY | DENY | ALLOW | ALLOW | ALLOW |
| INTERNAL_METHOD | DENY | DENY | DENY | DENY | DENY | ALLOW |
| INTERNAL_CODE | DENY | DENY | DENY | DENY | DENY | ALLOW |
| unknown/None | DENY | DENY | DENY | DENY | DENY | DENY |

Admin atoms (`admin.research`, `admin.commerce`) have empty matrix rows (total
lookup, fail closed) — they grant no read access at II.4. `forge.internal` is the
single fail-closed atom admitting internal classes; no staff-role mechanism was
invented. Any combination of ordinary capabilities still denies internal classes
(tested adversarially). Role values from II.3 `IdentityRole` are never consulted.

## 10. Anonymous behavior

Explicitly enumerated: anonymous + VIEW/QUERY + PUBLIC_TEACHING = ALLOW. Every
other anonymous combination = DENY (`NOT_AUTHENTICATED`). AUDIT principal_id is
the literal `"anonymous"`; the anonymous principal is structurally preserved
(the kernel never mutates or upgrades principals).

## 11. Authenticated behavior

- Authenticated, no capability: PUBLIC_TEACHING VIEW/QUERY only; all protected
  classes DENY (`ENTITLEMENT_MISSING`).
- Capabilities are cumulative read-down per the matrix; subscriber capability
  does NOT grant OPERATOR_ONLY; operator/research do NOT grant internal classes.
- RESEARCH_LAB authorization never mutates EvidenceStatus / claim status /
  canonical status (explicit tests: decision and canonical object unchanged).

## 12. Internal exposure behavior

INTERNAL_METHOD / INTERNAL_CODE: DENY for anonymous, authenticated-no-cap,
member, operator, research, all-ordinary-combination, and admin contexts. ALLOW
only for a context carrying `forge.internal` (reserved for explicitly-configured
trusted internal service principals). Fail closed per the Internal Exposure Law.

## 13. Pre-loader enforcement proof

- Deny-before-load: `guard()` calls `authorize()` first; `SpyLoader` records zero
  calls on every DENY (dedicated tests + the adversarial barrage).
- Adversarial extraction test: 1 no-capability principal × 6 resource ids (incl.
  `../etc/passwd`, `MOD.A?ver=2`) × 4 resource types × 7 exposures (6 + None) ×
  6 action spellings (incl. `READ`, `list`, `view `, `VIEW;`) — loader calls
  correspond exactly to legitimate PUBLIC_TEACHING allows; every other attempt
  returned `payload is None` without loading. 100+ attempts, no leak.
- Allowed requests invoke the loader exactly once with the caller's args.

## 14. HTTP integration

No new routes; no route changes. `GET /forge/v1/health`, `/ready`, `/meta`
remain public infrastructure endpoints per II.1/II.2 contracts (tested: no new
route registered, health/ready/meta responses unchanged, no corpus CRUD route).
No authentication/policy dependency was added to health checks.

## 15. Persistence / migrations

- **No migration added.** `discover_migrations()` versions remain `[1, 2]`;
  identities unchanged (`001_initial_schema`,
  `002_identity_session`; 001 SHA-256 pinned
  `d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14` — verified
  unchanged by test). No policy tables in either schema (tested).
- Policy evaluation is stateless; audit records are in-memory, bounded
  (oldest-dropped beyond capacity), content-free (correlation_id, principal_id,
  authenticated, action, resource_type/id, exposure, allowed, reason_code, at).
  No session token, protected body, internal code, or provider secret can appear
  (tested). Persistent audit sinks defer to the owning architecture (clause U).

## 16. Exact tests

Focused II.4 suite: `tests/test_forge_policy.py` — **86 tests** (exposure matrix
table-driven incl. internal/adversarial rows; provider/role/header/JSON atom
authority; wildcard/substring; malformed/missing context; deny-before-load;
adversarial extraction; pre-LLM seam; II.3 authentication integration incl.
invalid/expired/revoked-token and disabled-user never reaching the loader;
audit shape/hygiene/bounding/correlation; determinism; purity source-scan +
socket-trap + mutable-global scan; no-new-migration + schema pins; no-policy-tables;
route/health/ready/meta guards; no-commercial-vocabulary; no-Whop; container seam).

Regression (Phase 10, exact):

| Suite | Result |
|---|---|
| I.1 `test_forge_canonical.py` + `test_forge_schemas.py` | 41 passed |
| I.2 `test_forge_provenance.py` | 41 passed |
| II.1 `test_forge_service_composition.py` | 36 passed |
| II.2 `test_forge_persistence.py` | 51 passed |
| II.3 `test_forge_identity.py` | 66 passed |
| II.4 `test_forge_policy.py` | 86 passed |
| Signal Guard (6 files) | 48 passed |
| **Full repository** `python -m pytest -q` | **369 passed, 14 skipped** |

(369 = 283 baseline + 86 new. 14 skips = PG integration module only.)

## 17. Security review (Phase 9 findings)

Checked: default-allow (none — every path terminates in DENY), wildcard
capability (none — exact-match only, tested), substring permission matching
(none — tested), user-supplied capability trust (none — context constructed
only from trusted service input; no production call sites yet), provider-ID
authority (none), role/plan conflation (none — roles never consulted),
auth/policy conflation (clean — policy consumes principal, never tokens),
protected fetch before policy (none — kernel has no loader/persistence/HTTP
imports; guard orders deny-before-load), policy after LLM/retrieval (N/A — no
LLM; seam established), INTERNAL_METHOD/CODE leakage (none — adversarially
tested), error-based resource enumeration (denial is structured, uniform
content-free reasons), tokens in audit logs (none — tested), protected content
in decision/audit logs (none — tested), mutable global policy state (none —
stateless engine + scan), bypass route (none — routes unchanged), duplicate
policy engines (none — one `DefaultDenyPolicyEngine`).

## 18. Defects discovered and repaired (append-only)

1. `d768d87` — kernel repair: `decide()` did not honor its own frozen matrix
   rows for authenticated-no-capability on PUBLIC_TEACHING (denied instead of
   ALLOW); OPERATE/ADMINISTER were not distinguished from reads (a read
   capability could implicitly grant ADMINISTER); `_CAPABILITY_EXPOSURES`
   lookup was not total (KeyError on admin atoms instead of fail-closed DENY).
   All three repaired in one fail-closed direction consistent with PLAN.md.
2. `7b9e2df` — regression repair: the II.2-era container guard test still
   asserted the `RuntimeError("II.4 owns that boundary")` contract; updated to
   accept a valid `PolicyEngine`, still reject arbitrary injection (mirrors the
   II.1 guard-test update committed in `884fd96`). No test weakened — the new
   assertion is strictly stronger (TypeError on non-engine, engine accepted,
   II.5 provider guard retained).

## 19. Changed files

- `app/forge/policy.py` (new; repaired in d768d87)
- `app/forge/service/policy_enforcement.py` (new)
- `app/forge/service/container.py` (policy seam typed `PolicyEngine | None`)
- `tests/test_forge_policy.py` (new, 86 tests)
- `tests/test_forge_service_composition.py` (II.1 guard test superseded)
- `tests/test_forge_persistence.py` (II.2 guard test superseded)
- `implementation/forge/book_ii/bloc_ii_4/{PLAN,ACCEPTANCE,EVIDENCE,RATIFICATION}.md`

## 20. Known gaps

- No production surface consumes `guard()` yet (I.3 corpus surfaces, III, IV, V,
  VII will). The boundary primitive and its proofs exist and are mandatory.
- `PolicyReason.ROLE_MISSING` is defined but unwired (role semantics reserved;
  role==plan conflation forbidden).
- Commercial entitlement production (populating `AuthorizationContext`) is Book VI.
- Persistent audit storage is deferred (clause U).
- No rate limiting (Book VIII).

## 21. I.3 handoff assumptions

- I.3 corpus surfaces MUST route canonical-object reads through
  `ForgePolicyEnforcementService.guard()` (or an equivalent `PolicyEngine`
  consumer): policy BEFORE retrieval, exposure metadata from Book I canonical
  objects, retrieval filtered by exposure class before content reaches any LLM.
- Canonical resources map to
  `ResourcePolicyMetadata(CANONICAL_OBJECT, <canonical id>, <ProductExposure>)`.
- Anonymous reads are limited to PUBLIC_TEACHING VIEW/QUERY.
- I.3 must NOT add routes that bypass the enforcement boundary; health/ready/meta
  remain public.

## 22. Book VI handoff assumptions

- Book VI owns producing trusted `AuthorizationContext` objects from commercial
  entitlement/licensing state (subscriptions, plans, provider normalization, Whop).
- Book VI may extend `REGISTERED_CAPABILITIES` and matrix rows via the owning
  governance process; unknown capability atoms still deny by construction.
- Book VI must not interpret II.4 capability atoms as prices, plans, or
  subscription state; `admin.*` atoms remain governance-reserved (no read access
  at II.4); `forge.internal` remains reserved for trusted internal service
  principals.
