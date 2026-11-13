# HASH_PIN_AMENDMENT_V1

**BA-36 — Governed hash-pin reconciliation for the authorized BA-35 Rung 2 IV.2 source change.**
**Append-only record. No earlier evidence document is overwritten.**

## 1. Authorization

BA-35 Rung 2 authorized a single behavioural amendment to
`app/forge/ask_cerebus/retrieval/service.py`: the Book III market/snapshot
intelligence trigger was narrowed so that `HISTORICAL_RESEARCH` plans no
longer force an unrelated snapshot requirement. The source diff is the
intelligence-trigger predicate only.

Because `retrieval/service.py` is pinned by BA-33 hash guards and upstream
pins, the authorized change invalidates the recorded pre-amendment identity.
Per AGENTS.md Section 12 and BA-35 Section 12, the pin is **not silently
rebaselined**; it is updated here through a separately governed amendment,
with mutation detection preserved.

## 2. Source-diff verification

**File:** `app/forge/ask_cerebus/retrieval/service.py`, `AskCerebusRetrievalService.retrieve`.

**Before:**
```python
if plan.requires_live_intelligence or plan.time_scope.value in (
    "CURRENT", "AS_OF", "HISTORICAL_RESEARCH",
):
```

**After:**
```python
needs_intelligence = bool(
    plan.requires_live_intelligence
    or plan.time_scope.value in ("CURRENT", "AS_OF")
)
if needs_intelligence:
```

Verified properties:
- Removes the unnecessary snapshot requirement for historical documentation
  (`HISTORICAL_RESEARCH` no longer triggers Book III intelligence).
- Preserves `CURRENT` and `AS_OF` intelligence routing (genuine live-data
  requests still route to the snapshot provider).
- Preserves provider-dependent historical snapshot requests where
  `requires_live_intelligence` or `time_scope` is `CURRENT`/`AS_OF`.
- Does not widen Book II authorization; no new provider port or capability.
- Does not alter canonical Claim/Evidence source facts (Book I untouched).
- Does not turn unsupported statistics into answers (statistics still route
  through `requires_evidence` and refuse `INSUFFICIENT_EVIDENCE`).
- Does not allow historical models to become current actionable setups
  (status/generation/exposure restrictions unchanged; `SUPERSEDED` stays
  superseded).

H1–H3 re-executed: all three historical explanations reach
`VALIDATED_ANSWER` with zero `ERROR` (previously `TypeError`/`ERROR`).

## 3. Affected hash constants

| Guard (test) | Protected file | Hash kind | Original identity | Current identity | Pin action | Result |
|---|---|---|---|---|---|---|
| `test_x006_frozen_upstream_hashes_are_unchanged` | `app/forge/ask_cerebus/retrieval/service.py` | git blob SHA-1 (UPSTREAM_PINS) | `1b69cd5e578f264872de830dc0402413dc14e492` | `cdbe615ffd18dd0fa4df096d27259a405ac98964` | Update pin | PASS |
| `test_am1_r27_hash_guards_are_checkout_encoding_invariant` | `app/forge/ask_cerebus/retrieval/service.py` | SHA-256 canonical content (`_INLINE_GUARDED`) | `d4ef64f9d3f994b08c331b48a2e720aa345f92af02d8b32a2d0feb9707d5fd83` | `2d73737e1a20f61e3ff276f16dee31e8e880304a6473754224d8a5ceb67b3535` | Update constant | PASS |
| `test_c88_frozen_iv2_bundle_refs_trace_unchanged` | `app/forge/ask_cerebus/retrieval/service.py` | SHA-256 canonical content (inline) | `d4ef64f9d3f994b08c331b48a2e720aa345f92af02d8b32a2d0feb9707d5fd83` | `2d73737e1a20f61e3ff276f16dee31e8e880304a6473754224d8a5ceb67b3535` | Update constant | PASS |
| `test_only_authorized_frozen_files_changed` | `app/forge` worktree vs HEAD | `git diff --name-only HEAD -- app/forge` | clean | clean (both amended files committed together) | No change; assertion confirms clean worktree | PASS |

**Pin locations updated:**
- `app/forge/ask_cerebus/evaluation/versions.py` — `UPSTREAM_PINS["app/forge/ask_cerebus/retrieval/service.py"]` (git SHA-1).
- `tests/test_forge_ask_cerebus_evaluation_amendment1.py` — `_INLINE_GUARDED["app/forge/ask_cerebus/retrieval/service.py"]` (SHA-256).
- `tests/test_forge_ask_cerebus_context.py` — `test_c88` inline expected dict for `service.py` (SHA-256).

**No guard removed, weakened, or made to accept arbitrary hashes. No unrelated constant changed.**

## 4. Mutation and restoration checks

| Check | Method | Result |
|---|---|---|
| Current authorized source passes | `test_x006`, `test_am1_r27`, `test_c88` on committed head | PASS |
| One-byte unauthorized mutation fails | Appended a comment line to `retrieval/service.py`; `test_x006` | FAILS (guard detects drift) |
| Restoring the file passes | `git checkout` of original bytes; `test_x006` | PASS |
| LF / CRLF canonical invariance | `canonical_sha256` normalizes CRLF→LF; both encodings yield `2d73737e…` | PASS |
| Unrelated frozen files retain previous hashes | All other 16 BA-33 guards unchanged and green | PASS |

## 5. Identity values

**Git blob SHA-1** (`git rev-parse HEAD:…/retrieval/service.py`):
- Pre-amendment (`dc3a5e7`): `1b69cd5e578f264872de830dc0402413dc14e492`
- Post-amendment (BA-35 Rung 2 head): `cdbe615ffd18dd0fa4df096d27259a405ac98964`

**Canonical SHA-256** (`canonical_sha256`, CRLF→LF normalized):
- Pre-amendment: `d4ef64f9d3f994b08c331b48a2e720aa345f92af02d8b32a2d0feb9707d5fd83`
- Post-amendment: `2d73737e1a20f61e3ff276f16dee31e8e880304a6473754224d8a5ceb67b3535`

The two identities are kept strictly apart per `tests/_support/canonical_bytes.py`: the git blob SHA-1 is the committed object identity; the SHA-256 is the checkout-independent content identity. `test_am1_r27` step 5 asserts they are distinct for non-content-identical files and that the sanctioned bridge holds for committed-as-is content.

## 6. Scope

- Only `retrieval/service.py` pins are rebaselined.
- No hash guard removed or weakened.
- `canonical_bytes` helper (`tests/_support/canonical_bytes.py`) unchanged.
- SQL migrations, routes, `.gitattributes`, Book I/II/III product code unchanged.
- No provider configuration or entitlement change.
