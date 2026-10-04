# SETUP CARD — JPY Carry Role-Gated Operator V1

setup_id: SETUP.JPY.CARRY_ROLE_GATE.V1
status: CANONICALIZATION_CANDIDATE
market_scope: USDJPY,AUDJPY,EURJPY
execution_class: MANUAL_OPERATOR
parent_model_ids: JPY.CARRY_GAME.L1_L3.V1
product_exposure: OPERATOR_ONLY

## Purpose
Gate local JPY execution through the basket's role hierarchy rather than equal-vote pair correlation.

## Eligibility
Resolve USDJPY carry-master state.
Resolve AUDJPY risk/execution state.
Use EURJPY as confirmation/veto.
Resolve daily or weekly native tier and no-go state for the pair being executed.

## Basket gate
Primary agreement is USDJPY + AUDJPY.
EURJPY confirmation strengthens the aligned basket state but is not itself an entry trigger.

## Local execution
Execution setup must come from the selected pair's L1 state/geometry.
Historical132/168/187.5 JPY geometry is not automatically imported; only use it when the current Carry Game setup explicitly references that family.

## No-go
Do not majority-vote three pairs.
Do not enter EURJPY solely because it confirms.
Do not use a pair whose native tier is in no-go.
Do not quote basket confirmation percentage as trade WR.

## Evidence
EV.JPY.CARRY.BASKET_RELATION.V1 supports the role gate:
USDJPY+AUDJPY agreement115/168=68.5%;
EURJPY confirmation conditional on that agreement103/115=89.6%.
These are state relationships.

## Automation
Manual operator model until latest Pine/manual parity is established.
No autonomous execution approval.

## Ask CEREBUS
Beginner: first see whether the JPY leader and risk pair agree; use EURJPY as the referee, then look for the actual entry on the chosen pair.
Operator: return all three role states, executed pair tier, confirmation/veto and local setup.
Forbidden: equal voting;89.6%=WR; historical DT setup inserted without lineage.
