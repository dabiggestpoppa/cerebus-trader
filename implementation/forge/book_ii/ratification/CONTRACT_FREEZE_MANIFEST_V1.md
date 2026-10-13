# BOOK II CONTRACT FREEZE MANIFEST V1

Status: CANONICAL (Book II ratification, Build Agent #16)
Date: 2026-10-12
Ratification record: `RATIFICATION.md` (G-F7)
Frozen implementation head: `b44857ba800fcb7e76c2322345e1733703a92a3a`
(= `origin/forge` at ratification; the packet commits that follow are
documentation-only — no frozen surface changes after this head, enforced
by the hashes below).

Scope: **only the Book II contract surfaces** enumerated by the operator
authorization (45 application files across seven surfaces + 5 cross-bloc
invariant files = 50 frozen files) — service lifecycle, persistence and migrations,
identity/session, policy and exposure, provider ports, observability and
error contract, durable audit infrastructure, and the cross-bloc security
invariants. Book I authority and provenance boundaries are preserved: the
frozen Book I manifest (`../../book_i/bloc_i_5/BOOK_I_FREEZE_MANIFEST_V1.md`)
and all 23 planning-manifest-pinned files are untouched by this freeze.
Downstream implementation that does not yet exist (Book III market data,
Book IV adapters, Book VI entitlement/commerce, Book VII embedding
generation, Book VIII launch hardening) is **not frozen**.

Hash method: `sha256sum <path>` over the tracked file content at the frozen
head (Windows checkout with `core.autocrlf=true`; same reading as all prior
integrity checks — EOL-normalized comparisons were used for the planning
pins, raw hashes here bind the exact committed blobs as checked out).

## Surface 1 — Service lifecycle (9 files)

`app/forge/service/__init__.py` — `29dc73d4c683bb6acd95e913bd4fbe3ff8155e9ede32070d3ec70a1c3d2b5344`
`app/forge/service/container.py` — `4fd691e7105c13feab5bf20e77a0448fe9da41bc0cad4b274738efb7f2306087`
`app/forge/service/lifecycle.py` — `f45e31e960c4edaa9d6ddcb7ad3b0ac29014f35bd9e86580e02f673afbefcc11`
`app/forge/service/routes.py` — `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af`
`app/forge/service/health.py` — `eb0a2c7e8804d157584e01ce88fef5a25f8d4c35c1a52bc76fb6e04c840fe30c`
`app/forge/service/errors.py` — `1fa98f0d4fee026d18dc43eba3754c7a103b5e786ac87916c6424b1dd6f6ef27`
`app/forge/service/correlation.py` — `4717a44d4ad5be5cd82a34e3216edddef42948cc4ee245b728a90414a948073e`
`app/forge/service/policy_enforcement.py` — `9ccc3b72f77fca0cb3fd0685128fd96a2f0ce8ca975b532d96646d285476e381`
`app/forge/config.py` — `8bc4dd63d1c0c576374cb1e4eb4208e96cf37456b5c74dab37c3689e4c200548`

## Surface 2 — Persistence and migrations (10 files)

`app/forge/persistence/__init__.py` — `669db4eb3f6f36e2407b4a3ec42f773702bdd2b02af457f03fd3c541d9d9e21f`
`app/forge/persistence/port.py` — `f4385b9c97132eca78ad3a840465883e637615a75d753087cdf776280b888090`
`app/forge/persistence/records.py` — `3ace3ea2401a3b51275b85c13f2812420c49d05b3002be4f57b513b88a6a08a8`
`app/forge/persistence/memory.py` — `5d52647fe763044f4079326039777f94f0353b428334cb775061fde7ea116937`
`app/forge/persistence/sql/__init__.py` — `966334c74ff51b1ed87c468b73740b8fbad50ef4aae6122762530de2cc6f802e`
`app/forge/persistence/sql/gateway.py` — `4e5b3cfbedf6ce919b59cf620df0722ed2894a681c558d83697d86c7c1406d72`
`app/forge/persistence/sql/migrations.py` — `8d26bc026c47196e5713d4f3745b417e9580663bf3c12a473e8b99126d8339b9`
`app/forge/persistence/sql/001_initial_schema.sql` — `d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14`
`app/forge/persistence/sql/002_identity_session.sql` — `c575f91d3fcb572cdc3b7744cbd97ba3b116401816f75d8764035cb0deaa194d`
`app/forge/persistence/sql/003_vector_projection.sql` — `c3d51e372bdc333874032ebdb67ba9b4ebb9e972a0889bee74f72cf165ef3f21`

Migration head: **4** (`001_initial_schema`, `002_identity_session`,
`003_vector_projection` PG-only, `004_audit_ledger` portable);
compatibility `OK` under `FORGE_MIGRATION_COMPATIBILITY_REQUIRED=1`.
Migrations are forward-only and immutable once frozen; they never run as a
startup/import side effect (D3).

## Surface 3 — Identity and session (2 files)

`app/forge/identity.py` — `0223d7a2f5f3a9c7a9caa75384c433dc7ab03f1fd981bf1df5f5a665f80a2487`
`app/forge/service/authentication.py` — `70b22c598830303b655fcecded075f8650cacadf1cd37a5c982b1b7c11ff5a68`

(Schema backing in Surface 2, migration 002.) Laws frozen: IDENTITY ≠
ENTITLEMENT, AUTHENTICATION ≠ AUTHORIZATION, SESSION ≠ LICENSE,
PROVIDER ID ≠ FORGE ID.

## Surface 4 — Policy and exposure (1 file)

`app/forge/policy.py` — `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`

Policy version/hash of record: `POLICY_MODULE_SHA256` =
`f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`
(asserted executable by `tests/test_forge_retrieval.py`; byte-identical
since Bloc I.4). The enforcement seam `service/policy_enforcement.py` is
frozen in Surface 1 (authorize → then load; bounded content-free policy
audit; reason codes).

## Surface 5 — Provider ports (10 files)

`app/forge/providers/__init__.py` — `9e9650fee50a971aa6f76a7b2c13ff40aaa605847dc4d9e7c989f62768c9a0ed`
`app/forge/providers/llm.py` — `f556d318efc6a65ece3921ad526306fe34b70b7d3740063dffd40ded42a82cd5`
`app/forge/providers/commerce.py` — `1bce7dd147f00415d41c940996c2066e41cde7c1c66efa6ee47f39037fcf3539`
`app/forge/providers/notification.py` — `dcc993548fd1bf32ad92900e909e1e18d56d71752a9ad4edd7357ab171d2dc64`
`app/forge/providers/storage.py` — `851ce6f8caf166dbbfbc70070a0ea6907d082d5705ce8442c216da2628f16ff6`
`app/forge/providers/errors.py` — `1097eeb0018e76e3e22615ad809849393a3a1fb0f9a65d8bea4e854bf966040f`
`app/forge/providers/registry.py` — `cf7bc8bcc5950db4403e9672dc57d275688b5a9d2837deec105742bfb0388709`
`app/forge/providers/resilience.py` — `dd5615f4f47fd79bff6651a51f48f76c6e9f864f796470f9a376909f54a238a0`
`app/forge/providers/doctrine.py` — `bc12e874037bfa5dc143b261dd6325b11967f9b231f48de192b431d3a010c5cc`
`app/forge/providers/fakes.py` — `a93b89d2fb49e8cc7317c5d710900207fe49bb89f6f9f03f10fa7c802f358e73`

Frozen: 4 neutral ports, 8-element contract specs, 8-class failure
taxonomy, registry/factory (config-selected, frozen after composition),
per-port fallback modes. Only `fake` implementations exist; concrete
adapters (Book IV OpenRouter, Book VI Whop) are **not frozen** and may only
be added through the registry seam.

## Surface 6 — Observability and error contract (11 files)

`app/forge/observability/__init__.py` — `db17260d15629149c23a0e3f6a981f3d9b0878cdd1bdba4ba674bb40d9abaa1f`
`app/forge/observability/service.py` — `688d9052a73c7fb50500881031f678de2fd53ffa2335a0213b087bb6760f9966`
`app/forge/observability/correlation.py` — `3a2ef6691155cb672c6d972cb82ea1c489db095eb2fd5e1d20761ff1c846d3ab`
`app/forge/observability/events.py` — `43cdd7bd0e29c60c07516ca2ebf181c5e5faabea5b3a7e2f3607a2c4aa86e183`
`app/forge/observability/emitter.py` — `73699c482ca22570c6d164d033c16feec5c3bbc28885908ac0cd6cc67a9e4439`
`app/forge/observability/metrics.py` — `65c5d9ea2f10c7e20453a06e2131b98eb3dda0f4aeff29e202eee0e9bb6d0dfd`
`app/forge/observability/audit.py` — `61400bba2c567bb6cd6dae507e07e019f7e992c831e232ce033f3928c4bb4970`
`app/forge/observability/usage.py` — `cbec7cc4a14583c6cb2da2a61aeb0c8f9d0241fe340d20c4f491f6160da3a7dd`
`app/forge/observability/errors.py` — `cb37994fd88f5a7a143f84c95b1712fdfcecff11ef4cf5017d02f142492a9691`
`app/forge/observability/redaction.py` — `df2c5981757a8a73be20a8fd8acddcf2c411c794586d0862492d56fedf9e9a66`
`app/forge/observability/integration.py` — `77b96deebeac00155b4c0e4ef8b6745ce05c859e514582402a9a8f96c5c46652`

Frozen: correlation vocabulary with disclosed fallback, bounded structured
events (frozen field set, typed-event scrub), frozen metric names, four
audit streams (telemetry / security / usage / entitlement), 9-class error
taxonomy + `safe_error_response`, usage ledger. No vendor sinks; in-process
only; `required=False` always.

## Surface 7 — Durable audit infrastructure (2 files + seams)

`app/forge/persistence/sql/004_audit_ledger.sql` — `bac4b2f8a5b705221975bbcb9db2cdb4a03360547cc333080a70f4de7acb748e`
`app/forge/observability/audit_ledger.py` — `82da40e37a63713af26bb24b57e88f8b5908aa570cba5d4d3d4e5da4a14c46cc`

(Port seam `AuditEventPort`/`coerce_audit_event` lives inside
`persistence/port.py` — hashed in Surface 2; the II.6 durable mirrors live
inside `observability/service.py` — hashed in Surface 6. The composition
root in `app/main.py` is intentionally **outside** the frozen surface set:
it is deployment-scoped composition, and the container's `persistence`
seam remains deliberately unwired per D4.)

Frozen: `forge_audit_events` (append-only, content-minimized, seq PK +
UNIQUE `event_id` idempotency), bounded cache, redaction-before-storage,
`best_effort` fallback markers vs `require_durable` typed redacted failure,
durable mirrors across all six Ch II.2.6 record classes, no HTTP exposure,
no authority escalation (streams ⊆ frozen vocabulary; auth vocabulary
frozen; no entitlement state machine). Change control: retention/compaction
requires a future governed packet (D1); write-policy promotion is a
deployment config act (D2); enabling requires migration 004 applied and
verified first (D3).

## Surface 8 — Cross-bloc security invariants (5 files)

`implementation/forge/book_ii/cross_bloc/PLAN.md` — `8363ab6cbf58575d648b41dd0e20924db3187fff1712492b5ad2fb6392a0ec7c`
`implementation/forge/book_ii/cross_bloc/ACCEPTANCE.md` — `10183ab1dad08a0a10c75adc8dbc3dae398571c639f8778e89dfc4f83fbaf1f0`
`implementation/forge/book_ii/cross_bloc/EVIDENCE.md` — `81e652970976ae64961cb6368b77138acf5f8e53e13c34befe47a303d5ab26a2`
`implementation/forge/book_ii/cross_bloc/VERIFICATION.md` — `4d97da344559b3d3dbcd0c49c05e23b841b79f4f4e5eb594f39f648d98c2e836`
`tests/test_forge_cross_bloc.py` — `5db4f7fda9292f0af0169dd86fcc9d4625e47e44325cf23437ae93310ca50667`

Frozen: the X1–X9 / F1–F12 adversarial invariants and the executable laws
(deny ≡ missing, authorization precedes content access, no entitlement
state machine, no Book VI business table, import discipline, exposure
boundary). These tests must remain green; changing an invariant requires a
governed packet, never a silent edit.

## Enforcement

1. Any change to a frozen file after this head requires an explicit
   governed packet (GAP/ADR + plan versioning) under audit §12 change
   control — never a silent edit, never an amend of history.
2. Frozen-file integrity is re-checkable at any time by re-running
   `sha256sum` over the lists above and comparing.
3. Book I freeze authority (`BOOK_I_FREEZE_MANIFEST_V1.md`) and the
   planning freeze (23 pinned files, head `60e0675`) remain in force,
   unchanged and superior within their own scope.
