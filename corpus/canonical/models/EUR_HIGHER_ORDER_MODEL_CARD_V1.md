# MODEL CARD — EUR Higher Order V1

model_id: EUR.HIGHER_ORDER.V1
status: SCIENTIFIC_CORE_CANDIDATE
market_scope: EURUSD
layer: L3 + cross-layer routing
model_type: DESTINATION + CROSS_LAYER
product_exposure: SUBSCRIBER_MODEL

## Purpose
Estimate higher-order EURUSD destination and route responsibility across quarter, month and week while preserving layer separation.

## Canonical hierarchy
Quarter seed -> M1 range seed -> M2 shaping -> M3 resolution -> Weekly local path -> Daily execution.

L3 destination
L2 path
L1 execution.

## Inputs
Quarter/D1-D3 seed information; Month1 range/position; Month2 shaping state; unfinished-side state; Month3 completion state; weekly path context.

## Outputs
Higher-order directional/destination prior, unfinished-side/completion state and routing context for lower layers.

## Scientific evidence recovered
Long-history sample:59 quarters.
Forward OOS:14 quarters.
D3 quarter-direction prior:69.5% historical /71.4% OOS.
M1 range correlation: r=.746 in recovered scientific review.
Unfinished-side -> M3 completion:81.0% historical /83.3% OOS.
All numerical claims must be attached to exact Evidence Cards before user-facing promotion.

## Critical negative result
Weekly layer did not materially improve the monthly destination forecast.
Therefore no forced universal confluence score.
Agreement may inform confidence/context; it does not erase layer ownership.

## Known limitations
Quarter sample size is inherently smaller than daily samples.
Destination correctness does not imply a local entry is safe.
Forward-OOS N=14 is useful but still finite.
Exact definitions of D3 prior, unfinished side and completion must travel with evidence.

## Lineage
Ancestors: V4 nested/fractal resolution, monthly seed research, workbook temporal delivery.
Relations: EUR Weekly=L2 path; EUR Daily=L1 execution.

## Implementation
Quarter/Month tracker indicators visualize portions of this architecture but tracker output and scientific model evidence are distinct objects.

## Ask CEREBUS
Beginner: Higher Order answers where the larger EUR distribution is trying to finish, not where to click buy/sell.
Operator: Return destination prior, month state, unfinished-side state, confidence/evidence and handoff to Weekly/Daily.
Researcher: Return historical vs forward-OOS separately with definitions and N.
Forbidden: presenting69-83% layer statistics as trade win rates; forced confluence.
