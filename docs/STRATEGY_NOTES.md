# CEREBUS Strategy Notes

## System Overview
EUR/USD M5 always-in-market flip system.
Two Pine scripts: CEREBUS_IMPULSE and CEREBUS_REBALANCE.
Position is always either LONG or SHORT (or FLAT during transitions).

## Signal Types
- IMPULSE: Primary directional signal from CEREBUS_IMPULSE
- REBALANCE: Position correction from CEREBUS_REBALANCE

## Session Windows
- LONDON: 08:00 - 12:00 UTC
- NY: 13:30 - 17:00 UTC
- OVERLAP: 13:00 - 16:00 UTC (London/NY overlap)

## State ID Format
EURUSD_{YYYYMMDD}_{HHMM}_{SIDE}_{SEQ}
Example: EURUSD_20260426_0930_BUY_001

## Pine Truth Panel (required for Phase 2)
The active Pine indicator must render a table with:
- SIDE: current bias direction (BUY/SELL)
- MODEL: which script fired (CEREBUS_IMPULSE / CEREBUS_REBALANCE)
- STATE ID: matches signal_id format above
- VALID UNTIL: bar close time of the current signal

## Alert JSON (from Pine)
```json
{
  "signal_id": "EURUSD_{{timenow}}_BUY",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "signal_type": "IMPULSE",
  "strategy_name": "CEREBUS_IMPULSE",
  "timestamp": "{{timenow}}",
  "timeframe": "M5",
  "price": {{close}},
  "session": "LONDON",
  "state_id": "EURUSD_{{timenow}}_BUY"
}
```

## 5-Second Cooldown (Pine)
Prevents duplicate alerts within 5 seconds:
```pine
var int lastSignalTime = 0
canFire = (timenow - lastSignalTime) > 5000
if signalCondition and canFire
    alert(jsonPayload)
    lastSignalTime := timenow
```
