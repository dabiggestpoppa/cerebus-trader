# BOOK III — WP-3 DEPENDENCY AND HANDOFF

**Packet:** BA-24 Rung 1 (WP-3A)
**Purpose:** separate WP-3 into independently authorizable packets, state every
upstream dependency and amendment path, and define what each packet hands to the
next. No packet may absorb another's authority.

---

## 1. Packet separation

| Packet | Authorizes | Delivers | Explicitly does not |
|---|---|---|---|
| **WP-3A** | analysis and selection only | `PLAN.md`, `ACCEPTANCE.md`, `PROVIDER_DECISION_MATRIX.md`, this file | connect, configure, code, test, buy |
| **WP-3B** | adapter code against synthetic fixtures | `app/forge/market_data_ingest/`, additive III.1 registrations, 66 contract tests, 12 fixtures | credentials, network, readiness change |
| **WP-3C** | real credentials and licensed slices | 6 external tests, captured `SOURCE_SLICE` data, licence records | readiness claim, route exposure |
| **WP-3D** | parity window and operational proof | R1–R10 evidence, reconnect/failover drills, Book II amendment request | production GO, paid launch |

Critical path: **3A → 3B → 3C → 3D.** 3B may not start before the vendor
decision and the additive-registration authorization. 3C may not start before
3B is green. 3D may not start before 3C and WP-4 retention.

---

## 2. Upstream dependencies

| Dependency | Needed by | Why | If absent |
|---|---|---|---|
| WP-1 integration (done) | all | frozen cross-bloc contracts | — |
| Operator vendor ratification (3A exit) | 3B | a boundary must target one contract | stop |
| Additive III.1 registrations | 3B | JPY instruments and provider schemas do not exist | stop; do not bend contracts |
| **WP-4 durability** (III.4-GAP-10, III.6-GAP-1) | 3C/3D | retained source slices and replay across sessions | in-memory only; no durable parity evidence |
| **WP-2 route registration / Book II amendment** | 3D and any customer-visible use | readiness seam lives in frozen `container.py`/`health.py`; consumers need routes | seam cannot flip; data stays internal |
| **WP-5 Book I card ADR** | independent | card schema defect is unrelated to ingestion | none for WP-3 |
| Provider licensing confirmation | 3C | lawful display to paying users | internal research only |

WP-3 does **not** wait on WP-5, Book IV or Book V.

---

## 3. Concurrency

| Packet | Runs with | Conflict risk |
|---|---|---|
| 3A | WP-4, WP-5, Book IV/V planning | none (documents only) |
| 3B | WP-4, WP-5, Book IV/V prototyping | additive III.1 table edits; must rebase on WP-4 only if WP-4 touches `market_data` (it should not) |
| 3C | WP-4 | credential/environment isolation is mandatory |
| 3D | WP-2 (consumption), WP-4 (retention) | readiness edit requires Book II amendment; routes frozen until then |

Rule: no two packets edit the same file in the same rung. 3B's additive edits
are confined to `normalize.PROVIDER_SCHEMAS`, `instruments.build_default_registry`
provider mappings and instrument tuples; nothing else in III.1 is touched.

---

## 4. Frozen surfaces and amendment path

| Surface | State | Amendment |
|---|---|---|
| Book I corpus | frozen | Book I ADR only (WP-5) |
| Book II contracts, 50 hashes | frozen | Book II packet + re-freeze |
| `service/routes.py` (`145757e0…`) | frozen | WP-2 only |
| `service/container.py` / `health.py` market-data entry | `NOT_CONFIGURED`, `required=False` | Book II amendment in WP-3D |
| III.1–III.6 semantics, 8 quality flags, refusal vocabulary | frozen | none proposed; WP-3 adds no codes |
| Migrations `001`–`004` | frozen set | WP-4 only, additive |
| 79 module files | frozen content unless a rung authorizes an additive edit | additive registrations listed in PLAN §6 |

Any need to change a signature, enum or vocabulary is a stop condition, not an
implementation choice.

---

## 5. Handoff interfaces

**3A → 3B**

- Ratified vendor list with per-instrument routing.
- The four additive registration items (schemas, mappings, JPY instruments,
  optional kernel rollup) approved or refused individually.
- Explicit confirmation that 3B runs with no credentials and no network.

**3B → 3C**

- Adapter package with a fake/recorded provider used by contract tests.
- 66 green contract tests; fixtures reproducible byte-identically.
- Frozen-integrity report: 50 hashes, 79 modules, `001`–`004`, routes hash,
  seam unchanged.
- A capture harness that can record a licensed slice with provenance metadata.

**3C → 3D**

- 6 green external tests on licensed captures (`SOURCE_SLICE`, `source_ref`,
  licence note, capture timestamp).
- Terms record: vendor, tier, permitted display, restrictions, renewal date.
- Credential inventory proving environment isolation and absence from artifacts.

**3D → operations**

- R1–R10 evidence bundle and the parity/recovery reports.
- Book II amendment receipt for the readiness entry.
- Honest residual-gap list (staleness policy, XAU/JPY sessions, BTC anchors).

---

## 6. Open-gap handoff

| Gap | Stays open after WP-3A | Closes at |
|---|---|---|
| III.1-GAP-1 real history | yes | 3C licensed captures |
| III.1-GAP-4 provider wiring | yes | 3D evidence |
| III.1-GAP-5 live parity | yes | 3D parity window |
| III.1-GAP-2 session families (XAU/JPY) | yes | Book I/research decision |
| III.1-GAP-3 final-bar rules beyond M5 | yes | research |
| III.6-GAP-2 provider unconfigured | yes | 3D |
| III.6-GAP-4 staleness threshold | yes | product/governance |
| III.5-GAP-7 setup live parity | yes | 3D |
| III.4-GAP-10 / III.6-GAP-1 durability | yes | WP-4 |
| III.3-GAP-8 BTC weekly/monthly anchors | yes | research |

No gap is closed by documentation. WP-3A closes **none** of them; it defines the
evidence that would.

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Licence forbids paying-user display | medium | high | business tier + written confirmation before 3C; OANDA excluded from display |
| Aggregator changes schema/symbols | medium | medium | versioned mappings, pre-network validation, contract tests |
| Historical vs live basis divergence | high | high | parity gate R6; per-bar source identity; no silent blending |
| Quiet-window bars absent (quote-derived FX) | medium | medium | silence → `GAP`, never a flat bar |
| Rate-limit exhaustion during backfill | medium | low | token buckets, file archives, checkpoint/resume |
| Credential leakage | low | critical | env injection, redaction law, fixture scans |
| Readiness flips without evidence | low | critical | R1–R10 gate; `required=False` until consumption |
| Vendors disagree beyond a tick | medium | medium | `OUTLIER_SOURCE` blocking, per-instrument source policy |

---

## 8. Stop conditions and authorization asks

Stop if: vendor ratification is withheld; registrations are refused; licensing
is unclear at 3C; parity fails without a documented cause; a frozen surface must
change; or a credential would appear in the repository, logs or fixtures.

This rung requests, and has not received:

1. Vendor/tier approval (Twelve Data business; Polygon business; Kraken public).
2. Authorization for the four additive III.1 registrations.
3. Authorization to provision credentials in a deployment environment.
4. A cost ceiling.
5. Confirmation that derived-intelligence display (not raw redistribution) is the
   intended licensed use.

Until these are answered, the only permitted WP-3 activity is synthetic,
credential-free contract work under a separate authorization.

---

## 9. Verification for this rung

- Four documents written; no other path changed.
- Foundation re-measured: HEAD/remote `c6bb05a…`, 79 modules, migrations
  `001`–`004`, routes `145757e0…`, seam `NOT_CONFIGURED`, CI green.
- Inventory counted: 72 unique names, 66 `M` + 6 `X`.
- Vendor claims labelled `VERIFIED`/`UNVERIFIED` with access date 2026-11-07.
- PLAN/ACCEPTANCE agree on counts, packet names and gate vocabulary.
- No credential, endpoint, account or network call exists in this packet.
