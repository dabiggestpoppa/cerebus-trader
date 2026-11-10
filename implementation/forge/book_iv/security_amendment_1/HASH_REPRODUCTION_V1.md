# Hash canonicalization — reproduction V1

Two isolated checkouts of head `3ad0b2e88a6759ddfb6610746a790551fc27e2c7` were
executed on the same host. They differ **only** in checkout encoding.

| | Environment A (LF) | Environment B (CRLF) |
|---|---|---|
| Path | temp clone `/tmp/lfenv` | working repository |
| `core.autocrlf` | `false` | `true` |
| `app/forge/service/routes.py` bytes | 0 CRLF, 194 LF | 194 CRLF, 194 LF |
| `tests/test_forge_ask_cerebus_answer.py` bytes | 0 CRLF | CRLF |
| Host runtime | native Windows, CPython 3.11 | native Windows, CPython 3.11 |
| Commit | `3ad0b2e` | `3ad0b2e` |

Both environments are **native Windows runtimes**; the difference under test is
the working-tree encoding. No Linux, WSL or macOS runtime was executed in this
rung — Linux coverage comes from the CI jobs recorded in `HASH_RATIFICATION_V1.md`
and is reported separately, not as a local result.

## 1. Guard results

| Suite | A (LF) | B (CRLF) |
|---|---|---|
| The 17 historical guards | **17 passed** | **17 passed** |
| Helper acceptance (`test_canonical_bytes.py`) | **24 passed** | **24 passed** |
| AM1-R01–R24 (`test_forge_ask_cerebus_amendment1.py`) | **24 passed** | **24 passed** |
| AM1-R25/R26/R27 (`test_forge_ask_cerebus_evaluation_amendment1.py`) | **3 passed** | **3 passed** |

Before the repair, Environment B produced **15 failed / 2 passing-of-the-17**
guards plus `test_wp3b_contract_suite_green` failing as a consequence — the
documented 17-failure inventory. Environment A produced 17 passing then as well,
which is exactly the asymmetry the defect was.

## 2. Book regression

| Suite | A (LF) | B (CRLF) |
|---|---|---|
| Book I retrieval | 72 passed | 72 passed |
| IV.1 interpreter | 60 passed | 60 passed |
| IV.3 context | 93 passed | 93 passed |
| IV.4 gateway | 72 passed | 72 passed |
| IV.5 answer | 86 passed | 86 passed |
| IV.6 evaluation | 112 passed | 112 passed |
| Book III integration | 96 passed | 96 passed |
| **Full repository** | **2624 passed, 0 failed, 29 skipped** | **2624 passed, 0 failed, 29 skipped** |

Baseline for comparison on this host before BA-33:
`2582 passed, 17 failed, 29 skipped`. The delta is exactly +17 repaired guards,
+24 helper drivers and +1 R27 driver = 2624.

## 3. Mutation checks

Executed in both environments by `mutation.py`, which mutates one governed byte,
runs the guard, restores the original bytes and confirms the digest and the
guard result return to passing. Nothing was committed.

| Mutation | A (LF) | B (CRLF) |
|---|---|---|
| one byte changed in `app/forge/service/routes.py` | guard fails | guard fails |
| … restored | guard passes | guard passes |
| one byte changed in `persistence/sql/001_initial_schema.sql` | guard fails | guard fails |
| … restored | guard passes | guard passes |
| one byte changed in `market_data/bars.py` | guard fails | guard fails |
| … restored | guard passes | guard passes |
| `app/forge/policy.py` removed from the tree | guard fails | guard fails |
| … restored | guard passes | guard passes |

`git status --porcelain` was empty after the CRLF run, so no mutation survived.

## 4. Encoding-invariance evidence beyond the guards

AM1-R27 does not rely on the two checkout results alone. For every one of the 65
governed files it also proves, in-process:

- `sha256(canonical_bytes(file)) == recorded constant`;
- `canonical_bytes(CRLF version) == canonical_bytes(LF version)`, using a
  synthetic opposite-encoding copy of the file's own bytes;
- `sha256(raw CRLF bytes) != constant` for every file that contains newlines —
  i.e. the historical failure is real and the repair, not the fixture, is what
  removed it;
- a one-byte alteration of the canonical content changes the digest;
- `committed_blob_id(routes.py) == canonical_git_blob_sha1(routes.py)` while
  `canonical_sha256(routes.py) != committed_blob_id(routes.py)`.

That is the same proof under either checkout, so it holds for encodings this host
cannot materialise directly.

## 5. Environmental limitations

1. Both local environments are Windows; the LF result is an LF *checkout* on a
   Windows runtime, not a Linux run. Linux is covered only by CI.
2. The repository's `.gitattributes` was not touched; the checkout policy that
   produced these two environments is the existing one.
3. Only four mutation targets were exercised end-to-end; every governed file is
   instead covered by the in-process one-byte mutation in AM1-R27.
4. `test_wp3b_contract_suite_green` shells out to a nested pytest run; it is
   slow but deterministic and passed in both environments.
