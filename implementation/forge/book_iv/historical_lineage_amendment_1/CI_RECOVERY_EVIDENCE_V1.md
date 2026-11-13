# CI_RECOVERY_EVIDENCE_V1

**BA-36 — CI recovery and final acceptance evidence.**
**Append-only record.**

## 1. Original CI failure inventory

Final-head workflow run `43240708557` (BA-35 Rung 2 head `99a5bfa`):

- `test` job: FAILURE
- `postgres` job: FAILURE

Local regression at `99a5bfa`: **2,692 passed / 4 failed / 29 skipped**.

The four local failures (all attributable to the authorized BA-35 Rung 2
`retrieval/service.py` behavioural change invalidating its recorded hash
pins):

| # | Failing test | Protected file | Failure reason |
|---|---|---|---|
| 1 | `test_x006_frozen_upstream_hashes_are_unchanged` | `app/forge/ask_cerebus/retrieval/service.py` | UPSTREAM_PINS expected git blob `1b69cd5e…`; amended file is `cdbe615…` |
| 2 | `test_am1_r27_hash_guards_are_checkout_encoding_invariant` | `app/forge/ask_cerebus/retrieval/service.py` | `_INLINE_GUARDED` expected SHA-256 `d4ef64f9…`; amended file is `2d73737e…` |
| 3 | `test_c88_frozen_iv2_bundle_refs_trace_unchanged` | `app/forge/ask_cerebus/retrieval/service.py` | Inline expected SHA-256 `d4ef64f9…`; amended file is `2d73737e…` |
| 4 | `test_only_authorized_frozen_files_changed` | `app/forge` worktree | `git diff HEAD -- app/forge` was non-empty (uncommitted `versions.py` pin update) |

These are hash-guard conflicts on the **authorized** IV.2 source diff, not
behavioural regressions. Every behavioural test passed.

## 2. Repairs applied (governed hash-pin reconciliation)

| Repair | File | Nature |
|---|---|---|
| Rebaseline `retrieval/service.py` pin | `app/forge/ask_cerebus/evaluation/versions.py` | `UPSTREAM_PINS` git SHA-1 `1b69cd5e…` → `cdbe615…` |
| Rebaseline `retrieval/service.py` pin | `tests/test_forge_ask_cerebus_evaluation_amendment1.py` | `_INLINE_GUARDED` SHA-256 `d4ef64f9…` → `2d73737e…` |
| Rebaseline `retrieval/service.py` pin | `tests/test_forge_ask_cerebus_context.py` | `test_c88` inline SHA-256 `d4ef64f9…` → `2d73737e…` |
| Confirm clean worktree | `tests/test_forge_market_data_provider_compatibility.py` | `test_only_authorized` asserts `git diff HEAD -- app/forge` is empty once both amended files are committed together |

No guard removed, weakened, or made to accept arbitrary hashes.

## 3. Mutation test (guard integrity preserved)

| Check | Result |
|---|---|
| Current authorized source passes all 4 guards | PASS |
| One-byte unauthorized mutation of `retrieval/service.py` fails `test_x006` | FAILS (guard detects drift) |
| Restoring the file passes `test_x006` | PASS |
| LF / CRLF canonical measurements agree (`2d73737e…`) | PASS |
| Unrelated frozen files retain previous hashes (all other BA-33 guards green) | PASS |

## 4. F-07a acceptance reconciliation

15 requirements (A01–A15) → 15 drivers, all PASS. See
`F07A_ACCEPTANCE_RECONCILIATION_V1.md`. Option C ratified with zero payload
change.

## 5. Local regression after repair

**Before repair:** 2,692 passed / 4 failed / 29 skipped (4 hash-guard conflicts).

**After repair (working tree, all amendments committed):**
- `test_x006`, `test_am1_r27`, `test_c88`, `test_only_authorized`: PASS
- F-09 drivers (R01–R28): 28/28 PASS
- F-07a drivers (A01–A15): 15/15 PASS
- EV-155–EV-178 corpus: 24/24 cases governed-correct

Full repository suite re-run: **0 failed** (behavioural); the 4 hash-guard
conflicts resolved by the governed pin update.

## 6. Remaining limitations

- The hosted `postgres` CI job could not be executed from this local
  environment; only the local `test` suite was re-run. Final-head CI on
  GitHub Actions (both `test` and `postgres`) must be allowed to conclude
  after the final push.
- `test_x003` (dataset digest stable across processes) and `test_x009`
  (requirements/drivers bidirectional mapping) include the updated driver
  count (`DRIVER_COUNT == 112`) and remain consistent with
  `implementation/forge/book_iv/bloc_iv_6/ACCEPTANCE.md`.
- Production readiness (BG-C) remains BLOCKED; EV-GATE-01–13 remain OPEN;
  no launch decision is inferred from a green deterministic corpus.

## 7. Files changed in this amendment

- `app/forge/ask_cerebus/evaluation/versions.py` — pin rebase (committed)
- `tests/test_forge_ask_cerebus_evaluation_amendment1.py` — `_INLINE_GUARDED` rebase
- `tests/test_forge_ask_cerebus_context.py` — `test_c88` rebase
- `tests/test_forge_market_data_provider_compatibility.py` — `test_only_authorized` worktree assertion
- `tests/test_forge_ask_cerebus_f07a.py` — split A01/A05 into A01 + A05 (15 drivers)
- New docs: `HASH_PIN_AMENDMENT_V1.md`, `F07A_ACCEPTANCE_RECONCILIATION_V1.md`, `CI_RECOVERY_EVIDENCE_V1.md` (this document), `RATIFICATION_SUPPLEMENT_V2.md`
