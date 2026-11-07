# Book III integration fixtures

Ten deterministic fixtures proving that the six ratified Book III blocs can be
composed over one synthetic object graph.

- `_builders.py` — reuses the III.6 fixture builders and constructs III.1 bars,
  III.2 measurements, III.4 snapshots and III.5 evaluations through their
  ratified public interfaces.
- `generate.py` — writes the fixtures; `--check` verifies byte-identical
  regeneration (LF-normalized).
- `FIXTURE_MANIFEST.json` — SHA-256 of every fixture.
- `FROZEN_BASELINE.json` — starting head, 79-module inventory, fixture count.

Discipline: every fixture is synthetic (`SYNTHETIC_FIXTURE`) and cannot satisfy
an evidence reference. A positive fixture proves a contract path, never market
accuracy, performance or production readiness. Cases that require unavailable
canonical material are represented by their governed refusal, not by invention.
