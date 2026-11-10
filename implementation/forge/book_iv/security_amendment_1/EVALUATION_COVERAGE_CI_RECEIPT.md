# Evaluation coverage CI receipt (BA-34)

| Field | Value |
|---|---|
| Workflow | FORGE Tests |
| Run id | `42915280736` |
| Head SHA | `6cc7ced4a875c8618042d4bc88caa1426853bf29` |
| Status | completed, **success** |
| Jobs | `test` success, `postgres` success |

That head carries the whole coverage rung: the additive corpus EV-145-EV-154 and
its manifest, the evidence-path contract V2, the refusal-limitation contract V1,
the coverage scoring supplement and the EC-01-EC-30 drivers.

## What this run establishes

The 30 new drivers and the 2654-test suite pass on the CI checkout, not only on
the authoring machine, including the 112 original IV.6 drivers and the 86 IV.5
drivers that the two contracts must not disturb.

## What it does not establish

- No closure of F-07a (limitation representation, IV.5) or F-09
  (historical-lineage admission, IV.2/IV.4). Both are recorded OPEN with their
  evidence and their owning bloc.
- No coverage claim for the two `CORPUS_ABSENT` V1 cases (EV-007, EV-010) or for
  the amendment's held-out population beyond its own drivers.
- No BG-C unblocking, no `EV-GATE-01`-`13` closure, no human review, no
  provider, market, entitlement or retention work.

This receipt records run `42915280736` only. The documentation commit that
follows it changes no source and is verified by the same workflow.
