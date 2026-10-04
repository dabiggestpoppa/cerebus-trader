# MODEL CARD — EUR Weekly Engine V1.1

model_id: EUR.WEEKLY.V1_1
status: CANONICALIZATION_CANDIDATE
market_scope: EURUSD
layer: L2
model_type: PATH + DISTRIBUTION + TEMPORAL
product_exposure: SUBSCRIBER_MODEL

## Purpose
Describe the weekly route, expansion state, timing and promoted outer nodes from the early-week seed without pretending to own higher-order destination.

## Inputs
Monday/early-week seed ranges; weekly tier; hour/state; consumed nodes; OCC/acceptance state; prior peak/extreme timing; higher-order context when available.

## Outputs
Weekly path state, range-left, timing surface, outer actionable nodes, OCC/static state and invalidation/context.

## Modern doctrine
Weekly layer owns PATH, not monthly/quarter destination.
Outer nodes only are preferred for promoted operator display.
Once OCC freezes a promoted structure, plotting should remain static according to the implementation specification.

## Calibration lineage
Recovered EUR weekly tier research includes T1/T2/T3 samples N=45/69/60 with median weekly ranges approximately126.8/133.5/168.95p.
Recovered Monday Q50/Q75/Q90 expansion factors:
T1 7.33/10.44/12.77
T2 5.39/7.16/7.73
T3 4.20/6.04/6.95.
These are research claims pending Evidence Cards, not universal constants.

## Temporal layer
Hour x Tier surface extends through the weekly horizon.
58-72h prior-peak / mid-week timing is a research feature, not a guaranteed timer.

## Evidence / negative evidence
Higher-order scientific review found weekly context useful for path/execution but it did not improve the monthly destination forecast enough to justify forced confluence.
This is a core architectural result: do not turn every layer into one score.

## Known limitations
Weekly nodes depend on exact seed/range definition and clock.
Small-N cells remain research flags.
Do not transfer EUR factors to another asset.

## Lineage
Ancestors: Monday weekly workbook, WILM/ILM, temporal delivery, recursive/fractal weekly clocks.
Relations: EUR Higher Order supplies L3 destination; EUR Daily supplies L1 execution.

## Implementation
CEREBUS_Weekly_Engine_V1_1.md and associated indicator lineage.
Dashboard/display behavior is not evidence by itself.

## Ask CEREBUS
Beginner: Weekly tells you the likely route and timing inside the bigger destination.
Operator: Return current weekly tier, path state, promoted outer nodes, range-left and time state.
Researcher: Return exact seed definition, tier sample, hour surface and evidence status.
Forbidden: claiming weekly layer predicts quarter/month destination merely because it aligns.
