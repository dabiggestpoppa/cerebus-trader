# IV.4 Q4 Fixtures

**Contract:** `ASK_GATEWAY_CONTRACT_V1`
**Base head:** `5ace8dfcd57f12996d168120ca74ee20e20e3f52`
**Scenarios:** 24 (`Q4-01`–`Q4-24`)

## Files

| File | Purpose |
|---|---|
| `_builders.py` | Builds every package through the frozen IV.3 `ContextPackager`, then binds a local routing policy, fake script, budget and expected gateway outcome |
| `generate.py` | Rewrites the 24 JSON fixtures and `FIXTURE_MANIFEST.json` with LF normalization |
| `Q4-01.json` … `Q4-24.json` | Deterministic fixture payloads: package, manifest, route, script, expected outcome and downstream expectation |
| `FIXTURE_MANIFEST.json` | SHA-256 and byte count for every fixture |
| `PROVENANCE.md` | Scenario-by-scenario source and boundary |

## Reproduction

```bash
python implementation/forge/book_iv/bloc_iv_4/fixtures/generate.py
```

`A-55` rebuilds the corpus in memory and verifies all 24 files byte-for-byte
against `FIXTURE_MANIFEST.json`.

## Boundary

A gateway `DRAFT` is always `UNVALIDATED`. It is not a factual answer, a
validated claim, an entitlement grant or execution permission. Scenarios that
preserve deliberate semantic defects (`Q4-07`, `Q4-11`–`Q4-16`) record the
downstream IV.5 rejection they require; the gateway itself only enforces schema,
package-local references, mandatory restrictions and forbidden authority fields.

No fixture contacts a provider, reads a market feed, writes canonical data or
contains a credential. No Q4 result closes F3 or F4.
