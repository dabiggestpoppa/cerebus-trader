# Security amendment 1 — CI receipt

## 1. Implementation head

| Field | Value |
|---|---|
| Workflow | FORGE Tests |
| Run id | `42813830771` |
| Head SHA | `26032731b7dfaa1ca26e59417aa047dc5ae41ba1` |
| Status | completed · **success** |
| Jobs | `postgres` success, `test` success |

That head contains the whole amendment: fixtures, IV.5 repair, additive IV.6
extension, the 26 drivers and the three evidence documents.

## 2. Local regression at the same content

```
python -m pytest -q
2582 passed, 17 failed, 29 skipped
```

The 17 failures are the checkout-encoding guards inventoried in
`INFRASTRUCTURE_HANDOFF.md` §2. They fail identically at `d21ebd0` (the Rung 1
head, whose CI run `42808104008` was also green on Linux) and are unrelated to
this amendment; no new failure appears. The amendment's own 26 drivers pass on
both this checkout and CI.

## 3. What this receipt does not claim

- No Windows full-suite pass; F-08 remains **OPEN**.
- No 27/27 amendment; AM1-R27 is deferred (`DEFERRED — TEST INFRASTRUCTURE OWNER`).
- No publication, provider, market-data, entitlement or Book V readiness.

This receipt records run `42813830771` only. Later documentation-only commits are
verifiable through the same workflow and carry no source change.
