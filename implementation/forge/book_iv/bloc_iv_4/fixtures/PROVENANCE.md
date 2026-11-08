# IV.4 Q4 Fixture Provenance

**Base head:** `5ace8dfcd57f12996d168120ca74ee20e20e3f52`
**Contract:** `ASK_GATEWAY_CONTRACT_V1`
**Count:** 24 deterministic synthetic scenarios

## Source law

Every package is built through the frozen IV.3 `ContextPackager` using the
IV.3 fixture builders. No fixture calls a provider, reads a market feed, writes
canonical data or contains a real credential.

The provider scripts are synthetic deterministic fakes. A scripted bad draft is
not sanitized into a good draft: it is admitted only where the gateway contract
permits an unvalidated representation, and its downstream expectation records
what IV.5 must reject.

## Q4 map

| ID | Depth | Expected gateway result | Attempts | Downstream expectation |
|---|---|---|---:|---|
| Q4-01 | BEGINNER | DRAFT — beginner definition | 1 | VALID |
| Q4-02 | OPERATOR | DRAFT — setup with mandatory no-go | 1 | VALID |
| Q4-03 | RESEARCHER | DRAFT — evidence/method summary | 1 | VALID |
| Q4-04 | BEGINNER | DRAFT — general knowledge; no CEREBUS claim | 1 | VALID |
| Q4-05 | OPERATOR | DRAFT — package-local citations and numeric link | 1 | VALID |
| Q4-06 | OPERATOR | REFUSED `NUMERIC_EVIDENCE_MISSING` | 1 | NUMERIC_EVIDENCE_MISSING |
| Q4-07 | RESEARCHER | DRAFT with altered number link | 1 | NUMERIC_MISMATCH |
| Q4-08 | OPERATOR | REFUSED `NUMERIC_EVIDENCE_MISSING` | 1 | NUMERIC_EVIDENCE_MISSING |
| Q4-09 | RESEARCHER | REFUSED `CITATION_REQUIRED` | 1 | CITATION_REQUIRED |
| Q4-10 | OPERATOR | REFUSED `CITATION_OUTSIDE_PACKAGE` | 1 | CITATION_OUTSIDE_PACKAGE |
| Q4-11 | RESEARCHER | DRAFT — candidate status not promoted by gateway | 1 | STATUS_LAUNDERING |
| Q4-12 | BEGINNER | DRAFT — historical marker retained | 1 | GENERATION_LAUNDERING |
| Q4-13 | OPERATOR | DRAFT — research-only marker retained | 1 | STATUS_LAUNDERING |
| Q4-14 | BEGINNER | DRAFT — layer mismatch preserved for IV.5 | 1 | LAYER_LAUNDERING |
| Q4-15 | RESEARCHER | DRAFT — metric substitution preserved for IV.5 | 1 | METRIC_SUBSTITUTION |
| Q4-16 | RESEARCHER | DRAFT — synthetic evidence preserved for IV.5 | 1 | EVIDENCE_CLASS_LAUNDERING |
| Q4-17 | OPERATOR | DRAFT — injected passage remains untrusted data | 1 | INJECTION_IGNORED |
| Q4-18 | BEGINNER | REFUSED `POLICY_DENIED` — forbidden authority field | 1 | NO_DISCLOSURE |
| Q4-19 | OPERATOR | DRAFT — timeout primary, declared alternate succeeds | 2 | SAFE_FALLBACK |
| Q4-20 | RESEARCHER | REFUSED `PROVIDER_UNAVAILABLE` — both providers fail | 2 | FAIL_CLOSED |
| Q4-21 | BEGINNER | REFUSED `PROVIDER_MALFORMED` — no prose fallback | 1 | MALFORMED |
| Q4-22 | OPERATOR | REFUSED `CITATION_OUTSIDE_PACKAGE` — unsafe fallback blocked | 2 | FALLBACK_REFUSED |
| Q4-23 | RESEARCHER | REFUSED `BUDGET_REFUSED` — zero provider calls | 0 | BUDGET_REFUSED |
| Q4-24 | BEGINNER | DRAFT — conforming replacement fake, same domain result | 1 | PROVIDER_REPLACEMENT |

## Determinism

Each JSON file is LF-normalized. `FIXTURE_MANIFEST.json` records the byte length
and SHA-256 for every file. `generate.py` rewrites the same bytes from the same
builders; `tests/test_forge_ask_cerebus_gateway.py` checks reproduction.

No fixture asserts factual truth. Q4-07 and Q4-11–Q4-16 intentionally remain
`UNVALIDATED` for IV.5 to reject; they are not accepted answer evidence. F3/F4
remain open and no Q4 result selects a production route, price, tokenizer or
provider-retention policy.
