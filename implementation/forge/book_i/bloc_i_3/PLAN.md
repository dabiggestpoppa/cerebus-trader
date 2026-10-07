# Book I / Bloc I.3 — Canonical Backfill — PLAN

> Status: ACTIVE
> Date: 2026-10-07
> Governing law: PRESERVE TRUTH, PRESERVE LINEAGE, PRESERVE UNCERTAINTY, PRESERVE
> NEGATIVE EVIDENCE. Migration is representation change, never epistemic promotion.

## 1. Source inventory (Phase 0 truth)

Verified repository truth at `ebda556` (II.4 final head; baseline 369 passed,
14 skipped). In-scope I.3 canonical card corpus:

- `corpus/canonical/models/` — **7 model cards**
- `corpus/canonical/evidence/` — **10 evidence cards**
- `corpus/canonical/setups/` — **3 setup/operator cards**
- `corpus/canonical/CLAIM_REGISTRY_V1.md` — **10 claims** (the claim registry)

Governance contracts (`ANSWER_CONTRACT_V1.md`, `CEREBUS_CANONICAL_TAXONOMY_V1.md`,
`CLAIM_REGISTRY_V1.md` header sections, `ONTOLOGY_CROSSWALK_V1.md`,
`PRODUCT_EXPOSURE_RULES_V1.md`, `RETRIEVAL_OBJECT_SCHEMA_V1.md`, `schemas/*`) are
the RULES the migration must obey, not corpus objects to migrate; they are
inventoried as governance-contract artifacts and are NOT canonicalized into
domain objects (self-referential migration is fabrication of a second ontology's
authority). `corpus/conversation-derived/*` is inventoried as conversation-derived,
non-empirical, and is not canonicalized.

Known input condition (I.1 verification, deliberately deferred to I.3):
model cards 0/7 IDs compatible (unprefixed legacy ids), evidence cards 10/10 IDs
compatible but only 5/10 statuses compatible, setup cards 0/3 IDs compatible
(`SETUP.*` vs canonical `SET.*`).

## 2. Migration unit

One card file = one canonical aggregate. The file is parsed deterministically
(front-matter `key: value` fields + known sections), validated against the
ratified I.1 machine schemas (`ModelCard`, `EvidenceCard`, `SetupOperatorCard`),
then persisted as a `CanonicalObject` aggregate through the II.2
`PersistenceGateway` port, with the full parsed card payload preserved in
`metadata["card"]` (no silent field loss) and a `ClaimIdentity` on CLAIM objects.
The historical file is never modified; it is registered as an `Artifact` with
deterministic content identity and typed provenance edges back to the canonical
object.

## 3. Canonical ID mapping (explicit registry, no string replacement)

Mapping registry = bounded data in `app/forge/backfill/mappings.py`, every entry
carrying `reason` + expected object type, type-validated at use. Unprefixed model
ids gain the frozen `MOD` prefix (I.1 `_ID_PREFIX`):

- `EUR.DAILY.NEWS_REKEY.V1` → `MOD.EUR.DAILY.NEWS_REKEY.V1`
- `EUR.HIGHER_ORDER.V1` → `MOD.EUR.HIGHER_ORDER.V1`
- `EUR.WEEKLY.V1_1` → `MOD.EUR.WEEKLY.V1_1`
- `XAU.GAME.L1_L2_L3.V1` → `MOD.XAU.GAME.L1_L2_L3.V1`
- `BTC.TRACKER.DWM.V1` → `MOD.BTC.TRACKER.DWM.V1`
- `CROSSASSET.FIB.RANGE_BIRTH.V1` → `MOD.CROSSASSET.FIB.RANGE_BIRTH.V1`
- `JPY.CARRY_GAME.L1_L3.V1` → `MOD.JPY.CARRY_GAME.L1_L3.V1`

Setup cards (frozen taxonomy §10 + I.1 prefix law; `SETUP` is NOT a canonical
prefix):

- `SETUP.XAU.QUARTER_ZONE.V1` → `SET.XAU.QUARTER_ZONE.V1`
- `SETUP.FIB.REKEY.V1` → `SET.FIB.REKEY.V1`
- `SETUP.JPY.CARRY_ROLE_GATE.V1` → `SET.JPY.CARRY_ROLE_GATE.V1`

Evidence and claim ids are already canonical (`EV.*`, `CL.*`); the registry
records them as `IDENTITY_PASSTHROUGH` after `CanonicalId.parse` validation —
not because string matching says so, but because each parses with the expected
type. No two legacy ids map to one canonical id. Legacy ids are preserved in
`metadata["legacy_ids"]`. Object type is taken from the registry entry, never
inferred from title text.

## 4. Enum / status mapping (explicit, auditable, no promotion)

EvidenceStatus mappings (legacy → canonical, each with reason):

| Legacy | Canonical | Reason |
|---|---|---|
| `VALIDATED` | `VALIDATED` | passthrough |
| `FORWARD_OOS` | `FORWARD_OOS` | passthrough |
| `CANDIDATE` | `CANDIDATE` | passthrough |
| `VALIDATED_RESEARCH` | `VALIDATED` | validated within recovered research sample; `research_sample: true` metadata; exposure stays RESEARCH-appropriate; NOT forward-OOS |
| `VALIDATED_SMALL_N` | `VALIDATED` | validated in source sample; `small_n: true` + N preserved; never surfaced without N |
| `VALIDATED_RELATIONSHIP` | `VALIDATED` | relationship statistic validated; `relationship_statistic: true` (never a trade WR) |
| `RESEARCH_FLAG_SMALL_N` | `RESEARCH_FLAG` | small-N research flag preserved as research flag |
| `NEGATIVE_EVIDENCE` | `FALSIFIED` | the R11 generator approach the claim concerns is falsified; `evidence_type` stays `NEGATIVE_EVIDENCE` so the negative dimension survives as first-class evidence |
| `CANONICALIZATION_CANDIDATE` / `CORE_CANDIDATE` / `SCIENTIFIC_CORE_CANDIDATE` / `RESEARCH_OPERATOR_CANDIDATE` | `CANDIDATE` | canonicalization-stage candidate; no promotion |
| `CANONICAL_FROZEN_FAMILY` | `DESCRIPTIVE` | family-level frozen architecture; per-claim epistemic status lives in Evidence Cards; `frozen_family: true` metadata. NO model-level promotion to VALIDATED |
| `ACTIVE_RESEARCH_IMPLEMENTED` | `RESEARCH_FLAG` | active research, implemented as indicator; `implemented: true`; not validated |
| `MODERN_RESEARCH_FRAMEWORK` | `RESEARCH_FLAG` | research framework; not validated |

Every mapping is identity-preserving or demoting; none crosses a promotion
boundary (HISTORICAL→VALIDATED, CANDIDATE→VALIDATED, RESEARCH_FLAG→FORWARD_OOS,
DESCRIPTIVE→OBSERVED, IMPLEMENTATION_NOT_PARITY_SAFE→AUTOMATION_APPROVED, etc.
are all absent by construction). Unknown/unmapped legacy status ⇒ QUARANTINED,
never nearest-enum coercion.

EvidenceType mappings: `SCIENTIFIC_RETEST`→`SCIENTIFIC_RETEST`;
`SCIENTIFIC_RETEST + FORWARD_OOS`→`FORWARD_OOS` (compound collapses to its
strongest frozen member; `historical_component: SCIENTIFIC_RETEST` metadata);
`SCIENTIFIC_RESEARCH_RESULT`→`SCIENTIFIC_RETEST` with the single explicit
per-card override `EV.FIB.R11.ANCHOR_OVERGEN.V1`→`NEGATIVE_EVIDENCE` (it is the
corpus's negative-evidence card); `RAW_RESEARCH_LEDGER`→`RAW_BACKTEST`;
`OPERATOR_RESEARCH`→`HISTORICAL_REPORT` with `operator_research: true` (not live
trade-log proof). Unknown evidence type ⇒ QUARANTINED.

Layer normalization: leading frozen token wins (`L3 + cross-layer routing`→`L3`,
`L1 / …`→`L1`); `CROSS_LAYER_CONTEXT`→`CROSS_LAYER`; `L1_L2`→`CROSS_LAYER` with
`layer_detail: "L1_L2"` (no Layer enum value exists for L1_L2; detail preserved).

## 5. Parser / loader strategy

Deterministic template parser only (`app/forge/backfill/parser.py`): H1 title,
`key: value` front-matter block, `## Section` bodies, `Beginner:/Operator:/
Researcher:/Forbidden:` Ask-CEREBUS lines. No LLM parsing, no prose inference
across the repository, no remote fetch. A card that violates its template
(missing required identity fields, unknown enum after mapping, unparsable id)
is QUARANTINED with reason — never "AI repaired".

Absent structured fields (e.g. evidence-card event-identity dimensions the
historical format never carried) are stamped with the honest, deterministic
marker `NOT_SPECIFIED_IN_SOURCE` in the corresponding machine field. This
preserves uncertainty explicitly instead of fabricating values; it is a
structured per-field value, not generic metadata dumping.

## 6. Canonical object construction

- MODEL: `ModelCard` validated (evidence_card_ids from the explicit
  model→evidence mapping derived from the Claim Registry), then
  `CanonicalObject(MOD.*, …)` with card payload in metadata.
- EVIDENCE: `EvidenceCard` validated, then `CanonicalObject(EV.*, …)`.
- SETUP: `SetupOperatorCard` validated (typed ids preserved: `SET.*`,
  parent `MOD.*`), then `CanonicalObject(SET.*, …)`. Execution class is
  preserved exactly: MANUAL_OPERATOR / AUTOMATION_APPROVED / RESEARCH_ONLY;
  automation approval is never inferred from strategy validity (no card claims
  AUTOMATION_APPROVED; none will be created).
- CLAIM: 10 registry claims as `CanonicalObject(CL.*, …)` with `ClaimIdentity`
  (market from card; dimensions the source does not state carry
  `NOT_SPECIFIED_IN_SOURCE` markers); result/statistic values live ONLY in
  metadata, never in identity. References: CLAIM→EVIDENCE (`supported_by`),
  CLAIM→MODEL (`belongs_to`), MODEL→EVIDENCE (`supported_by`),
  EVIDENCE→CLAIM (`evidence_for`), SETUP→MODEL (`parent`), SETUP→EVIDENCE
  (`supported_by`).

## 7. Provenance mapping

Each card file is registered as a `MARKDOWN` artifact
(`compute_content_identity`, `derive_artifact_id`, locator = repo-relative path)
with edge relation `DEFINES` → its canonical object. Additional typed edges
where the cards name real in-repo sources (artifact registered only if the file
exists; else `MISSING_SOURCE` classification, never fabricated):

- `corpus/research/eur/daily_range_tracker/PHASE_1_LEDGER.md` `SUPPORTS`
  `EV.EUR.DAILY.PHASE1_TIERS.V1` (named as source_artifact by that card).
- `corpus/indicators/eur/CEREBUS_Daily_News_Rekey_Engine_V1_1_P90_MERGED_FIX1.pine`
  `IMPLEMENTS` `MOD.EUR.DAILY.NEWS_REKEY.V1`;
  `corpus/indicators/xau/CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine` `IMPLEMENTS`
  `MOD.XAU.GAME.L1_L2_L3.V1`;
  `corpus/indicators/btc/CEREBUS_BTC_Daily_Weekly_Monthly_Tracker_V1.pine`
  `IMPLEMENTS` `MOD.BTC.TRACKER.DWM.V1`.
- `corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1.pine` and
  `…_V1_2.pine` `VISUALIZES` `MOD.EUR.HIGHER_ORDER.V1` (visualizer ≠ evidence).

`SUPPORTS` is never used for visual/conversation sources. No `SUPERSEDES`/
`DERIVED_FROM` edges are fabricated where no frozen source states them.

## 8. Exposure stamping

Model and setup cards carry valid frozen `product_exposure` values
(SUBSCRIBER_MODEL ×7 models, OPERATOR_ONLY ×2 setups, RESEARCH_LAB ×1 setup) —
passthrough after enum validation. Evidence cards historically carry none; each
receives an explicit per-card exposure from the frozen Product Exposure Rules:
validated evidence-backed statistics → SUBSCRIBER_MODEL; candidate /
small-N-flag / negative-evidence research material → RESEARCH_LAB. Unknown
exposure fails closed (quarantine). PUBLIC_TEACHING is never assigned by
default. INTERNAL_METHOD/INTERNAL_CODE remain protected: backfill reports
contain counts and ids only, never card bodies.

## 9. Numerical claims

Every registry claim already names an Evidence Card; canonicalization requires
CLAIM→EVIDENCE→source resolution (`claim_source_chain`). A numerical claim
(result metadata present) without a resolvable empirical evidence path is
classified UNSUPPORTED_CLAIM and quarantined/gapped, never promoted to canonical
truth. Results stay outside `ClaimIdentity`; parallel populations are never
merged (`compare_claim_identity`).

## 10. Persistence, idempotency, conflict, rollback

Runner (`app/forge/backfill/runner.py`) with explicit DRY_RUN and APPLY modes;
explicit CLI/module invocation only — never on import, never on startup, never
on a web request (tested). Writes go through the II.2 `PersistenceGateway` port
only (`create_object` / `create_artifact` / `add_provenance_edge` inside one
`gateway.transaction()` batch): no ad-hoc SQL, no direct DB writes. No new
migration (the 001 schema already stores objects/artifacts/edges).

- DRY_RUN: parse, map, validate, audit, report — zero writes.
- APPLY: one logical batch; failure rolls back the whole batch (II.2 deferred
  transaction semantics); emits a deterministic audit summary.
- Idempotency: second apply over identical source state is a deterministic
  NO-OP/ALREADY_CURRENT (existing object with identical content hash → skipped;
  counts reported).
- Conflict: existing canonical id with DIFFERENT governed content → explicit
  conflict error, no silent overwrite, batch aborted atomically.

## 11. Policy boundary

Backfill tooling operates internally through the persistence port. II.4 policy
is untouched; no entitlement/license/Whop data is created; no corpus read route
is added (`/corpus`, `/models`, `/claims`, `/evidence`, `/setups`, `/artifacts`
are all forbidden in I.3). Any future read surface must consume the II.4 guard.

## 12. Audit report

Deterministic report (`BackfillReport.to_json()`): sources inventoried, ready,
mapped, migrated, unchanged, quarantined, missing source, unresolved reference,
unsupported numerical claim, models/evidence/setups/claims/artifacts/provenance
edges, negative evidence, visual-only, conversation-derived, conflicts — counts
and canonical/artifact ids only. Report never contains INTERNAL_METHOD or
INTERNAL_CODE bodies (there are none in scope; the guard is tested anyway).

## 13. Model-specific truth tests

Regression fixtures prove: EUR Daily ≠ Weekly ≠ Higher Order; XAU L3/L2/L1
separation; BTC Tracker migrated independently and BTC Game NOT fabricated
(no BTC Game object exists after apply); JPY role asymmetry (EURJPY
confirmation/veto, not equal vote); Fib R11 overgeneration survives as negative
evidence (FALSIFIED status + NEGATIVE_EVIDENCE type) and Range Birth doctrine is
not reduced to coordinates; ST-family doctrine preserved via EUR Daily P90-merge
caution (no P90 win-rate import; P90 stays distinct); no autonomous execution
approval anywhere.

## 14. I.4 handoff

I.3 delivers persisted canonical objects + artifacts + provenance edges with
deterministic identities. I.4 (retrieval index) must: index only through the
persistence port; stamp/query exposure through II.4 policy before release;
never index INTERNAL_METHOD/INTERNAL_CODE bodies; treat quarantined/gap
objects as non-retrievable truth (research gaps are valid outputs).
