# BOOK IV / BLOC IV.1 — DEPENDENCY HANDOFF

**Bloc:** IV.1 · **Rung:** BA-26 Rung 1 (planning)
**Consumers:** IV.2 retrieval, IV.3 context, IV.4 LLM gateway, IV.5 validator,
IV.6 evaluation, Book V surfaces.

---

## 1. Contract map (actual surfaces at `1df1b1d`)

| Contract | Producer | Surface used by IV.1 | Status |
|---|---|---|---|
| C01 canonical identity | Book I | `canonical.py::CanonicalId`, `ObjectType`, `EvidenceStatus`, `ProductExposure`, `Layer` | FROZEN |
| C02 claim/evidence | Book I | ids/status vocabulary only; no bodies | FROZEN |
| C03 retrieval object | Book I | `retrieval/aliases.py::HISTORICAL_ALIASES`, exact lookup | FROZEN |
| C04 principal | Book II | `identity.py::ForgePrincipal`, `AuthorizationContext` | FROZEN |
| C05 authorization | Book II | `policy.py`, `service/policy_enforcement.py` (`authorize`, `guard`) | FROZEN |
| C07 snapshot | Book III.6 | `Snapshot`, `SnapshotKey`, `SnapshotRequest`, `HistoricalRequest`, `SetupContextRequest`, `InstrumentViewRequest`, `BasketRequest` | RATIFIED |
| C08 setup | Book I definition + III.5 runtime | `SetupContextPayload`, four-valued eligibility | RATIFIED |
| C09 Ask CEREBUS answer | Book IV (later) | not implemented by IV.1 | OUT OF SCOPE |
| C10 capability | Book VI (not implemented) | max authorized depth only, injected | **ABSENT** |

Frozen integrity: Book II 50/50 hashes, planning 23/23 pins, Book III 79
modules (11/12/13/13/16/14), migrations `001`–`004`, router hash
`145757e0…d190af`, provider `NOT_CONFIGURED`.

---

## 2. III.6 compatibility (verified against actual DTOs)

`SnapshotKey` requires: `instrument_id`, `model_id`, `model_version`, `layer`,
`as_of`, `data_cutoff`, `calculation_version`, with optional `clock_id` and
`session_id`.

`SnapshotRequest` has the same required fields plus `surface`; `HistoricalRequest`
adds `retention_acknowledged`; `SetupContextRequest` takes `setup_id`,
`setup_version`, `surface`; `InstrumentViewRequest` takes `layers`;
`BasketRequest` is JPY-only.

Therefore an IV.1 plan must carry enough to build these requests **only when
the user supplied or canonically determined each field**. IV.1 never invents
`as_of`, `data_cutoff`, `calculation_version` or a model version. When a field
is absent the plan records a material ambiguity; IV.2 may resolve it from an
authorized context, but IV.1 does not fabricate it.

No `snapshot_id`/`snapshot_hash` is accepted or emitted. III.6 derives identity
from the key (`identity.py::snapshot_id`).

Refusals owned by III.6 that IV.1 must surface, not reinterpret:
`PROVIDER_NOT_CONFIGURED`, `STALE_DATA`, `DATA_QUALITY_BLOCKED`, `NONFINAL_BAR`,
`CLOCK_UNRESOLVED`, `MIXED_CUTOFF`, `VERSION_DRIFT`, `UNKNOWN_MODEL`,
`UNKNOWN_VERSION`, `HISTORICAL_UNAVAILABLE`, `HISTORICAL_NOT_RETAINED`,
`SETUP_UNRESOLVED`, `SCHEMA_INCOMPATIBLE`, `NO_GO_ACTIVE`.

`NO_GO_ACTIVE` is a market fact; unavailability refusals are not market facts.
IV.1 must never convert either into an action recommendation.

---

## 3. Book II entitlement boundary

- The interpreter receives `max_authorized_depth` and a policy fingerprint from
  the caller; it does not query entitlements.
- `effective_depth` is a presentation ceiling, not access.
- IV.1 emits no `exposure`, `execution_class`, `eligible`, `verdict`,
  `automation_permitted` or `probability` field.
- Any depth cap is recorded as `DEPTH_CAPPED` without disclosing the principal's
  plan or the existence of restricted content.
- Book VI capability projection is absent (III.6-GAP-6); until it exists the
  caller may pass `max_authorized_depth` from the current Book II policy, and
  IV.1 tests use a fixture ceiling, never a real entitlement.

---

## 4. Book III current-data limitations

- `market_data` seam is `NOT_CONFIGURED`, `required: false`; no live snapshot
  can be produced at this head.
- IV.1 still emits `CURRENT` + `requires_live_intelligence = true`; downstream
  III.6 returns `PROVIDER_NOT_CONFIGURED`.
- No historical corpus or model doctrine may be substituted for current state.
- `as_configured` sessions/clocks exist, but IV.1 must not assume a current
  bar, cutoff or session state.
- Fib production eligibility and XAU `WATCH` ceiling remain Book III/Book I
  facts, not IV.1 decisions.

---

## 5. Downstream dependency map

| Consumer | Receives from IV.1 | Must not receive |
|---|---|---|
| IV.2 retrieval | intent, entities, ids, market, layer, scope, flags, ambiguity | a verdict or numeric answer |
| IV.3 context | plan id, requested fields, depth, evidence/lineage flags | protected content |
| IV.4 LLM gateway | context package built by IV.3 | raw plan with unrestricted ids? (only authorized package) |
| IV.5 validator | plan id, claim/evidence refs, scope, setup requirement | a pre-authorized claim |
| IV.6 evaluation | fixture id, expected plan, actual plan | market truth assertions |
| Book V | answer contract (IV.5) + plan id | a second retrieval engine |

Dependency order remains `IV.1 → IV.2 → IV.3 → IV.4 fake → IV.5 → IV.6 →
OpenRouter adapter`, per `AGENT_EXECUTION_HANDOFF_V1.md`.

---

## 6. Handoff artifact

Rung 2 must produce, alongside the interpreter package:

1. `AskCerebusQueryPlan` canonical JSON schema version
   `ASK_QUERY_CONTRACT.V1`.
2. Fixture manifest with LF-normalized SHA-256 for Q-01–Q-12.
3. Test report for A-01–A-60 with exact pass count.
4. A statement of gaps: live data unavailable, Book VI capability absent,
   BTC Game/P90/Fib production authority unresolved.
5. No change to Book I/II/III source, tests or frozen fixtures.

---

## 7. Stop conditions for handoff

- Any consumer requires a plan field outside the frozen set.
- Any consumer expects IV.1 to supply a market fact, evidence body, verdict or
  entitlement decision.
- III.6 DTO fields diverge from the mapping in §2.
- A downstream Bloc needs a new intent or generation not in the frozen
  taxonomy.
- Book II policy or Book VI capability semantics change the depth contract.

In each case: stop, record a GAP/ADR reference, do not amend this Bloc's
acceptance silently.
