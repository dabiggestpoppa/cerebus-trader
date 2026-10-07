# BOOK II / BLOC II.4 — POLICY & ACCESS CONTROL — ACCEPTANCE.md

Status: ACCEPTANCE
Date: 2026-10-07
Freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, II.1 `598b34c`,
II.2 `772a0d2`, II.3 `cad9cd7`

Each clause names its verification. "test" = executable in the focused II.4
suite (`tests/test_forge_policy.py`) or the pre-existing regression suites;
"review" = inspection recorded in EVIDENCE.md.

## A. Policy decision

- A1 Structured deterministic decision — test: `PolicyDecision` carries
  `allowed`, `reason_code`, `detail`; equality is value-based.
- A2 ALLOW/DENY constructors produce auditable reasons, never bare booleans.
- A3 Decision contains no protected content — test: decision fields scanned
  against body strings; `detail` is rule-descriptive only.

## B. Action

- B1 Governed actions only — test: `PolicyAction` = VIEW/QUERY/OPERATE/
  ADMINISTER.
- B2 Unknown action string ⇒ DENY `UNKNOWN_ACTION` — test.
- B3 No per-surface permission zoo — review: no other action vocabulary
  exists in II.4.

## C. Resource

- C1 Safe metadata only — test: `ResourcePolicyMetadata` constructible from
  type + opaque id + exposure alone; no body field exists.
- C2 Resource type bounded — test: unknown resource type rejected/DENY.
- C3 No protected-body dependency — test: authorizing never imports or calls
  a loader.

## D. Principal

- D1 Kernel consumes `ForgePrincipal` unchanged — test: anonymous and
  authenticated principals produce matrix-correct decisions.
- D2 Policy cannot reconstruct identity — review + test: kernel exposes no
  API taking email/provider subject/headers/JSON.

## E. Authorization context

- E1 Trusted seam, provider-neutral — test: `AuthorizationContext` carries
  `capabilities: frozenset[str]` only (plus presence marker).
- E2 No commercial fields — test: no price/billing/plan/subscription/
  provider-id field anywhere in the context type.
- E3 Capability atoms exact-match — test: wildcard/substring/prefix strings
  grant nothing.
- E4 Malformed context ⇒ DENY `MALFORMED_CONTEXT` — test.
- E5 Missing context on protected resource ⇒ DENY — test.

## F. PUBLIC_TEACHING

- F1 Anonymous VIEW allowed (Product Exposure Rules authorize public
  teaching for anonymous consumption; II.3 explicitly supports anonymous) —
  test.
- F2 Anonymous allowed for VIEW/QUERY only; OPERATE/ADMINISTER denied.

## G. SUBSCRIBER_MODEL

- G1 Authenticated without capability ⇒ DENY `ENTITLEMENT_MISSING`.
- G2 `corpus.read.member` ⇒ ALLOW; anonymous ⇒ DENY.

## H. OPERATOR_ONLY

- H1 `model.read.operator` required; member cap ⇒ DENY; anonymous ⇒ DENY;
  authenticated-no-capability ⇒ DENY.

## I. RESEARCH_LAB

- I1 `evidence.read.research` required; member cap ⇒ DENY.
- I2 Authorization never mutates status — test: deciding on a RESEARCH_LAB
  object leaves `EvidenceStatus`/record untouched (no mutation path exists;
  kernel is pure).

## J/K. INTERNAL_METHOD / INTERNAL_CODE

- J1/K1 Anonymous, authenticated-no-capability, member, operator, research
  caps — ALL DENY `EXPOSURE_FORBIDDEN` — table-driven adversarial test.
- J2/K2 Only `forge.internal` capability admits them — test.
- J3/K3 Combined ordinary customer capabilities (member+operator+research)
  still DENY — adversarial test.

## L. Unknown exposure

- L1 Unknown/unset exposure value ⇒ DENY `UNKNOWN_EXPOSURE`/`POLICY_UNKNOWN`
  — test: never coerced to a nearest class.

## M. Anonymous

- M1 Anonymous is explicitly enumerated: PUBLIC_TEACHING VIEW/QUERY only;
  all else DENY `NOT_AUTHENTICATED` — table test.

## N. Authenticated without authorization context

- N1 Valid principal + no trusted capability ⇒ DENY protected exposure —
  test (SUBSCRIBER_MODEL and above).

## O. Provider data

- O1 Provider subject / Whop-style ID / email strings passed as capabilities
  grant nothing — test: context containing such atoms still denies (exact
  atom match only).
- O2 Raw request fields have no path into policy — review.

## P. Pre-retrieval enforcement

- P1 DENY ⇒ protected loader never invoked — test: spy loader records zero
  calls.
- P2 ALLOW ⇒ loader invoked exactly once with the guarded args — test.
- P3 Loader result only reachable through `GuardedAccess` when allowed —
  test: denial outcome exposes no payload.

## Q. Pre-LLM seam

- Q1 The enforcement primitive is reusable for corpus/LLM-context callers —
  test: `guard` composes around an arbitrary loader; kernel independent of
  retrieval.
- Q2 No LLM/retrieval code introduced — review.

## R. Error contract

- R1 Denial is a structured decision, not a thrown 500 — test.
- R2 Existing FORGE error envelope untouched; no new enumeration surface —
  review.
- R3 Authentication failure vs authorization denial distinguishable
  internally (exception vs decision) without leaking hidden-resource
  existence — test.

## S. Audit

- S1 Audit record carries correlation id, principal id/anonymous, action,
  resource type/id, exposure, decision, reason — test.
- S2 Audit never contains token/protected body/internal code — test: audit
  scan against those strings.
- S3 Bounded audit memory; no external sink; no policy database — review.

## T. Determinism

- T1 Same inputs ⇒ equal decisions (repeated calls, value equality) — test.
- T2 Purity: no network/SQL/FastAPI imports in the kernel — test (module
  source scan + no socket/db imports).
- T3 No mutable global policy state — test: two engine instances decide
  independently; module holds no mutable policy registry.

## U. Persistence

- U1 No migration added — test: `discover_migrations()` still `[1, 2]`; 001
  SHA-256 pin unchanged; 002 unchanged.
- U2 No policy/audit tables — test: table-set scan unchanged.

## V. HTTP enforcement

- V1 No new public route — test: route set remains exactly
  `/forge/v1/health|ready|meta`.
- V2 Health/ready/meta behavior unchanged (II.1/II.2 contracts) — test.
- V3 No corpus CRUD route — test/review.

## W. Internal classes

- W1 Explicit INTERNAL_METHOD/CODE adversarial matrix (all ordinary
  principal/capability combinations DENY) — test.
- W2 Only the single `forge.internal` capability atom admits them — test.

## X. No commercial ownership leak

- X1 No Plan/Subscription/License/WhopCustomer/BillingStatus/Price domain
  object — test: vocabulary scan over II.4 modules.
- X2 Capability names are permission facts, not marketing names — test: no
  FREE/PRO/PREMIUM atoms.

## Y. Regression

- Y1 I.1 green. Y2 I.2 green. Y3 II.1 green. Y4 II.2 green. Y5 II.3 green.
- Y6 Signal Guard green (run separately). Y7 Full repository green; no test
  weakened or removed.

## Z. Adversarial extraction

- Z1 Varying resource id/type/exposure/action/query wording cannot cause
  loader execution without authorization — test: N denied attempts ⇒ loader
  calls == 0.
- Z2 Denied loader result cannot leak body — test.
