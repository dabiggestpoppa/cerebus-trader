# SETUP CARD — Fib Rekey Operator V1

setup_id: SETUP.FIB.REKEY.V1
status: RESEARCH_OPERATOR_CANDIDATE
market_scope: CROSS_ASSET_RECALIBRATED
execution_class: RESEARCH_ONLY
parent_model_ids: CROSSASSET.FIB.RANGE_BIRTH.V1
product_exposure: RESEARCH_LAB

## Purpose
Express a valid born range through the rekey ladder only after anchor legitimacy and setup-specific eligibility are established.

## Eligibility
A valid active A-B Range Birth is mandatory.
Correct Alpha/Beta/Gamma/Delta family identified.
Asset-native calibration and clock active.
Do not use arbitrary local pivots.

## Entry lineage
Primary rekey location:132%.
Historical dual-entry research also includes168%.
50-72% is a separate entry/location family and must not be conflated with rekey entry.

## Invalidation / targets
Recovered rekey lineage:
132 entry -> invalidation around168; targets midpoint / -25 depending setup generation.
168 entry -> invalidation around185.
-25 extension is conditional in dual-entry lineage and historically depended on rekey triggering first.

## No-go
No Range Birth = no fib setup.
Do not transfer R11 frequency/hit rates into R15.
Do not promote because projected RR looks attractive if anchor eligibility is absent.
Do not infer a universal cross-asset tolerance.

## Evidence
EV.FIB.R11.ANCHOR_OVERGEN.V1 is negative evidence explaining why anchor gating is mandatory.
Current R15 eligibility/evidence must be attached before this card can become AUTOMATION_APPROVED or canonical operator execution.

## Ask CEREBUS
Beginner: rekey is a structural remapping setup inside an already valid range, not a magic132 line.
Operator: first return anchor validity, family and state; if anchor is unresolved, stand down.
Researcher: identify R-generation, eligible population and exact invalidation/target semantics.
