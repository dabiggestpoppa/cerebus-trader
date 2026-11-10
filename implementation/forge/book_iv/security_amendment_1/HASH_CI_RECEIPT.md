# Hash canonicalization — CI receipt

| Field | Value |
|---|---|
| Workflow | FORGE Tests |
| Run id | `42825972485` |
| Head SHA | `66a0192d1dabef48506bc52a09660685b82ea143` |
| Status | completed · **success** |
| Jobs | `test` success, `postgres` success |

That head contains the whole infrastructure repair: the canonical helper and its
24 acceptance drivers, the seventeen migrated guards, the policy plan, the
constant ledger, the AM1-R27 behavioural driver, the LF/CRLF reproduction and the
ratification.

## What the Linux job adds

The two local environments in `HASH_REPRODUCTION_V1.md` were both native
Windows runtimes differing only in checkout encoding. This run is the Linux
evidence: the same seventeen guards, the same helper, AM1-R27 and the full suite
on a checkout with `core.autocrlf=false` under the CI job's own Python. A pass
here plus the two local passes is what makes the cross-encoding claim hold on
both operating systems rather than on one.

## What this receipt does not claim

- No second operating-system run of the CRLF environment; CRLF was executed only
  on native Windows.
- No closure of F-06 or F-07, and no change to BG-C (`BLOCKED`) or
  `EV-GATE-01`–`13` (`OPEN`).
- No production provider, market data, entitlement or Book V work.

This receipt records run `42825972485` only. The documentation commit that
follows it carries no source change and is verified by the same workflow.
