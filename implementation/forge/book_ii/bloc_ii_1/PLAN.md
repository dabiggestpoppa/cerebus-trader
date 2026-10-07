# BOOK II / BLOC II.1 — SERVICE SKELETON — PLAN.md

Status: PLAN
Date: 2026-10-07
Freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24
Previous ratified HEAD: 5ce3246e5ba661db21fa8856ef66073397cecaba

---

## Scope

Book II / Bloc II.1 — Service Skeleton & Runtime Contract, translated to the **actual** repository.

## Inputs

- planning/forge/books/BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md
- planning/forge/PLANNING_FREEZE_MANIFEST_V1.md
- app/main.py (existing FastAPI application — CEREBUS Signal Guard)
- app/forge/canonical.py
- app/forge/schemas.py
- app/forge/provenance.py
- app/config.py
- requirements.txt
- Dockerfile
- frozen Book II Bloc II.1 acceptance criteria (application boots, health/readiness semantics, test runtime requires no paid/external provider, provider code cannot contaminate domain imports, migration compatibility is checked before readiness)

## Actual repository reality

- One existing FastAPI application: `app.main:app`, titled "CEREBUS Signal Guard", currently serving `/webhook`, `/health`, `/state`, `/reconcile`, `/logs`, `/screenshot`.
- Existing config is `app/config.py` with module-level `WEBHOOK_SECRET`, `ENVIRONMENT`, `USE_MCP_VISION`, `TRADINGVIEW_MCP_DIR`, `MCP_TIMEOUT_SECONDS` loaded from `.env` + `configs/strategy_rules.yaml`.
- Existing test suite is 130 tests: Signal Guard domain tests (`test_state_engine.py`, `test_flip_logic.py`, `test_duplicate_signal.py`, `test_ghost_signal.py`, `test_vision_confirm.py`, `test_vision_mcp.py`) plus FORGE I.1/I.2 tests (`test_forge_canonical.py`, `test_forge_schemas.py`, `test_forge_provenance.py`).
- FORGE domain already has `app/forge/` with `canonical.py`, `schemas.py`, `provenance.py`. None of these modules import FastAPI today — that must remain true.
- There is no existing `app/forge/service/` package. We create the smallest sensible service container here.

## II.1 local decisions

1. **Service namespace/version boundary.**
   FORGE routes live under `/forge/v1` as a FORGE-owned namespace, chosen here because:
   - the existing Signal Guard app has no `/forge` footprint;
   - the frozen plan says "explicit namespace/version boundary," and V1 is the current frozen implicit version;
   - this keeps FORGE visible and isolated rather than sprinkling routes among Signal Guard paths.

2. **Application composition.**
   - FORGE is composed into the existing `app.main:app` via an explicit `FastAPI.include_router(...)` call in the existing `app/main.py`.
   - No second FastAPI app is created.
   - No monkeypatching.
   - FORGE lifecycle is registered by appending `ForgeLifecycle.startup`/`shutdown` to `app.router.on_startup`/`on_shutdown` in the composition root, because sub-router `on_event` handlers never fire once a router is included. The existing Signal Guard startup handler is not modified.

3. **Domain/service separation.**
   - `app/forge/canonical.py`, `schemas.py`, `provenance.py` remain pure domain.
   - New FORGE service layer lives under `app/forge/service/` and imports from `app.forge.*`.
   - Domain must not import anything transport-level.

4. **Configuration boundary.**
   - Introduce `app/forge/config.py` as the FORGE configuration boundary.
   - It wraps/augments the existing app config without replacing it.
   - It exposes a typed `ForgeConfig` with safe defaults for LOCAL/TEST.
   - It redacts secrets in its diagnostic representation.
   - No provider configuration beyond what II.1 needs (none).

5. **Health/readiness/liveness.**
   - Keep existing `/health` as a Signal Guard endpoint untouched.
   - Add FORGE `/forge/v1/health` returning a FORGE-owned health object with `service`, `version`, `environment`, `status`, and an optional `dependencies` structure.
   - FORGE liveness/readiness at this stage only reports on FORGE-owned dependencies, which at II.1 is **none**.
   - FORGE readiness explicitly does NOT claim Postgres/Whop/OpenRouter/market-data readiness.

6. **Build/version identity.**
   - Expose `/forge/v1/meta` with deterministic, non-secret metadata:
     - service name
     - api_version
     - application_version (from the existing app where applicable; else a FORGE-local default)
     - environment
     - forge_domain_version (FORGE domain package identity)
   - No env dump, no secret, no corpus path.

7. **Service container / DI boundary.**
   - Introduce `app/forge/service/container.py` as the smallest explicit composition boundary.
   - It provides the FORGE services needed by the FORGE router: health/metadata services and later canonical/provenance/policy/persistence/provider-port access.
   - At II.1 this is intentionally minimal: mostly a marker boundary plus a real `ForgeServiceContainer` that can be replaced/faked in tests.
   - Domain modules remain multi-instance-safe and free of global mutable singletons used by the HTTP layer.

8. **Error envelope.**
   - FORGE introduces a small FORGE error envelope helper in `app/forge/service/errors.py`.
   - FORGE-owned endpoints wrap unexpected exceptions into a safe JSON body: `code`, `message`, `request_id` only.
   - FORGE does not rewrite Signal Guard error behavior.

9. **Request correlation.**
   - II.1 introduces a minimal correlation boundary: FORGE router reads/generates a bounded request id header `X-Request-Id` (regex-limited) and returns it in FORGE responses.
   - It does not trust arbitrary unbounded user input.
   - It does not attempt to retrofit correlation into the existing Signal Guard routes.

10. **Logging boundary.**
    - FORGE uses standard Python logging under a `forge` logger name.
    - FORGE logs no secrets, no env dump, no raw provider payload.
    - FORGE logs startup identity deterministically.

11. **Lifecycle.**
    - No network provider is contacted during import.
    - No future provider is contacted during startup.
    - No persistence is required to start FORGE in LOCAL/TEST.
    - Explicit startup/shutdown hooks are introduced in `app/forge/service/lifecycle.py` but II.1 does not require DB/provider connections yet.

12. **Provider-port placeholders.**
    - II.1 does **not** implement OpenRouter/Whop/market-data ports.
    - The frozen Book II plan defines provider ports in Bloc II.5. No port interfaces are required to prove any II.1 acceptance clause (domain isolation is proven by AST import checks, which need no port stubs).
    - Local decision: **defer the ports package entirely to II.5.** No `app/forge/service/ports/` placeholder is created in II.1; the container exposes a `providers` seam that stays `None` and rejects wiring until II.5.

13. **Signal Guard isolation.**
    - All existing Signal Guard routes and behavior are preserved.
    - FORGE adds routes under `/forge/v1`.
    - FORGE imports must not change Signal Guard runtime behavior or import side effects.

14. **Explicit non-goals.**
    - No persistence, no Postgres, no pgvector, no migrations.
    - No identity/session/authorization.
    - No policy engine.
    - No provider adapters.
    - No corpus/routing/data APIs.
    - No I.3 backfill.

15. **Security implications.**
    - No secrets endpoint.
    - No debug stack-trace route.
    - No corpus/file-serving route.
    - No internal method/code exposure route.
    - No arbitrary-object-by-ID route.
    - FORGE router must not accidentally become a wildcard file server.

## II.2 handoff boundary

- II.1 leaves FORGE at: domain + service container boundary + FORGE router + configuration boundary + basic observability/correlation hooks.
- II.2 will add persistence + migration runner and wire readiness to actual DB migration compatibility.

## Acceptance checklist mapping

See `ACCEPTANCE.md`. This plan is the source-of-truth mapping from Book II / Bloc II.1 frozen chapters to the actual repo implementation.
