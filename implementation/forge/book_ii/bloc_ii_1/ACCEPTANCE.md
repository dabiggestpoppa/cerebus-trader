# BOOK II / BLOC II.1 — SERVICE SKELETON — ACCEPTANCE.md

Status: ACCEPTANCE
Date: 2026-10-07
Freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24
Previous ratified HEAD: 5ce3246e5ba661db21fa8856ef66073397cecaba

---

## A. APPLICATION COMPOSITION

A1. Existing Signal Guard application behavior remains available.
- Acceptance: `app/main.py` still exposes the existing Signal Guard routes and behavior under test client.
- Test: existing Signal Guard tests plus a focused composition test against `app.main:app`.

A2. FORGE service routes/components are composed intentionally rather than by monkeypatch/import side effects.
- Acceptance: FORGE routes appear on `app.main:app` only because `app/main.py` explicitly includes a FORGE router.
- Test: verify FORGE router metadata/source is included by `app/main.py`.

A3. Importing FORGE domain modules does not start the HTTP server.
- Acceptance: importing `app.forge.canonical`, `app.forge.schemas`, `app.forge.provenance` does not start uvicorn/serve, does not bind a socket, and does not run a live event loop serving HTTP.
- Test: import-time assertion under pytest.

A4. HTTP/service modules may depend on FORGE domain modules.
- Acceptance: FORGE service code imports from `app.forge.*`.
- Test: import graph assertion.

A5. FORGE domain modules must NOT depend on FastAPI.
- Acceptance: `app/forge/canonical.py`, `schemas.py`, `provenance.py` do not import `fastapi`.
- Test: AST-based import isolation assertion.

A6. No circular imports.
- Acceptance: FORGE package imports cleanly top-down.
- Test: import smoke test.

## B. FORGE SERVICE NAMESPACE

B1. FORGE endpoints live under an explicit namespace/version boundary.
- Acceptance: FORGE routes are under `/forge/v1`.
- Test: route-path assertions against test client.

B2. FORGE does not rename domain objects merely to fit route naming.
- Acceptance: routes reference domain concepts through service/adapter terms, not through renamed kernel objects.
- Test: code review + route naming assertion.

## C. HEALTH

C1. Provide a lightweight liveness endpoint.
- Acceptance: `GET /forge/v1/health` returns HTTP 200 with a FORGE-owned health object.
- Test: focused test.

C2. Liveness answers “is the FORGE service process/application alive?” only.
- Acceptance: health payload contains only FORGE-owned fields.
- Test: payload shape assertion.

C3. Liveness does not falsely imply database/provider/corpus/market-data/Ask CEREBUS readiness.
- Acceptance: FORGE health object contains no `dependencies.postgres.ready = true`, no `providers.openrouter`, no `providers.whop`, no `market_data`, no `ask_cerebus` claimed ready.
- Test: absence/negative assertion.

## D. READINESS

D1. If Book II requires readiness in II.1, implement readiness with honest dependency semantics.
- Acceptance: `GET /forge/v1/ready` exists and reports readiness only against FORGE-owned dependencies that exist at II.1.
- Test: readiness payload assertion.

D2. At this stage readiness may only evaluate dependencies that actually exist.
- Acceptance: readiness does not reference non-existent DB/provider dependencies as healthy.
- Test: absence assertion.

D3. If future dependencies are represented, mark them NOT_CONFIGURED / NOT_APPLICABLE / NOT_IMPLEMENTED rather than HEALTHY.
- Acceptance: any placeholder dependency field is explicitly non-healthy.
- Test: value assertion.

## E. BUILD / VERSION IDENTITY

E1. Service metadata must expose enough identity to distinguish application/service, API version, build/version identity where configured, environment where safe.
- Acceptance: `GET /forge/v1/meta` returns deterministic non-secret identity fields.
- Test: payload shape + deterministic-value assertions.

E2. Do not expose secrets, internal corpus paths, credentials, raw environment dumps, internal method content.
- Acceptance: metadata payload excludes any env var values, secret-like strings, corpus paths, code.
- Test: absence assertions.

## F. CONFIGURATION

F1. Introduce or formalize a typed FORGE configuration boundary if required.
- Acceptance: `app/forge/config.py` exists and exposes a typed FORGE config with safe defaults.
- Test: config construction + defaults.

F2. Configuration must have safe defaults for local/test where appropriate.
- Acceptance: FORGE starts under test client with no special env for II.1 scope.
- Test: default-configuration boot test.

F3. Configuration must fail clearly on malformed required values.
- Acceptance: malformed FORGE config raises clearly, not silently.
- Test: invalid-config test.

F4. Configuration must not read secrets into response payloads.
- Acceptance: no endpoint returns secret values.
- Test: absence assertion.

F5. Configuration must not require future providers for II.1 startup.
- Acceptance: no provider env required to boot FORGE under test client.
- Test: provider-absent boot test.

F6. Configuration must be testable without mutating global process state unpredictably.
- Acceptance: FORGE config can be constructed/faked for tests without hidden global side effects where feasible.
- Test: isolated config test.

## G. SERVICE CONTAINER / DEPENDENCY BOUNDARY

G1. Create the smallest boundary necessary for future services.
- Acceptance: `app/forge/service/container.py` exists and defines a replaceable FORGE service container boundary.
- Test: container construction/replacement test.

G2. It must allow later Books/Blocs to provide canonical registry access, provenance access, persistence, policy, provider adapters without converting domain modules into global mutable singletons.
- Acceptance: domain modules remain free of service-layer singletons; container is the composition root seam.
- Test: import/graph assertion + container replaceability test.

G3. Do NOT implement future services unless II.1 actually requires the current in-memory kernel for a route.
- Acceptance: II.1 routes do not depend on unimplemented persistence/policy/provider services.
- Test: route dependency assertion.

## H. ERROR CONTRACT

H1. HTTP errors owned by FORGE should have a deterministic safe envelope.
- Acceptance: FORGE uses a consistent FORGE error shape for FORGE-owned failures.
- Test: error response shape.

H2. Do not leak stack traces, secrets, internal paths, raw provider payloads.
- Acceptance: FORGE responses exclude those.
- Test: absence assertions.

H3. Differentiate at least client/input error, not found where applicable, internal service failure.
- Acceptance: FORGE distinguishes at least those categories.
- Test: status code + body assertions.

H4. Do not rewrite unrelated Signal Guard error behavior merely for consistency.
- Acceptance: existing Signal Guard error behavior preserved.
- Test: regression test.

## I. OBSERVABILITY

I1. Establish the minimum service observability boundary required by Book II.
- Acceptance: FORGE uses a `forge` logger and logs startup identity deterministically.
- Test: logging boundary test / review.

I2. No secret logging.
- Acceptance: FORGE logs contain no secrets.
- Test: review + absence assertion.

I3. Service startup identity logged.
- Acceptance: startup log line includes FORGE service identity/version.
- Test: capture/log assertion.

I4. If request IDs/correlation IDs are implemented:
- accept safe inbound IDs only under a bounded format OR generate one;
- return the effective ID;
- do not trust arbitrary unbounded user input.
- Acceptance: FORGE request-id behavior satisfies that.
- Test: request-id tests (valid inbound, invalid inbound ignored/ignored safely, generated when absent).

I5. Do not add an observability vendor.
- Acceptance: no vendor SDK added.
- Test: dependency review.

## J. LIFECYCLE

J1. Startup/shutdown behavior must be explicit and testable.
- Acceptance: FORGE lifecycle hooks exist and are testable.
- Test: lifecycle tests.

J2. No network provider should be contacted during import.
- Acceptance: importing FORGE modules does not perform network I/O.
- Test: import-time network absence (review + no network-using imports).

J3. No future provider should be contacted during startup.
- Acceptance: FORGE startup does not contact LLM/commerce/market-data providers.
- Test: startup behavior review + test.

J4. No persistence should be required.
- Acceptance: FORGE boots without DB.
- Test: boot-without-DB test.

## K. SECURITY

For each, acceptance = explicit verification in tests/review.

K1. No secret dump endpoint.
K2. No debug stack trace response in normal service behavior.
K3. No corpus exposure endpoint.
K4. No INTERNAL_METHOD/INTERNAL_CODE exposure route.
K5. No permissive "return arbitrary object by ID" route.
K6. No provider credentials in metadata.
K7. No wildcard behavior accidentally turning the service into a raw file server.

## L. REGRESSION

L1. All I.1 tests remain green.
L2. All I.2 tests remain green.
L3. Existing Signal Guard tests remain green.
L4. Full suite remains green.
L5. No existing test may be weakened/deleted simply to accommodate II.1.

## Non-goals (explicit)

- II.1 does NOT create persistence.
- II.1 does NOT implement identity/session/policy/provider adapters.
- II.1 does NOT expose canonical/evidence/setup/artifact/provenance/corpus routes.
- II.1 does NOT begin I.3 or II.2.

## Security/boundary review record

See `EVIDENCE.md`. This file defines the acceptance; evidence records the executed review.
