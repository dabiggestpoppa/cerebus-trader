# Book I / Bloc I.3 — Canonical Backfill — ACCEPTANCE

Clauses are executable gates; the focused suite maps tests to clause ids.

## A. INVENTORY
A1. Every in-scope I.3 source artifact (7 model cards, 10 evidence cards, 3 setup
cards, 1 claim registry) is inventoried by the deterministic inventory module.
A2. Inventory is deterministic: same tree state ⇒ same classification, counts,
and order (no timestamps, no dict-order dependence).
A3. Each artifact carries a deterministic content identity
(`sha256:<hex>` via `compute_content_identity`).
A4. No source file is modified, moved, or deleted by I.3.
A5. Unsupported/unmigrated artifacts appear in the report with classification
and reason (quarantine/gap is a truthful outcome, never hidden).

## B. LEGACY ID MAPPING
B1. `SETUP.XAU.QUARTER_ZONE.V1` → `SET.XAU.QUARTER_ZONE.V1` (explicit registry).
B2. `SETUP.FIB.REKEY.V1` → `SET.FIB.REKEY.V1`; `SETUP.JPY.CARRY_ROLE_GATE.V1` →
`SET.JPY.CARRY_ROLE_GATE.V1`.
B3. Unprefixed legacy model ids map to `MOD.*` (7 explicit entries).
B4. Mappings are registry entries with expected object type + reason; a mapping
applied to the wrong object type is rejected (no `MOD` id for a SETUP card).
B5. Invalid legacy ids do not fuzzy-map (unknown legacy id ⇒ quarantine).
B6. No two legacy ids map to the same canonical id; evidence/claim ids are
passthrough after `CanonicalId.parse` type validation.
B7. Legacy ids preserved in `metadata["legacy_ids"]`.

## C. ENUM / STATUS MAPPING
C1. All status mappings are explicit registry entries with reasons.
C2. Unknown status ⇒ QUARANTINED (never nearest-enum coercion).
C3. No promotion: no mapping sends CANDIDATE/RESEARCH_FLAG/HISTORICAL/DESCRIPTIVE
to VALIDATED/FORWARD_OOS; `CANONICAL_FROZEN_FAMILY` → DESCRIPTIVE (demotion,
`frozen_family: true`); `NEGATIVE_EVIDENCE` → FALSIFIED with `evidence_type`
NEGATIVE_EVIDENCE preserved (negative result classified, not laundered).
C4. `VALIDATED_RESEARCH`/`VALIDATED_SMALL_N`/`VALIDATED_RELATIONSHIP` → VALIDATED
with `research_sample`/`small_n`(+N)/`relationship_statistic` metadata so the
qualifier survives; small-N results are never surfaced without N.
C5. Evidence-type mapping table explicit; unknown type ⇒ QUARANTINED;
compound `SCIENTIFIC_RETEST + FORWARD_OOS` → FORWARD_OOS with
`historical_component` metadata.

## D. MODEL CARDS
D1. All 7 model cards parse into valid machine `ModelCard` objects (I.1 schema).
D2. Typed canonical ids (`MOD.*`) preserved; evidence_card_ids are valid `EV.*`.
D3. No silent field loss: full parsed payload stored in `metadata["card"]`.
D4. No generic metadata dumping as substitute for structured required fields.

## E. EVIDENCE CARDS
E1. All 10 evidence cards parse into valid machine `EvidenceCard` objects.
E2. Evidence type, status, sample/period, source, claim relationship,
limitations and negative evidence survive (payload preserved; markers
`NOT_SPECIFIED_IN_SOURCE` used for historically absent structured dimensions —
uncertainty preserved, nothing fabricated).
E3. Evidence→CLAIM reference resolves for every card.

## F. SETUP / OPERATOR CARDS
F1. All 3 setup cards parse into valid machine `SetupOperatorCard` objects
(`SET.*` typed ids; parent `MOD.*`).
F2. `MANUAL_OPERATOR` preserved exactly where source states it (JPY, XAU).
F3. `RESEARCH_ONLY` preserved exactly where source states it (Fib rekey).
F4. No `AUTOMATION_APPROVED` is created anywhere in I.3 (none exists in source);
automation approval is never inferred from strategy validity.

## G. CLAIMS
G1. All 10 registry claims exist as canonical CLAIM objects with typed `CL.*` ids.
G2. `ClaimIdentity` preserves market / event_definition / conditioning_event /
clock_origin / horizon / tolerance / eligibility / implementation_semantics;
dimensions the source does not state carry `NOT_SPECIFIED_IN_SOURCE` markers.
G3. Result/statistic values remain in metadata only, never in identity.
G4. Parallel populations are never merged (`compare_claim_identity`).

## H. NUMERICAL CLAIMS
H1. Every numerical claim has a resolvable CLAIM→EVIDENCE→source path, or is
classified UNSUPPORTED_CLAIM (gap), never canonical truth without evidence.
H2. The BTC Tracker family carries no fabricated evidence card (honest empty
evidence set; no invented statistics).

## I. PROVENANCE
I1. Every migrated object has ≥1 provenance edge from a registered artifact with
deterministic content identity and repo-relative locator.
I2. Card markdown → object edges are `DEFINES`; the Phase1 ledger →
`EV.EUR.DAILY.PHASE1_TIERS.V1` is `SUPPORTS`; named Pine files → models are
`IMPLEMENTS`; EUR quarter/month trackers → `MOD.EUR.HIGHER_ORDER.V1` are
`VISUALIZES`.
I3. `SUPPORTS` is never used for visual/conversation-derived sources.
I4. Named-but-missing source files classify MISSING_SOURCE (never fabricated).

## J. VISUAL SOURCES
J1. Visual trackers remain non-empirical support (`VISUALIZES`); they never
establish empirical truth (`classify_support` never returns EMPIRICAL from
VISUAL-only sources).

## K. CONVERSATION-DERIVED SOURCES
K1. Conversation-derived material is inventoried as non-empirical and is not
canonicalized into empirical support.

## L. NEGATIVE EVIDENCE
L1. Fib R11 overgeneration survives migration: evidence object exists with
`evidence_type=NEGATIVE_EVIDENCE`, status FALSIFIED, referenced by the Fib model
and the Fib rekey setup.
L2. The R15/generator distinction is preserved in payload (no deletion of
negative results because they reduce product neatness).

## M. HISTORICAL REFERENCES
M1. No canonical object is fabricated to satisfy a historical reference;
historical narrative stays in preserved card payloads and artifacts.
M2. No reference is silently dropped (full payload preservation).

## N. EXPOSURE
N1. Every migrated object carries a valid frozen `ProductExposure`.
N2. Exposure assignments follow PRODUCT_EXPOSURE_RULES_V1 explicitly (per-card
table for evidence cards); unknown exposure fails closed (quarantine).
N3. PUBLIC_TEACHING is never assigned by default.

## O. INTERNAL MATERIAL
O1. No INTERNAL_METHOD/INTERNAL_CODE body appears in any report, log, or route.
O2. II.4 policy module is untouched by backfill; no bypass is added.

## P. PERSISTENCE
P1. All writes go through the II.2 `PersistenceGateway` port inside one
transaction batch; no ad-hoc SQL; no direct DB writes.
P2. Persisted round-trip preserves canonical semantics (id, status, exposure,
references, claim identity, metadata payload).
P3. No new migration; `discover_migrations()` remains `[1, 2]`.

## Q. IDEMPOTENCY
Q1. Applying twice over identical source state yields NO-OP/ALREADY_CURRENT on
the second run with zero duplicate canonical truth.

## R. CONFLICT
R1. Existing canonical id with different governed content ⇒ explicit conflict
error; no silent overwrite; batch aborted atomically.

## S. DRY RUN
S1. DRY_RUN parses, maps, validates, audits, reports — and performs zero
persistent writes (object/artifact/edge counts unchanged).

## T. TRANSACTION / ROLLBACK
T1. Batch granularity = one full APPLY run; a failure inside the batch leaves
no partially canonicalized truth (II.2 deferred-transaction rollback).

## U. POLICY BOUNDARY
U1. Backfill does not modify `app/forge/policy.py` or the enforcement service;
no entitlement/license/Whop data is created.

## V. NO NEW PUBLIC CORPUS ROUTE
V1. No `/corpus`, `/models`, `/claims`, `/evidence`, `/setups`, `/artifacts` (or
similar) public route is added; route table unchanged.

## W. REPRODUCIBILITY
W1. Same repository source state + mapping rules ⇒ same canonical identities,
content hashes, and audit classifications (deterministic report hash).

## X. REGRESSION
X1. I.1, I.2, II.1, II.2, II.3, II.4, Signal Guard, and the full repository
suite are green; no existing test weakened or deleted.
