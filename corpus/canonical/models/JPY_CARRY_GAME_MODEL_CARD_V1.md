# MODEL CARD — JPY Carry Game L1-L3 V1

model_id: JPY.CARRY_GAME.L1_L3.V1
status: CORE_CANDIDATE
market_scope: USDJPY,AUDJPY,EURJPY
layer: CROSS_LAYER
model_type: CROSS_ASSET + DESTINATION + PATH + EXECUTION_SUPPORT
product_exposure: SUBSCRIBER_MODEL

## Purpose
Use a role-based JPY basket to separate carry leadership, risk/execution expression and confirmation/veto rather than treating three correlated pairs as equal votes.

## Asset roles
USDJPY = carry master / primary structural driver.
AUDJPY = risk/execution expression.
EURJPY = confirmation/veto.
EURJPY is not an equal third vote unless a later validated model explicitly changes the role map.

## Evidence base
Recovered modern operator research used182 common basket weeks.
Recovered basket relationship:
USDJPY + AUDJPY agreed direction115/168 =68.5%.
When they agreed, EURJPY confirmed103/115 =89.6%.
These are relationship statistics, not trade WRs, and require Evidence Cards before promoted numerical display.

## Layering
L3: carry/basket destination and broad state.
L2: pair/basket path and confirmation.
L1: local execution geometry and invalidation.

## Related historical geometry
JPY12-4PM DT research includes132/168/187.5 structures, no-132-touch continuation and132-touch+OCC recovery.
Do not automatically merge those setups into Carry Game; crosswalk only when source/manual establishes the relation.

## Small-N governance
Matrix cells with tiny samples remain research flags. The operator manual explicitly recognizes this limitation.

## Implementation
Modern operator manual + multiple Pine generations were located in recovery sweep; latest implementation/evidence should be materialized before automation approval.

## Ask CEREBUS
Beginner: The three JPY pairs have different jobs: leader, expression and confirmation.
Operator: Return basket state, USDJPY master direction/state, AUDJPY execution expression, EURJPY confirmation/veto, then local setup context.
Researcher: Return common-week population, exact agreement definition and cell N.
Forbidden: equal-vote majority logic; treating89.6% confirmation as trade WR; autonomous execution before implementation parity review.
