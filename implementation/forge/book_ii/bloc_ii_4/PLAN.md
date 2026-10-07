# BOOK II / BLOC II.4 — POLICY & ACCESS CONTROL — PLAN.md

Status: PLAN
Date: 2026-10-07
Starting remote HEAD: `cad9cd7cfffc72e78a0f30b8accd01e39bf6cd9a`
Freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24` (ancestor, verified)
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, II.1 `598b34c`,
II.2 `772a0d2`, II.3 `cad9cd7` (all PASS)

---

## Governing laws (mandatory, restated)

- **IDENTITY != POLICY.** II.3 answers who. II.4 answers what a principal may
  do or receive. The policy kernel never reconstructs identity — it consumes
  an II.3 `ForgePrincipal` as given.
- **AUTHENTICATION != AUTHORIZATION.** A valid principal authorizes nothing.
  Authentication alone never unlocks protected exposure.
- **POLICY != ENTITLEMENT.** II.4 evaluates capability facts; it does not
  produce, refresh, price, or store them.
- **ENTITLEMENT != COMMERCE.** No plan/subscription/license/checkout concept
  exists in II.4. Book VI owns commercial state and will map products to
  capabilities later.
- **EXPOSURE METADATA != POLICY DECISION.** Book I exposure classes are
  inputs to a central policy authority, never scattered `if premium` checks.
- **PROVIDER ID != FORGE ID.** Provider identifiers, emails, and raw request
  fields can never grant capability.
- **POLICY MUST RUN BEFORE RELEASE.** Protected content is never fetched and
  filtered later: DENY ⇒ the protected loader is never invoked. This is the
  pre-retrieval/pre-LLM law the future Ask CEREBUS depends on.

Book VI is read-only context. Whop is not integrated. No LLM, retrieval,
pgvector, indicators, or corpus backfill is implemented.

## Scope

Owns: the pure deterministic policy kernel (`app/forge/policy.py`); the
central exposure matrix for all six canonical exposure classes; the trusted
provider-neutral authorization-context seam Book VI will later populate; the
service-layer enforcement primitive (principal + context + action + safe
resource metadata → decision, with deny-before-load ordering); auditable
decisions with safe reason codes; focused II.4 tests including the
adversarial extraction and internal-exposure suites.

Does NOT own: commercial entitlement production (Book VI), identity/auth
(II.3), corpus backfill (I.3), retrieval/LLM (Book IV), any new public HTTP
route, any policy database.

## Phase 0 truth (recorded)

- Baseline `python -m pytest -q` at `cad9cd7`: **283 passed, 14 skipped**
  (skips = PG integration module; CI executes them).
- No policy/authorization code exists anywhere in `app/forge` beyond II.3's
  identity primitives (grep-verified).
- `ForgeConfig`/container hold a `policy` seam that II.2/II.3 deliberately
  left forbidden (`__post_init__` raised on non-None `policy`). II.4 now
  owns that seam and replaces the guard honestly (purely additive for all
  other fields).
- Exposure classes confirmed in `app/forge/canonical.py` = the six canonical
  classes from `corpus/canonical/PRODUCT_EXPOSURE_RULES_V1.md`.

## Policy decision model

`PolicyDecision` — frozen dataclass: `allowed: bool`,
`reason_code: PolicyReason`, `detail: str` (safe, non-content), plus
`ALLOW`/`DENY` classmethod constructors. Deterministic, comparable, free of
protected content. Machine-readable reason codes (frozen Ch II.4.8 vocabulary
where applicable): `NOT_AUTHENTICATED`, `ENTITLEMENT_MISSING`,
`ACCOUNT_DISABLED`, `ROLE_MISSING`, `EXPOSURE_FORBIDDEN`, `UNKNOWN_ACTION`,
`UNKNOWN_EXPOSURE`, `MALFORMED_CONTEXT`, `OBJECT_UNAVAILABLE`,
`POLICY_UNKNOWN`. No vague bare booleans anywhere in the port.

## Action model

`PolicyAction` str-enum — a deliberately small governed vocabulary:
`VIEW`, `QUERY`, `OPERATE`, `ADMINISTER` (frozen equivalents). Unknown or
arbitrary action strings ⇒ DENY with `UNKNOWN_ACTION`. No per-surface
permission zoo is invented.

## Resource model

`ResourcePolicyMetadata` — frozen dataclass describing ONLY what policy may
know: `resource_type` (bounded str-enum: `CANONICAL_OBJECT`, `ARTIFACT`,
`CAPABILITY`, `SERVICE_ENDPOINT`), `resource_id` (opaque string — id, never
content), `exposure: ProductExposure | None`. Constructing it requires no
protected body: a caller can build it from an index/ID alone. No loaders, no
DB, no network. The pairing to real content happens strictly downstream of
ALLOW.

## Principal input

The kernel consumes II.3 `ForgePrincipal` unchanged (anonymous and
authenticated structurally distinct; policy cannot construct one from email,
provider subject, headers, or raw JSON — it has no such API at all).

## Authorization-context seam (Book VI handoff)

`AuthorizationContext` — frozen, provider-neutral value:
`capabilities: frozenset[str]` (+ `is_present()` marker). It is a passive
fact-carrier constructed explicitly from trusted service input; it contains
no price, billing, plan name, subscription state, provider ID, or raw request
authority. Capability strings are exact-match atoms (no wildcard, no
substring, no prefix logic — enforced by tests). Missing capability ⇒ DENY.
Malformed context (non-frozenset capabilities, wrong type) ⇒ DENY with
`MALFORMED_CONTEXT`. Book VI will later own producing this object from
commercial state; II.4 defines only the consumption contract.

Capability vocabulary (registered constants, exact atoms; the frozen Ch
II.4.2 examples minus anything commercial): `corpus.read.public`,
`corpus.read.member`, `model.read.operator`, `evidence.read.research`,
`admin.research`, `admin.commerce`, plus `forge.internal` — the ONLY
capability that can ever admit INTERNAL_METHOD/INTERNAL_CODE, reserved for
explicitly-configured trusted internal service principals. No FREE/PRO/
PREMIUM marketing atoms exist.

## Exposure matrix (central authority)

`DefaultDenyPolicyEngine.decide(principal, context, action, resource) →
PolicyDecision` implements the single frozen matrix:

| Exposure | Anonymous | Auth, no capability | member cap | operator cap | research cap | internal cap |
|---|---|---|---|---|---|---|
| PUBLIC_TEACHING | ALLOW (`corpus.read.public`) | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| SUBSCRIBER_MODEL | DENY | DENY | ALLOW | ALLOW | ALLOW | ALLOW |
| OPERATOR_ONLY | DENY | DENY | DENY | ALLOW | ALLOW | ALLOW |
| RESEARCH_LAB | DENY | DENY | DENY | ALLOW | ALLOW | ALLOW |
| INTERNAL_METHOD | DENY | DENY | DENY | DENY | DENY | ALLOW |
| INTERNAL_CODE | DENY | DENY | DENY | DENY | DENY | ALLOW |
| unknown/None | DENY | DENY | DENY | DENY | DENY | DENY |

Rationale vs frozen documents: PUBLIC_TEACHING is anonymous-readable per
Product Exposure Rules (concepts/beginner material; the II.3 auth contract
explicitly allows anonymous principals, and no frozen document requires login
to read public teaching). Subscriber tier: `corpus.read.member` + everything
below it (cumulative read-down, standard exposure semantics). OPERATOR_ONLY
and RESEARCH_LAB both sit above subscriber: `model.read.operator` /
`evidence.read.research` each grant their class and everything below.
RESEARCH_LAB access still receives the object AS research — the decision
carries no status mutation, and authorization never touches `EvidenceStatus`
/ claim status / canonical status (tested). INTERNAL_METHOD/INTERNAL_CODE
admit ONLY the `forge.internal` capability; ordinary member/operator/
research capabilities and any combination of them DENY — no staff principal
mechanism is invented beyond this single fail-closed capability atom.
Unknown action, unknown exposure, malformed context, missing context ⇒ DENY.

Role behavior: II.3 `IdentityRole` values are NOT consulted by the matrix
(ROLE_MISSING reason is defined for future governance use, not wired to
permissions at II.4 — role == plan conflation is forbidden).

## Anonymous behavior

Explicitly enumerated: anonymous + VIEW/QUERY + PUBLIC_TEACHING = ALLOW.
Every other anonymous combination = DENY (`NOT_AUTHENTICATED`). Nothing
non-public is reachable without a principal.

## Enforcement service (pre-retrieval primitive)

`app/forge/service/policy_enforcement.py` — `ForgePolicyEnforcementService`:

```
authorize(principal, context, action, resource) -> PolicyDecision
guard(principal, context, action, resource, loader, *, loader_args) -> outcome
```

`guard` is the reusable deny-before-load primitive: it evaluates the kernel
FIRST; on DENY it returns the decision and never touches `loader`; on ALLOW
it invokes `loader(*loader_args)` exactly once and returns
`GuardedAccess(allowed=True, decision, payload)`. Later books (I.3 corpus
surfaces, III, IV Ask CEREBUS, V, VII) call this instead of writing their own
access logic — the pre-LLM boundary is exactly "policy before the loader that
would feed the LLM context".

## Service integration

- The container's existing `policy` seam becomes real: `ForgeServiceContainer`
  accepts an injected `PolicyEngine` (structural guard), keeps default None
  (pure kernel needs no wiring to exist), and `redacted_diagnostics` reports
  `policy_wired` honestly.
- `ForgeAuthenticationService` is reused unchanged — no second auth
  implementation; policy never inspects tokens.
- Readiness: no new dependency (policy is stateless logic, not
  infrastructure); existing readiness semantics untouched.

## Persistence

None. Policy evaluation is stateless and pure (frozen II.4 requires no
policy/audit tables). **No migration is added.** Audit is a safe in-memory
decision-log primitive on the enforcement service (bounded, content-free);
a durable audit sink belongs to a later owning bloc.

## Auditability

`PolicyAuditRecord` — frozen: timestamp, correlation id (caller-supplied, no
reconstruction), principal id (or explicit `anonymous`), action, resource
type/id, exposure, decision, reason code. Never contains: session token,
protected body, internal code text, provider secrets. The enforcement
service can append decisions to an in-memory bounded audit list for tests/
ops; no external sink is wired.

## Error behavior

Denial is returned as a structured `PolicyDecision`, not thrown. The
external HTTP error contract is untouched (403-vs-404 for protected corpus
surfaces is an I.3/route-owning decision; II.4's decision+reason gives the
caller the safe distinction). No enumeration leak is introduced: reasons
describe the rule, not the existence of hidden objects beyond the caller's
own request.

## Determinism & purity

Same trusted inputs ⇒ same decision. No network, no provider calls, no SQL,
no FastAPI, no clock reads inside the kernel (audit timestamps are supplied
by the caller/enforcement layer), no mutable global policy state. Tested
explicitly.

## Testing strategy

Focused suite `tests/test_forge_policy.py`: table-driven exposure matrix
(6 exposures × principal/context combinations), unknown-action/exposure/
malformed-context deny, adversarial extraction test (varying
IDs/types/exposures/actions cannot trigger the loader), internal-exposure
adversarial matrix (anonymous + every ordinary capability combination ⇒
DENY on INTERNAL_METHOD/INTERNAL_CODE), pre-retrieval spy tests (DENY ⇒
loader never called; ALLOW ⇒ called exactly once), purity guards (no
network/SQL/FastAPI/mutable global), commercial-object absence, decision/
audit content hygiene, II.3 regression integration (invalid/expired/revoked
token or disabled user can never reach the loader), and full-scope
regression.

## Book VI handoff

Book VI receives: the `AuthorizationContext` seam (construct one with
capability atoms from commercial state), the capability registry, and the
guarantee that policy consumes capabilities only. Book VI must NOT need to
touch the matrix to launch a product.

## I.3 handoff

I.3 receives: `ForgePolicyEnforcementService.guard` as the mandatory gateway
for any canonical-object surface; `ResourcePolicyMetadata` built from
canonical ID + Book I exposure metadata without loading the object; the
frozen contract that corpus content crosses into a response/LLM context only
after ALLOW.
