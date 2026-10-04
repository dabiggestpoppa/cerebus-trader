# P90 LINEAGE REGISTRY

Status: Recovery registry / not a performance guarantee
Updated: 2026-10-04

## Purpose
Preserve what P90 meant in each CEREBUS generation, what was implemented, what evidence exists, and what survives into FORGE.

## P90-0 — Conceptual kinetic threshold
Meaning: qualifying candle body as evidence that a constraint pathway has activated.
Historical ontology language: kinetic validation / plastic vs elastic deformation.
Status: CONCEPT SURVIVES; deterministic rhetoric deprecated.

## P90-1 — Time-window detector
Historical EUR thresholds:
02-04 4.1p
04-06 4.6
06-08 4.6
08-10 5.9
10-11 6.2.
Manual event additionally tied to Asian-band resolution.
Status: HISTORICAL_CANONICAL_DEFINITION; exact reproduction needed.

## P90-2 — Base80 / initial
First qualifying directional P90 after Asian constraint.
Historical target family -25/-50 AR.
Initial stop family 80% P90 body.
Historical report WR83.3.
Raw Python reconstruction initial WR34.9 in later artifact.
Status: CLAIM/IMPLEMENTATION DIVERGENCE.

## P90-3 — Cascade
Second/third same-direction qualifying P90.
Opposite default ignored.
Historical report second87.8, third84.2;45-60m best88.2.
Raw Python artifact cascade1 51.2, cascade2 60.1.
Status: STRUCTURAL HYPOTHESIS SURVIVES; exact historical magnitude unverified.

## P90-4 — 45-Min Add
Legacy time-conditioned add after initial activation and sufficient extension.
Historical report91.2 standalone condition /93.4 combined language.
Raw Python:30 trades,53.3% in later artifact.
Status: LEGACY_VARIANT / REPRODUCTION_REQUIRED.

## P90-5 — EWS
Opposite P90 near target.
Meaning: exhaustion/exit warning, NOT automatic reversal.
This semantic survives strongly across manuals and later research.
Status: SURVIVED_OPERATOR_DOCTRINE.

## P90-6 — Stall-Harvest / deep-state
168 stall interaction;200 deep-state boundary.
Opposite reversal historically required deep-state +132 kill confirmation.
Status: HISTORICAL_VARIANT / useful state semantics / performance reproduction required.

## P90-7 — P90P Distribution Tracker
P90 used as one conditioning feature in expected final distribution:
Base Tier .40
Regime .25
P90 .20
Cascade .10
Time decay .05.
6AM/9AM checkpoints.
Status: ABSORBED into modern range-left/checkpoint conditioning.
Historical precision claims not independently validated.

## P90-8 — V5 Pine integrated implementation
Contains Asian range, P90 thresholds, extension tracking,132 violation, multi-position execution,45m add and P90P display.

CRITICAL CODE AUDIT:
The current V5 Pine entry block calculates direction-specific stop and target prices, BUT all three strategy.entry calls submit strategy.long:
P90_Pos1_Long -> strategy.long
P90_Pos2_Long -> strategy.long
P90_Pos3_Long -> strategy.long.
Therefore bearish P90s are not actually submitted as short positions in this code path.

This is a concrete implementation defect, not a theoretical concern.
It can materially invalidate V5 strategy-performance output for bearish signals.

The V5 detector also does not enforce the Python >60% body/range quality filter.
Status: IMPLEMENTATION_NOT_PARITY_SAFE.

## P90-9 — Python cascade reconstruction
Raw later artifact:
EURUSD M5 Jan2023-May2026
1,153 trades,43.5%,PF1.10,+430p.
Initial34.9
Cascade1 51.2
Cascade2 60.1
45m53.3.

Important implementation issues:
- fixed UTC-5
- timezone stripped if aware
- calendar-date state reset
- Asian session spans19-03
- >60% body/range filter
- detector itself does not require outside-band close.

### Session ownership defect
The loop resets Asian high/low when calendar date changes.
Because Asian session is19:00-03:00, the range accumulated19:00-23:55 is cleared at midnight, then rebuilt from00:00-03:00.
Thus this implementation does NOT measure the intended full19:00-03:00 Asian range.

This is a concrete defect and is highly material because tier, targets, kill switch, and eligibility all depend on Asian range.

Status: RAW IMPLEMENTATION EVIDENCE, NOT VALID P90 PARITY TEST.

## What FORGE should teach now
1 P90 is a kinetic/momentum event, not mean reversion.
2 Exact P90 definition is generation-specific.
3 Same-direction repetition/cascade is a conditional-strength hypothesis.
4 Opposite P90 is not automatically a reversal.
5 EWS is primarily exit/exhaustion semantics.
6 P90 became a conditioning feature in distribution/range-left models.
7 Historical WR claims must carry source/generation labels.
8 Existing V5/Python implementations contain concrete parity defects; do not cite their performance as definitive tests of manual P90.
9 P90 remains a valid reproduction candidate because automation is feasible once event/session semantics are corrected.

## Recommended future test
Do NOT patch old result files.
Build a clean research implementation with:
- research-day ownership evening19:00 assigned to following day
- explicit fixed-EST vs America/New_York mode
- exact19:00-03:00 final bar convention
- outside-band close required
- body threshold exact
- optional body/range filter as separate ablation
- initial/cascade/EWS event ledger
- first-delivery targets before stop
- no strategy sizing in discovery layer
- raw event ledger before trade simulation.
