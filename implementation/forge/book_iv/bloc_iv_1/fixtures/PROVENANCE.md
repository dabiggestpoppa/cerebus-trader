# IV.1 golden fixture provenance

- Base head: `6ca573d226b14100b9244b3a8d7bb92f68b5907f`
- Query contract: `ASK_QUERY_CONTRACT.V1`
- Fixtures: 12 (Q-01–Q-12)
- Generator: `generate.py` (deterministic, offline)
- Expectations: query plans only — intent, identity, scope, depth, flags, confidence, ambiguity.
- No market observation, performance figure, probability, answer or provider response is present.
- Regeneration on the same contract version must be byte-identical.
