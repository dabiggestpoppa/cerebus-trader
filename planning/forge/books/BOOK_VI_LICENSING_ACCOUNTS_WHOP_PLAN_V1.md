# BOOK VI PLAN — LICENSING, ACCOUNTS & WHOP

Status: DETAILED PLANNING V1
Date: 2026-10-05
Parent: GLX_FORGE_MASTER_BUILD_PLAN_V1
Depends on: Book II identity/policy/provider ports; Book V capability-consuming UX
Reference: LEGACY_WHOP_REFERENCE_AUDIT.md from larger-lab/master historical MAD LABS store
Feeds: Books VII, VIII

## Book objective
Commercialize GLX FORGE through licenses and entitlements while keeping CEREBUS IP, user identity and access semantics independent of Whop.

Whop is the initial commerce provider, not the source of product truth.

## Core law

GLX FORGE owns:
PRODUCT -> PLAN -> CAPABILITY BUNDLE -> LICENSE -> ENTITLEMENT -> ACCESS POLICY

Whop owns:
CHECKOUT -> PAYMENT/SUBSCRIPTION STATE -> PROVIDER CUSTOMER/SUBSCRIPTION/EVENT IDs

Bridge:
WHOP EVENT
-> VERIFY
-> NORMALIZE
-> IDEMPOTENT EVENT LEDGER
-> RECONCILE
-> INTERNAL LICENSE/ENTITLEMENT PROJECTION
-> BOOK II POLICY
-> BOOK V/IV ACCESS

A Whop outage may interrupt commerce. It must not redefine CEREBUS, user identity, plan semantics or already-known entitlement truth.

---

# BLOC VI.1 — INTERNAL PRODUCT CATALOG

## Objective
Represent what FORGE sells without encoding provider IDs into the product model.

### Ch VI.1.1 Product identity
Fields:
product_id
name
brand
description
status
product_type
default exposure
availability
metadata/version.

Initial conceptual product:
GLX FORGE — Powered by CEREBUS.

Future products can share the catalog without changing entitlement architecture.

### Ch VI.1.2 Product lifecycle
DRAFT
COMING_SOON
ACTIVE
PAUSED
RETIRED.

Historical MAD LABS store explicitly modeled lifecycle; retain the useful concept, not old products/prices.

### Ch VI.1.3 Plan identity
Plan is a commercial/access package:
plan_id
product_id
name
billing cadence metadata
capability bundle
status
effective dates
display metadata.

Provider price/plan IDs live only in mappings.

### Ch VI.1.4 Capability bundles
Plans grant capabilities such as:
library content
Ask CEREBUS depth
operator workspace
indicator vault
research evidence depth
research lab
API/future institutional access.

Book II policy consumes capabilities.

### Ch VI.1.5 Initial tier hypothesis
Planning baseline, not irreversible pricing:
LIBRARY
PRO
INSTITUTIONAL/CUSTOM.

Historical working ranges:
Library approximately $29-49/month
Pro approximately $99-149/month
Institutional custom.

Exact price points require commercial ratification before production configuration.

### Ch VI.1.6 Billing metadata
Internal plan may express:
monthly/annual/custom
trial eligibility if later approved
grace policy reference
seat policy
currency/display.

Do not implement billing arithmetic that conflicts with provider truth.

### Ch VI.1.7 Feature/exposure mapping
Map capability -> Book I/II exposure permissions and Book V surfaces.

Example:
Library: teaching/library + selected model/evidence.
Pro: operator dashboards/vault + Ask Operator.
Institutional: advanced evidence/API/custom capabilities when actually built.

No capability may promise a feature not implemented/released.

### Ch VI.1.8 Catalog configuration
Brand/store/catalog config externalized where practical.
Version changes and effective dates auditable.

### Ch VI.1.9 Catalog validation
- no duplicate IDs
- active plan requires active product
- capability exists
- retired capability cannot be newly sold
- provider mapping not required to define product.

Acceptance VI.1:
- catalog fully understandable without Whop
- plans map only to internal capabilities
- lifecycle explicit
- pricing can change without changing capability IDs or user identity.

---

# BLOC VI.2 — LICENSE & ENTITLEMENT DOMAIN

## Objective
Define the legal/access state that Book II policy trusts.

### Ch VI.2.1 License object
Fields:
license_id
account_id
product_id
plan_id/version
status
starts_at
ends_at
grace_until
seat_limit
source
terms_version
created/updated.

Statuses:
PENDING
ACTIVE
GRACE
SUSPENDED
EXPIRED
REVOKED
CANCELED_PENDING_END.

### Ch VI.2.2 Entitlement object
Derived/access-grant record:
entitlement_id
license_id
capability_id
status
effective_at
expires_at
source/version.

Entitlement is not the same as payment event.

### Ch VI.2.3 License state machine
Explicit legal transitions:
PENDING -> ACTIVE
ACTIVE -> CANCELED_PENDING_END
ACTIVE -> GRACE
ACTIVE -> SUSPENDED
ACTIVE -> EXPIRED
ACTIVE -> REVOKED
GRACE -> ACTIVE/EXPIRED
CANCELED_PENDING_END -> EXPIRED.

Illegal transitions fail.

### Ch VI.2.4 Entitlement projection
License/plan state projects capabilities transactionally.
Changing plan version or status recalculates only authorized capability set.

### Ch VI.2.5 Grace
Grace is explicit product policy, not accidental provider retry behavior.
During grace, allowed capabilities must be defined.

### Ch VI.2.6 Revocation
Revocation wins over:
provider stale state
session cache
old checkout success
saved frontend state.

Book II cache/session invalidation triggered.

### Ch VI.2.7 Seats
Foundation for institutional/multi-seat:
license seat_limit
membership assignment
seat status.

V1 may ship single-seat plans; schema must not require rewrite for institutional.

### Ch VI.2.8 Terms acceptance
Record:
terms/license version
accepted_at
actor
evidence/reference.

A payment alone is not sufficient evidence of every future terms revision.

### Ch VI.2.9 Manual/admin grants
Support controlled:
comp
beta
research/admin
support correction.

Must include reason, actor, expiration where appropriate and audit.

### Ch VI.2.10 License tests
- duplicate active license rules
- expiry boundary
- grace
- revoke
- plan change
- seat overflow
- terms version
- stale provider event after revoke
- concurrent updates.

Acceptance VI.2:
- policy access can be derived entirely from internal license/entitlement state
- revocation is authoritative
- manual grants are auditable
- seats/terms have durable identity.

---

# BLOC VI.3 — WHOP COMMERCE ADAPTER

## Objective
Integrate current Whop commerce APIs/webhooks behind Book II's provider-neutral commerce port.

### Ch VI.3.1 Provider mapping
Mapping records:
internal product/plan
<-> Whop company/product/plan/access identifiers required by the current integration.

Provider IDs never become internal PKs.

### Ch VI.3.2 Checkout handoff
FORGE requests provider checkout/handoff for a specific internal plan.
Return safe provider destination/session metadata.

Do not grant entitlement from checkout creation.

### Ch VI.3.3 Customer mapping
Verified provider customer/member identity maps to internal account/user through controlled linking.

Email equality alone must not authorize account takeover.

### Ch VI.3.4 Webhook ingress
Requirements:
raw request size limit
signature/authenticity verification using current Whop contract
timestamp/replay controls if supported
event ID extraction
schema validation
safe logging
fast acknowledgment after durable ingest where architecture permits.

Do not implement from historical API assumptions; validate against current Whop docs during implementation.

### Ch VI.3.5 Event normalization
Provider-specific events normalize into internal commerce events such as:
SUBSCRIPTION_STARTED
SUBSCRIPTION_RENEWED
SUBSCRIPTION_CHANGED
PAYMENT_FAILED
CANCEL_SCHEDULED
SUBSCRIPTION_ENDED
REFUNDED/REVOKED where semantics support.

Preserve raw provider event reference/hash for audit without exposing sensitive payload broadly.

### Ch VI.3.6 Idempotency
Unique provider + event ID.
Repeated webhook -> same result/no duplicate entitlement mutation.

### Ch VI.3.7 Out-of-order handling
Event occurrence time/version and reconciliation prevent an older event from resurrecting expired/revoked access incorrectly.

### Ch VI.3.8 Provider lookup/reconciliation reads
Adapter can fetch authoritative current subscription/customer state needed for reconciliation.

### Ch VI.3.9 Adapter errors
Normalize authentication, rate limit, unavailable, malformed response, not found and upstream rejection.

Commerce failure never fails open.

### Ch VI.3.10 Sandbox/test adapter
Where Whop supports sandbox/test mechanisms, use them.
Otherwise fixture/captured-contract tests plus deterministic fake remain mandatory.

Acceptance VI.3:
- verified events map to normalized internal events
- invalid signature rejected
- duplicate event harmless
- checkout alone grants nothing
- provider IDs remain mappings
- current Whop contract is documented/versioned at implementation time.

---

# BLOC VI.4 — EVENT LEDGER & RECONCILIATION

## Objective
Make access recoverable even when webhooks are late, duplicated, missed or out of order.

### Ch VI.4.1 Commerce event ledger
Append-oriented:
internal_event_id
provider
provider_event_id
event_type
occurred_at
received_at
account mapping
provider object refs
normalized payload
processing status
hash/version.

### Ch VI.4.2 Processing state
RECEIVED
VERIFIED
NORMALIZED
APPLIED
IGNORED_DUPLICATE
PENDING_MAPPING
FAILED
RECONCILED.

### Ch VI.4.3 Projection transaction
Within one controlled transaction:
lock relevant license/account
validate transition
append processing result
update license
reproject entitlements
write audit
invalidate policy cache.

### Ch VI.4.4 Missed webhook recovery
Scheduled reconciliation compares internal provider mapping/license state to provider authoritative state.

Differences produce reconciliation event, not silent mutation.

### Ch VI.4.5 Out-of-order conflict
Rules prevent stale event from reversing newer terminal state.
Escalate ambiguous provider history.

### Ch VI.4.6 Pending mapping queue
If provider event is valid but account mapping unresolved:
store safely
grant nothing
queue/admin resolution
retry after mapping.

### Ch VI.4.7 Manual correction
Authorized admin can correct projection with:
reason
before/after
support evidence
actor
timestamp.
Never rewrite/delete original provider ledger.

### Ch VI.4.8 Refund/chargeback/revocation policy
Map provider financial states to explicit license policy.
Do not guess provider semantics.

### Ch VI.4.9 Reconciliation dashboard contract
Counts:
healthy
pending
mismatch
failed
stale
unmapped.
No payment secrets in normal dashboard.

### Ch VI.4.10 Chaos tests
- webhook never arrives
- duplicate x10
- end before start
- renewal after cancel
- provider outage
- account mapping missing
- stale event after admin revoke
- reconciliation mismatch.

Acceptance VI.4:
- access converges to correct internal state after recoverable event loss/order issues
- no event deletion needed
- ambiguity fails closed
- manual correction preserves original evidence.

---

# BLOC VI.5 — ACCOUNT, BILLING & LICENSE UX

## Objective
Give users a clear view of what they bought and what access they currently possess without rebuilding Whop's payment UI.

### Ch VI.5.1 Account page
Show:
account identity
current product/plan
license status
renewal/end date if available/appropriate
capabilities
seat usage where applicable
terms version
support route.

### Ch VI.5.2 Access page
Human-readable:
WHAT YOU HAVE
WHAT IT UNLOCKS
LOCKED FEATURES
WHY ACCESS IS LIMITED if safe.

Use capability semantics, not provider jargon.

### Ch VI.5.3 Upgrade/downgrade
FORGE chooses internal target plan then hands commerce action to Whop/current provider.

After provider action, entitlement changes only after verified/reconciled state.

### Ch VI.5.4 Cancel
Cancellation handoff to provider where applicable.
FORGE displays CANCELED_PENDING_END vs immediately expired correctly.

### Ch VI.5.5 Billing history boundary
Prefer provider-managed detailed financial history unless FORGE has a clear need/legal basis to persist it.
Store only necessary normalized commerce metadata.

### Ch VI.5.6 Grace/payment failure
Clear status:
payment issue
grace access if policy permits
end date/next step.
No scare UI.

### Ch VI.5.7 Institutional/custom
Foundation:
contact/sales handoff
custom license record
seat assignment.
Do not fake self-serve institutional billing if not supported.

### Ch VI.5.8 Terms/license acknowledgement
Surface current terms and require acknowledgement when policy requires.
Record version.

### Ch VI.5.9 Support/admin reference
Expose safe license/account reference IDs for support.
Never ask user to send secrets/webhook payloads.

### Ch VI.5.10 UX tests
- active
- cancel pending
- expired
- grace
- revoked
- plan change pending
- provider outage
- entitlement lag/reconciliation
- institutional/custom.

Acceptance VI.5:
- user can understand access independently of Whop terminology
- UI never treats checkout success page as entitlement proof
- provider outage does not fabricate status
- plan changes converge after verified provider state.

---

# BLOC VI.6 — LEGAL, IP & LICENSE CONTROLS

## Objective
Encode the product's licensing posture into software boundaries while leaving final legal language for attorney review.

### Ch VI.6.1 License doctrine
Commercial intent:
limited
revocable
non-exclusive
non-transferable
access while valid/active according to plan.

Underlying CEREBUS/GLX intellectual property remains owner property.

ATTORNEY REVIEW REQUIRED before production legal text.

### Ch VI.6.2 IP scope
Reserve ownership of:
models
methods
research
code
names/branding
canonical corpus
derivative research/implementation where legally applicable
unreleased parameters/internal methods.

Do not overstate rights beyond counsel-approved language.

### Ch VI.6.3 Acceptable use hooks
Product must support policy for:
credential/account sharing
bulk extraction
redistribution/resale
source/code copying
abusive automation/scraping
attempted access bypass.

Enforcement must be proportional/auditable.

### Ch VI.6.4 Research/financial disclaimer hooks
CEREBUS provides market research/operator intelligence.
No personalized financial advice.
No guaranteed performance/returns.

### Ch VI.6.5 Privacy hooks
Document categories needed:
identity/account
commerce/provider references
usage/security logs
Ask CEREBUS retention per Book IV
support data.

Final policy/cookie/retention requires legal/product review.

### Ch VI.6.6 Terms versioning
Terms/privacy/license documents have:
version
effective date
status
acceptance requirement.

### Ch VI.6.7 Revocation enforcement
Software can revoke capabilities while preserving audit/evidence.
Do not delete canonical/user accounting history merely because access ended.

### Ch VI.6.8 DMCA/IP support hooks
Operational contact/process placeholder if required.
Do not invent legal procedure without counsel.

### Ch VI.6.9 Legal launch checklist
Attorney review:
license agreement
terms
privacy
financial/research disclaimers
refund/cancellation representation
Whop/provider terms compatibility
trademark/brand language
institutional terms.

Acceptance VI.6:
- software can enforce versioned license/access states
- legal text remains configurable/versioned
- no hard-coded unreviewed legal promise
- acceptance evidence retained.

---

# BLOC VI.7 — COMMERCE CONTRACT, SECURITY & REPLACEMENT TESTS

## Objective
Prove FORGE can sell access safely and survive replacing Whop.

### Ch VI.7.1 Fake commerce lifecycle
Simulate:
checkout
start
renew
upgrade
downgrade
cancel pending
payment failure
grace
expire
revoke/refund where modeled.

### Ch VI.7.2 Whop contract tests
Against current integration:
signature/auth
event parsing
mapping
lookup
rate limit/error normalization.

### Ch VI.7.3 Webhook adversarial
- forged signature
- replay
- malformed body
- oversized body
- duplicate ID/different payload
- out-of-order
- unknown plan
- unmapped customer.

### Ch VI.7.4 Entitlement security
Try:
edit client plan name
forge checkout success
reuse old event
guess provider ID
stale cached entitlement
role escalation
direct protected URL.

All fail.

### Ch VI.7.5 Provider outage
Existing known entitlement follows internal state/policy.
New uncertain purchase/change does not grant access until verified.
Reconciliation resumes later.

### Ch VI.7.6 Replacement-provider proof
Implement second fake provider adapter with different IDs/event vocabulary.
Run same normalized lifecycle and prove no domain/UI policy changes.

### Ch VI.7.7 Data minimization
Verify no card/payment secrets stored.
Provider payload retention minimized.
Logs redacted.

### Ch VI.7.8 Load/idempotency
Burst duplicate webhooks and concurrent subscription changes.
No duplicate grants.

### Ch VI.7.9 End-to-end access
purchase event
-> license active
-> entitlement
-> Book II policy
-> Book V unlocked
-> Book IV depth allowed
-> cancel/expire
-> access removed.

### Ch VI.7.10 Evidence pack
Record current provider contract version/date, test fixtures, mappings and known unsupported cases.

Acceptance VI.7:
- complete lifecycle passes with fake provider
- Whop adapter passes current contract suite
- forged/replayed events fail
- replacement-provider proof passes
- end-to-end entitlement/revocation works.

---

# INITIAL FORGE PRODUCT/CAPABILITY MATRIX — PLANNING BASELINE

This matrix is intentionally capability-first. Names/prices can change later.

## LIBRARY
Potential capabilities:
- subscriber CEREBUS Files/library
- canonical model explanations
- selected evidence summaries
- Beginner Ask CEREBUS
- selected indicator education/manual access.

## PRO
Includes Library plus:
- operator dashboards
- Indicator Vault access according to releases
- Operator Ask CEREBUS
- setup context/no-go/state
- deeper evidence views
- saved operator workspace preferences.

## INSTITUTIONAL / CUSTOM
Potential:
- Researcher depth
- advanced evidence/provenance
- API when built/released
- seats
- custom research/data access by contract.

Do not promise future capabilities on checkout pages until they are actually released or explicitly labeled coming soon.

---

# LEGACY WHOP REFERENCE — WHAT WE REUSE

Recovered MAD LABS work demonstrated useful separation:
products/
community/tiers
branding/config
payments/config
integrations/config
master store manifest.

FORGE translates this into:
catalog
plans/capabilities
brand/config
commerce adapters
entitlements
provider mappings
integration configuration.

We do NOT copy:
MAD LABS product names
old prices
placeholder URLs
historical API assumptions
unverified Stripe/PayPal fallback
OCE verification as commerce correctness.

The unresolved historical whop-landing gitlink is reference lineage only, not implementation source.

---

# BOOK VI SECURITY INVARIANTS

1. Checkout creation != entitlement.
2. Client success page != entitlement.
3. Email equality != account ownership proof.
4. Provider ID != internal identity.
5. Webhook authenticity verified before normalization.
6. Duplicate provider event cannot duplicate access.
7. Older event cannot resurrect a newer terminal revocation.
8. Provider outage never fails open.
9. Admin corrections append evidence; do not erase provider history.
10. Revocation invalidates access promptly.
11. UI plan labels do not authorize access.
12. Protected features use Book II capability policy.
13. No payment secrets in app logs/corpus/LLM context.
14. Whop can be replaced without changing CEREBUS or FORGE domain IDs.

---

# BOOK VI ACCEPTANCE / RATIFICATION GATE

Book VI is DONE only when:

## Catalog
- product/plan/capability schema valid
- lifecycle/versioning works
- no provider IDs in core identity.

## License
- state machine passes
- entitlement projection deterministic
- grace/revoke/expire/seat tests pass
- terms acceptance versioned.

## Whop
- current docs/contracts validated at implementation time
- signature/event tests pass
- duplicate/out-of-order handling
- provider mappings explicit.

## Reconciliation
- missed webhook recovery
- pending mapping
- stale conflict
- manual correction
- audit convergence.

## UX
- active/grace/cancel/expired/revoked states clear
- checkout not treated as access proof
- capability display accurate.

## Legal/IP
- configurable/versioned documents/hooks
- attorney-review gate explicitly unresolved until signed off
- license/access enforcement available.

## Replacement/security
- fake provider full lifecycle
- second-provider replacement proof
- forged/replay/direct-access tests fail
- E2E purchase->access->revocation passes.

## Evidence pack
Each Bloc produces PLAN, ACCEPTANCE, implementation commits, test results, EVIDENCE, known gaps and ratification.

Final Book VI record:
catalog version/hash
capability registry version
license schema/state-machine version
Whop adapter contract version/date
provider mapping version
webhook/reconciliation test report
legal review status
known exclusions
ratification commit.

---

# BOOK VI EXCLUSIONS

Do NOT:
- make Whop the user database
- hard-code Whop plan IDs in Book V
- store raw card data
- grant access from redirect/success page
- invent provider webhook semantics from old code
- promise unreleased features
- finalize legal language without attorney review
- build affiliate/referral systems unless separately approved
- build complex tax/accounting engine
- couple CEREBUS model access directly to payment events.

---

# RECOMMENDED IMPLEMENTATION ORDER

1 VI.1 Catalog/capabilities
2 VI.2 License/entitlement state machine
3 fake commerce provider
4 VI.4 generic event ledger/reconciler
5 VI.5 account/access UX contracts
6 current Whop documentation audit
7 VI.3 Whop adapter
8 VI.7 adversarial/replacement tests
9 VI.6 legal/IP hooks + counsel review package
10 E2E purchase/access/revoke
11 evidence pack
12 Book VI ratification/freeze.

Build the internal commercial truth first. Whop integration comes after FORGE knows what a product, license and entitlement mean.

# HANDOFF TO BOOK VII

Book VII can publish/release content and model capabilities into catalog-visible product surfaces, but publishing does not automatically alter paid plan entitlements.

# HANDOFF TO BOOK VIII

Book VIII performs production threat modeling, secret handling, rate limits, disaster recovery, provider outage drills, production Whop mapping validation and final launch/legal readiness.
