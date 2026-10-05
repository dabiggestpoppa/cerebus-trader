# BOOK II PLAN — FORGE CORE / PLATFORM

Status: DETAILED PLANNING V1
Date: 2026-10-05
Parent: `GLX_FORGE_MASTER_BUILD_PLAN_V1.md`
Depends on: Book I contracts and canonical object identities
Feeds: Books III, IV, V, VI, VII, VIII

## Book objective

Build the provider-independent application substrate beneath GLX FORGE.

Book II owns runtime composition, persistence, identity, sessions, authorization policy, provider boundaries and observability. It must be possible to run and test FORGE with no Whop and no OpenRouter. A provider outage or replacement must not redefine CEREBUS truth, user identity, license semantics, exposure policy or audit history.

Book II is infrastructure, not market intelligence.

## Architectural law

```
CLIENT / INTERNAL CALLER
        |
        v
APPLICATION BOUNDARY
        |
  +-----+-------------------+
  |                         |
IDENTITY                 REQUEST CONTEXT
  |                         |
  +----------+--------------+
             v
        POLICY ENGINE
             |
       ALLOW / DENY
             |
     +-------+--------+
     |                |
 DOMAIN SERVICES   PROVIDER PORTS
     |                |
     v                v
 POSTGRES          ADAPTERS
 canonical        LLM / commerce /
 account          notifications /
 license          object storage
 audit
```

Hard rule: protected data is filtered/authorized before a provider receives it.

---

# BLOC II.1 — SERVICE SKELETON & RUNTIME CONTRACT

## Objective
Create a boring, deterministic application shell that every later Book can depend on without owning deployment assumptions.

### Ch II.1.1 Repository/runtime layout
Define the FORGE application package boundaries:
- domain
- application/use-cases
- persistence
- policy
- providers/ports
- providers/adapters
- API/interface
- observability
- jobs/workers
- tests/fixtures

Keep canonical corpus source distinct from runtime projections.

Tests:
- import/dependency boundary test
- no domain import from concrete provider adapters
- application boot test

### Ch II.1.2 Configuration contract
Typed configuration with explicit required/optional fields and no silent production defaults.

Configuration classes:
- application
- database
- auth
- policy
- provider selection
- observability
- feature/release flags
- environment

Rules:
- secrets never committed
- startup fails on invalid production config
- provider credentials are adapter concerns
- configuration values expose redacted diagnostic representation

Tests:
- valid dev/test/prod fixtures
- missing production secret fails
- redaction test
- unknown/invalid enum fails

### Ch II.1.3 Environment profiles
Define LOCAL, TEST, STAGING, PRODUCTION.

Environment changes deployment/configuration, not domain semantics.

Tests:
- production cannot enable test bypasses
- staging and production use same schema contracts
- TEST can use fake providers without code branching in domain layer

### Ch II.1.4 Application lifecycle
Explicit startup/shutdown sequence:
1. load config
2. initialize observability
3. database connectivity
4. migration/schema compatibility check
5. load policy configuration
6. initialize provider adapters
7. readiness
8. graceful shutdown/drain

Tests:
- dependency failure prevents readiness
- shutdown closes DB/provider resources
- partial startup cannot report ready

### Ch II.1.5 Health/readiness/liveness
Separate:
- liveness: process alive
- readiness: safe to serve
- dependency diagnostics: privileged/admin-safe detail

Do not leak credentials, provider payloads or corpus internals.

### Ch II.1.6 Migration runner
One authoritative migration path with ordered immutable migrations.

Rules:
- app refuses incompatible schema
- no ad-hoc CREATE/ALTER during normal request handling
- migrations have forward verification
- destructive migration requires explicit migration plan

### Ch II.1.7 Local developer harness
One-command local stack using:
- Postgres + pgvector
- fake identity/auth where explicitly TEST/LOCAL
- fake LLM
- fake commerce
- deterministic seed corpus/account fixtures

Acceptance II.1:
- application boots from empty local environment
- health/readiness semantics are correct
- test runtime requires no paid/external provider
- provider code cannot contaminate domain imports
- migration compatibility is checked before readiness

---

# BLOC II.2 — PERSISTENCE & DATA INTEGRITY

## Objective
Create the durable state layer for canonical knowledge projections and commercial/user state without collapsing their meanings.

## Persistence domains

At minimum, schemas/tables must distinguish:
- canonical registry projection
- source/provenance projection
- retrieval documents/embeddings
- users/accounts/identities
- roles
- products/plans
- licenses
- entitlements
- provider mappings
- provider events
- access/audit events
- application jobs
- release/version metadata

### Ch II.2.1 Database foundation
PostgreSQL as authoritative transactional store. pgvector is an extension for semantic retrieval, not the source of canonical truth.

Tests:
- required extension check
- transaction behavior
- timezone UTC storage
- deterministic IDs/constraints

### Ch II.2.2 Canonical projection tables
Persist Book I objects while preserving:
- canonical ID
- object type
- version
- lifecycle status
- exposure class
- payload/schema version
- content hash
- effective/supersession metadata

The DB projection may optimize queries but cannot silently alter canonical meaning.

### Ch II.2.3 Provenance/relationship graph
Represent typed edges such as:
SUPPORTS, DEFINES, IMPLEMENTS, VISUALIZES, SUPERSEDES, DERIVED_FROM, CONFLICTS_WITH, ALIAS_OF.

Prevent impossible/dangling launch edges.

### Ch II.2.4 Retrieval/embedding storage
Store:
- retrieval object ID/version
- structured payload
- safe semantic text
- embedding vector
- embedding model/version
- exposure class
- canonical hash
- generated-at timestamp

Changing embedding provider/model does not change canonical object identity.

### Ch II.2.5 Account and access tables
Foundation for Book VI:
- user
- account
- external identity
- role binding
- license
- entitlement
- product/plan capability projection
- provider mapping

No Whop ID as primary identity.

### Ch II.2.6 Audit/event ledger
Append-oriented records for:
- authentication/security events
- policy decisions
- protected retrieval access
- entitlement changes
- provider event ingestion/reconciliation
- administrative mutations

Audit payloads must avoid secrets and unnecessary corpus content.

### Ch II.2.7 Transaction/concurrency rules
Define transaction boundaries for:
- entitlement mutation
- provider-event ingestion
- canonical projection update
- retrieval rebuild publication
- role/revocation changes

Use idempotency/uniqueness where repeated external events are possible.

### Ch II.2.8 Migration discipline
Migration metadata:
- ID
- parent/current schema version
- forward action
- verification
- rollback/recovery strategy
- destructive/non-destructive classification

### Ch II.2.9 Backup/restore contract
Book II defines mechanism; Book VIII performs launch-grade drills.

Minimum:
- database backup procedure
- restore into clean instance
- schema/version verification
- row/count/hash verification for critical tables
- RPO/RTO placeholders to ratify later

### Ch II.2.10 Persistence test matrix
Include:
- empty DB bootstrap
- migrate N-1 -> N
- duplicate IDs
- dangling relations
- duplicate provider event
- concurrent entitlement updates
- backup/restore smoke
- vector index rebuild without canonical loss

Acceptance II.2:
- clean DB reaches current schema deterministically
- critical constraints fail closed
- canonical and commercial identities are independent of providers
- vector data can be deleted/rebuilt without losing canonical truth
- audit records survive normal projection rebuilds
- backup/restore smoke passes

---

# BLOC II.3 — IDENTITY, ACCOUNT & SESSION CORE

## Objective
Know who is calling FORGE without binding identity to Whop, an LLM provider or a single authentication vendor.

### Ch II.3.1 Internal identity model
Stable internal `user_id` is authoritative.

External identities map:
```
provider + provider_subject -> internal_user_id
```

Support future identity-provider replacement/account linking.

### Ch II.3.2 Account model
Separate person/user identity from account/license ownership where needed.

Initial design must not block:
- individual account
- future organization/institutional account
- seats/memberships
- admin/service accounts

Do not overbuild organization UX in Book II; preserve the domain seam.

### Ch II.3.3 Authentication adapter
Define an auth port that yields a verified principal:
- user ID
- session ID
- authentication strength/method if relevant
- issued/expiry
- trusted claims

Concrete vendor is replaceable.

### Ch II.3.4 Session contract
Session properties:
- opaque identifier
- expiration
- revocation
- rotation where applicable
- account/user binding
- no entitlement snapshot trusted indefinitely

Entitlements must be re-evaluable after revocation/change.

### Ch II.3.5 Account linking
Rules for linking multiple external identities to one internal user.

Security:
- authenticated proof required
- collision protection
- no email-string-only takeover
- audit every link/unlink

### Ch II.3.6 Roles
Platform roles are separate from paid entitlements.

Initial roles:
- USER
- RESEARCH_ADMIN
- SUPPORT_ADMIN
- SYSTEM_ADMIN
- SERVICE

No generic ADMIN bypass that implicitly grants all corpus exposure without explicit policy.

### Ch II.3.7 Service identity
Background jobs/provider callbacks receive constrained service principals and scopes.

Webhook authenticity is not equivalent to user authentication.

### Ch II.3.8 Revocation
Support:
- session revocation
- user disable
- external identity unlink
- role removal
- account suspension

Policy must observe revocation promptly.

### Ch II.3.9 Identity security tests
Test:
- forged subject
- linked-account collision
- expired session
- revoked session
- disabled user
- privilege escalation
- role vs entitlement confusion
- service principal misuse

Acceptance II.3:
- user identity survives auth-provider replacement
- Whop customer identity cannot authenticate by itself
- roles and entitlements are distinct
- revocation closes protected access
- account linking cannot occur from unverified identifier equality

---

# BLOC II.4 — POLICY & EXPOSURE ENGINE

## Objective
Make authorization a deterministic FORGE capability, not scattered `if premium` checks.

## Decision model

```
principal
+ account
+ active entitlements
+ role/scopes
+ requested capability
+ object exposure
+ object lifecycle/status
+ request context
= ALLOW / DENY + reason code
```

### Ch II.4.1 Exposure taxonomy
Book I exposure metadata becomes enforceable runtime policy.

Minimum conceptual classes:
- PUBLIC
- MEMBER
- PRO
- INSTITUTIONAL
- INTERNAL_RESEARCH
- INTERNAL_METHOD
- INTERNAL_CODE

Exact names can be frozen during implementation, but ordering/meaning must be explicit.

### Ch II.4.2 Capability registry
Examples:
- corpus.read.public
- corpus.read.member
- model.read.operator
- evidence.read.research
- indicator.vault
- ask.beginner
- ask.operator
- ask.researcher
- admin.research
- admin.commerce

Plans map to capabilities in Book VI; policy consumes capabilities only.

### Ch II.4.3 Entitlement resolver
Resolve active capabilities from internal entitlement state.

Rules:
- expiration respected
- revocation wins
- grace state explicit
- stale provider state cannot directly override internal projection during a request

### Ch II.4.4 Object authorization
Policy evaluates each canonical/retrieval object before it can enter downstream context.

This is the core anti-leakage invariant:
**filter before retrieval/context handoff, not after LLM generation.**

### Ch II.4.5 Lifecycle/status policy
Exposure and epistemic status are separate.

Example:
A PRO user may be entitled to a research object but the answer must still label it EXPERIMENTAL rather than VALIDATED.

### Ch II.4.6 Depth/mode policy
Beginner/Operator/Researcher are presentation/retrieval depths, not automatic trust tiers.

Entitlement may grant a depth; depth cannot bypass object exposure.

### Ch II.4.7 Deny-by-default
Unknown capability, unknown exposure, malformed principal, missing entitlement or unresolved policy state => DENY.

### Ch II.4.8 Policy reason codes
Machine-readable reason codes:
- NOT_AUTHENTICATED
- ACCOUNT_DISABLED
- ENTITLEMENT_MISSING
- ENTITLEMENT_EXPIRED
- ROLE_MISSING
- EXPOSURE_FORBIDDEN
- OBJECT_UNAVAILABLE
- POLICY_UNKNOWN

User-facing messages need not reveal hidden object existence.

### Ch II.4.9 Policy simulation/explain
Admin/test tooling can explain a decision without exposing secrets:
principal class + capability + policy rule + result.

### Ch II.4.10 Policy adversarial suite
Test:
- direct object-ID guessing
- semantic retrieval leakage
- alias to internal object
- historical version leakage
- vector result leakage
- revoked subscription
- admin-role confusion
- malformed exposure
- provider outage
- stale cache

Acceptance II.4:
- all protected object paths use central policy
- deny-by-default proven
- unauthorized objects are excluded before LLM/provider boundary
- revoked entitlement blocks subsequent protected retrieval
- aliases/versions cannot bypass exposure
- policy decisions are auditable

---

# BLOC II.5 — PROVIDER PORTS & ADAPTER BOUNDARIES

## Objective
External vendors are replaceable implementation details.

### Ch II.5.1 Provider contract doctrine
Domain/application code imports ports/interfaces, never OpenRouter/Whop-specific clients.

Every provider contract defines:
- request
- response
- timeout
- retry ownership
- idempotency expectations
- error taxonomy
- health semantics
- redaction rules

### Ch II.5.2 LLM port
Book II defines only transport/provider abstraction:
- generate
- optional structured output capability
- model identifier
- usage/cost metadata
- timeout/cancel
- normalized errors

Prompt/retrieval intelligence belongs to Book IV.

Implement:
- fake deterministic LLM
- OpenRouter adapter later under Book IV or adapter implementation chapter

### Ch II.5.3 Commerce port
Provider-neutral operations needed by Book VI:
- checkout/session handoff as applicable
- customer/subscription lookup
- provider event normalization
- health/reconciliation reads

Internal entitlement mutation does NOT live in the adapter.

Implement fake commerce provider before Whop.

### Ch II.5.4 Notification port
Only if needed by launch:
- send transactional notification
- normalized delivery result

Do not prematurely build marketing automation.

### Ch II.5.5 Object/blob storage port
If runtime needs non-database protected artifacts:
- put/get metadata
- signed/authorized access strategy
- delete/version behavior

Library/GitHub recovery sources are not automatically production blob storage.

### Ch II.5.6 Provider registry/factory
Configuration selects adapters at composition root.

No `if provider == whop` spread through domain code.

### Ch II.5.7 Failure normalization
Common classes:
- unavailable
- timeout
- rate_limited
- invalid_request
- authentication_failed
- upstream_rejected
- malformed_response
- unknown

### Ch II.5.8 Circuit/fallback policy
Fallback must be explicit per provider type.

LLM fallback may select another model/provider.
Commerce must not fabricate success when unavailable.
Authorization never fails open because a provider is down.

### Ch II.5.9 Fake providers
Deterministic fakes support:
- success
- latency
- timeout
- duplicate events
- out-of-order events
- invalid signature/event shape where applicable
- rate limit
- hard failure

### Ch II.5.10 Replacement tests
Run identical contract suite against fake adapters and each concrete adapter.

Acceptance II.5:
- core application passes with only fake providers
- no provider identifier is required as core domain PK
- commerce outage cannot grant access
- LLM outage cannot corrupt canonical state
- adapter replacement requires composition/config change, not domain rewrite

---

# BLOC II.6 — OBSERVABILITY, AUDITABILITY & ERROR CONTRACT

## Objective
Make every important FORGE decision traceable without logging secrets or leaking proprietary corpus content.

### Ch II.6.1 Request correlation
Every request/job has correlation/request ID propagated through:
API -> identity -> policy -> persistence -> provider call -> response.

### Ch II.6.2 Structured logging
Structured events, not free-form dumps.

Fields include where appropriate:
- timestamp
- environment
- request/job ID
- actor class/internal ID
- operation
- object/capability ID
- outcome
- reason code
- duration
- provider/model IDs
- error class

Never log raw secrets or unnecessary full protected context.

### Ch II.6.3 Tracing
Trace high-value boundaries:
- auth
- policy
- DB
- retrieval
- provider
- jobs

Keep proprietary payloads out of span attributes.

### Ch II.6.4 Metrics
Foundation metrics:
- request rate/errors/latency
- DB latency/pool
- policy allow/deny counts
- auth failures
- retrieval counts
- provider latency/error/rate-limit
- LLM token/cost metadata
- commerce event processing
- job lag/failure

### Ch II.6.5 Retrieval access audit
Record protected retrieval facts:
who/which service, capability, canonical/retrieval object IDs, exposure, decision, timestamp.

Do not copy full source documents into audit records.

### Ch II.6.6 Entitlement audit
Record:
- grant
- renew
- grace
- expire
- revoke
- admin correction
- source event/provider mapping

### Ch II.6.7 Error taxonomy
Stable application errors:
- AUTHENTICATION
- AUTHORIZATION
- VALIDATION
- NOT_FOUND
- CONFLICT
- RATE_LIMIT
- DEPENDENCY
- DATA_INTEGRITY
- INTERNAL

Map provider errors to application errors without leaking internals.

### Ch II.6.8 Safe error responses
Production responses:
- stable code
- safe message
- request ID
No stack traces, SQL, secrets, hidden object existence or provider credential detail.

### Ch II.6.9 Cost/usage ledger
Record LLM/provider usage enough for later cost controls:
request, provider/model, input/output usage if supplied, normalized cost if known, latency, success.

No financial accounting claims unless provider data supports them.

### Ch II.6.10 Observability tests
Test:
- request ID propagation
- redaction
- policy decision logged
- provider error normalized
- protected text absent from logs
- metrics emitted
- audit append behavior

Acceptance II.6:
- protected access and entitlement mutations are reconstructable from audit metadata
- secrets/protected corpus are absent from standard logs
- provider and application failures are distinguishable
- request IDs connect user-visible errors to internal traces

---

# BOOK II CROSS-BLOC INTEGRATION

## Integration path A — protected corpus request

```
request
-> authenticate principal
-> load account/session
-> resolve capability
-> query candidate canonical/retrieval objects
-> policy filter candidates
-> audit decision/access
-> return authorized objects to caller
```

At no point may an unauthorized object be passed to an LLM for later redaction.

## Integration path B — entitlement change

```
trusted internal/provider event
-> normalize event
-> idempotency check
-> transaction
-> mutate entitlement projection
-> append audit/event record
-> invalidate relevant auth/policy cache
-> commit
```

Whop implementation belongs to Book VI. Book II proves the generic path with a fake provider.

## Integration path C — provider failure

```
adapter failure
-> normalized dependency error
-> observability event
-> explicit fallback if policy allows
-> otherwise graceful failure
```

Never:
provider failure -> assume paid
provider failure -> expose INTERNAL
provider failure -> mutate canonical truth

---

# SECURITY INVARIANTS ESTABLISHED IN BOOK II

1. Authentication does not imply entitlement.
2. Role does not imply every corpus exposure.
3. Commerce identity does not equal FORGE identity.
4. Provider data is untrusted until adapter validation/normalization.
5. Unknown policy states deny.
6. Entitlement revocation beats caches.
7. Retrieval exposure is enforced before external LLM context.
8. Vector similarity never bypasses object authorization.
9. Canonical truth survives embedding/provider loss.
10. Audit logs do not become a shadow copy of proprietary corpus.

Book VIII later hardens/red-teams these invariants; Book II must make them structurally possible.

---

# BOOK II ACCEPTANCE / RATIFICATION GATE

Book II is DONE only when all are demonstrated:

## Runtime
- clean application boot in LOCAL/TEST
- readiness refuses incompatible/unavailable critical dependencies
- graceful shutdown works
- production config has no test bypass

## Database
- empty Postgres+pgvector -> current schema
- migration verification passes
- canonical projection loads
- vector projection rebuilds independently
- backup/restore smoke passes
- duplicate/dangling critical records fail

## Identity
- internal identity independent of provider
- session expiration/revocation works
- role escalation tests fail
- external identity collision/linking tests pass

## Policy
- deny-by-default
- protected objects filtered before provider boundary
- direct-ID, alias, historical-version and vector leakage tests fail closed
- entitlement revocation observed promptly
- decision reason/audit available

## Providers
- complete application core runs against deterministic fakes
- fake LLM can be swapped without domain change
- fake commerce can be swapped without entitlement-domain change
- provider outage never grants access

## Observability
- request correlation works end-to-end
- protected access is auditable
- secrets/protected corpus absent from normal logs
- dependency failures normalize correctly

## Evidence pack
Each Bloc produces:
- `PLAN.md`
- `ACCEPTANCE.md`
- implementation commit ladder
- test output
- `EVIDENCE.md`
- unresolved issue list
- ratification record

Final Book II evidence records:
- schema version
- migration head
- test counts
- provider contract versions
- policy version/hash
- known exclusions
- Book II ratification commit

---

# BOOK II EXCLUSIONS

Do NOT implement in Book II:
- market calculations or CEREBUS model logic
- Ask CEREBUS prompting/retrieval orchestration beyond generic protected retrieval primitives
- TradingView indicators
- production Whop-specific business behavior
- pricing decisions
- frontend dashboards
- research promotion workflows
- autonomous trading/execution
- personalized financial advice
- final production security certification

Those belong to later Books.

---

# RECOMMENDED IMPLEMENTATION ORDER

1. II.1 Service Skeleton
2. II.2 Persistence
3. II.3 Identity/Session
4. II.4 Policy Engine
5. II.5 Provider Ports/Fakes
6. II.6 Observability
7. Cross-bloc adversarial integration suite
8. Book II evidence pack
9. Ratify/freeze Book II contracts before Books III/VI depend on them

Parallelism is intentionally limited. Identity and policy should not be built against a moving persistence model; provider adapters should not define domain contracts by accident.

# HANDOFF TO BOOK III / VI

Book III may assume:
- canonical IDs are durable
- persistence transactions exist
- request identity is available
- policy can protect model/setup objects
- observability is available
- market intelligence does not need to understand Whop.

Book VI may assume:
- stable internal user/account identity
- product-neutral entitlement storage
- provider-neutral commerce port
- audit/event ledger
- policy consumes internal capabilities, not Whop product IDs.

This separation is mandatory for FORGE to remain replaceable, licensable and survivable as providers change.
