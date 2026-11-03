# Bloc III.4 — Deterministic Golden Fixtures

`BLOC_III_4.*.V1` — committed contract-test inputs for the CEREBUS State,
Path & Transition Engine acceptance suite
(`tests/test_forge_state_engine.py`, clauses T1–T12 of the frozen
`ACCEPTANCE.md`).

`_builders.py` builds the synthetic inputs **and** the suite reproduces
them with the same module, so a fixture can never drift from its
reproduction. `generate_fixtures.py` writes every JSON file and the
LF-normalized manifest.

## Inventory

| File | Fixture id | Contents |
|------|-----------|----------|
| `state_snapshots.json` | `BLOC_III_4.STATE_SNAPSHOTS.V1` | One finalized genesis snapshot per family: model key, layer, active state, snapshot hash, source output hash, authorization classification, quality state, empty claim refs |
| `transition_vocabulary_cases.json` | `BLOC_III_4.TRANSITION_VOCABULARY.V1` | The exact twelve transition kinds and every family's allowed / restricted / unresolved sets |
| `first_delivery_cases.json` | `BLOC_III_4.FIRST_DELIVERY.V1` | Ordered delivery AB, the reversed BA pair (same terminal both-side reach), the same-bar ambiguous case, and per-case path hashes |
| `failure_repair_cases.json` | `BLOC_III_4.FAILURE_REPAIR.V1` | Declared chains (accept → fail → repair → compress → release), repair-without-failure refusal, failure-without-acceptance refusal, the golden EUR chain, and the distinct failure states |
| `rekey_cases.json` | `BLOC_III_4.REKEY.V1` | The five-step EUR Daily ladder, the touch-only refusal, and the XAU 132 → 168 forbidden pair |
| `layer_handoff_cases.json` | `BLOC_III_4.LAYER_HANDOFF.V1` | L3→L2 and L2→L1 ownership, the L1→L3 ownership violation and the L3→L1 direction refusal |
| `range_left_cases.json` | `BLOC_III_4.RANGE_LEFT.V1` | Conditioned remaining distribution, explicit unresolved, and the unconditional-frequency refusal |
| `stand_down_cases.json` | `BLOC_III_4.STAND_DOWN.V1` | The frozen III.3 no-go vocabulary mapped onto bounded stand-down states with the eligibility lock |
| `transition_history_cases.json` | `BLOC_III_4.TRANSITION_HISTORY.V1` | The ordered EUR ledger (deliver → rekey → stand down), per-event hashes, chain hashes and retained negative evidence |
| `path_invariants_cases.json` | `BLOC_III_4.PATH_INVARIANTS.V1` | The same-terminal / different-path pair with both path hashes |
| `model_family_transition_authority.json` | `BLOC_III_4.FAMILY_AUTHORITY.V1` | The full seven-family matrix: states, canonical sources, allowed / restricted / unresolved / never, canonical-only targets, forbidden pairs, engine codes |
| `replay_hashes.json` | `BLOC_III_4.REPLAY_HASHES.V1` | Per-family snapshot hashes plus the ledger history and event hashes |
| `FIXTURE_MANIFEST.json` | — | sha256 of every JSON fixture except the manifest itself |

## Provenance honesty

Every fixture is labelled and stays inside its class:

* **`SYNTHETIC_FIXTURE`** — all model outputs, snapshots, events, targets
  and bar references are deterministic generated values. They are
  *structural validation material only*: never empirical market evidence
  and never citable for a performance claim (PLAN §10.3; ACCEPTANCE §P).
* **`CANONICAL_SOURCE_SLICE`** — the twelve-kind vocabulary, the family
  authority matrix, the EUR Daily rekey ladder, the declared
  failure/repair grammars, the stand-down mapping and the canonical
  evidence ids enter only through the ratified III.2/III.3 registries and
  frozen model cards, quoted verbatim.
* **`replay_hashes.json`** — reproduction of these hashes is
  *determinism evidence* (clause T9/K7), never empirical performance
  evidence.

A fixture never carries a win rate, expectancy, probability or profit
figure; the suite asserts that (`test_no_performance_claims_from_fixtures`).

## Determinism and regeneration

```bash
python implementation/forge/book_iii/bloc_iii_4/fixtures/generate_fixtures.py
```

Writes LF-normalized JSON (`sort_keys`, two-space indent, UTF-8) and
recomputes the manifest. Hashes are recorded over LF-normalized content,
so the manifest verifies identically on this Windows `core.autocrlf=true`
checkout and on the Linux CI checkout. Regeneration is idempotent: an
unchanged engine produces byte-identical fixtures.
