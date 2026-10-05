# Book I / Bloc I.1 — Acceptance

Bloc I.1 may be ratified only if all conditions pass.

## A. IDs and enums
- valid canonical IDs parse into object type + local identity
- ID prefix/type mismatch fails
- canonical identity fields are immutable
- unsupported enum values fail

## B. Objects
- canonical object validates with version/status/exposure/layer
- deterministic payload/hash is stable across dictionary ordering
- object type includes the frozen registry classes required by I.1

## C. References
- registry rejects duplicate IDs
- launch/normal objects with dangling references fail
- explicitly partial historical objects may preserve unresolved references without pretending they resolve
- self-reference is rejected unless a future typed relation explicitly permits it

## D. Lifecycle
- legal promotion/status transitions pass
- illegal resurrection/promotion from terminal states fails
- SUPERSEDED/FALSIFIED remain terminal for V1 kernel
- status transition never mutates object identity

## E. Conflict identity
- equal market/event/condition/clock/horizon/tolerance/eligibility/implementation semantics compare as same claim population
- mismatch on a material identity dimension returns PARALLEL rather than contradiction
- claim values/results are not part of population identity

## F. Regression/non-interference
- existing tests continue to pass
- no existing Signal Guard files changed for this Bloc
- no new external dependency required

## Evidence required
Exact pytest command/output, changed-file inventory, known gaps, ratification decision.
