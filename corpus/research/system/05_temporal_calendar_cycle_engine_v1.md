# Chapter 5 — Temporal and Calendar Cycle Engine

## Status

**Canonical reconstruction draft v1.** This chapter preserves the canvas's temporal models while separating three distinct clocks that must not be merged:

1. a repeating **week-letter cycle**;
2. a continuous **daily A→B→C→D code**;
3. longer **quarterly, super-cycle, and 60-day measurement/delivery models**.

The canvas treats time as a state variable. It does not yet prove that the same letter has one universal market meaning across every clock.

## 1. Temporal hierarchy

The recovered temporal branch is best represented as:

```text
Recurring code
    ├── Weekly A/B/C/D designation
    ├── Daily continuous A/B/C/D designation
    ├── Month-by-month weekday calendar
    ├── Quarterly and year-close observations
    └── Instrument-specific long cycles
            └── USD/NOK 60-day model
```

The graph connects the month-by-month calendar to the week-letter table and then to the full-year continuous code. It also connects the week-letter table to the large quarterly/super-cycle research node. These arrows establish dependency and continuation, but do not define a single executable strategy by themselves.

## 2. Week-letter cycle

The canvas maps calendar weeks into a repeating four-state loop:

| Week position | Letter |
|---:|:---:|
| 1 | A |
| 2 | B |
| 3 | C |
| 4 | D |
| 5 | A |

The sequence repeats through week 52. Formally:

```text
week_letter = [A, B, C, D][(week_number - 1) mod 4]
```

A separate note states: **“Week C, Month C swings are golden.”** This is preserved as a high-priority hypothesis, not a validated law. The canvas does not yet define:

- how a “Month C” is calculated;
- what qualifies as a swing;
- the instrument or timeframe;
- the tested sample size;
- the entry, invalidation, and target.

## 3. Weekday-only month calendar

The month-by-month node assigns A/B/C/D letters to weekdays from November 2025 through December 2026. Weekends are omitted. The sequence advances one letter per listed weekday and continues across month boundaries.

This is a **trading-day presentation layer**, not necessarily the same clock as the continuous daily code. For example, the weekday table labels January 1, 2026 as **B**, January 2 as **C**, and January 5 as **D**, because the weekend is skipped in the displayed progression.

The extracted registry contains **304 weekday-date assignments**.

## 4. Continuous daily Code 2

A second node explicitly defines a different mechanism:

```text
No resets.
Every calendar day advances one step.
A → B → C → D → A
Weekends are included.
Anchor: January 1, 2025 = A.
```

From that anchor, January 1, 2026 is stated as **B**. The rule can be represented as:

```text
index(date) = days_since_2025_01_01 mod 4
letter(date) = [A, B, C, D][index(date)]
```

This clock is continuous across weekends and month boundaries. It must not be silently substituted for the weekday-only calendar.

## 5. Calendar conflict that must remain explicit

The two date tables are related but not identical:

- **Weekday calendar:** advances across listed weekdays only.
- **Code 2 calendar:** advances across all calendar days.

They can agree on some dates and diverge on others. A future system must require a field such as `calendar_mode` before calculating a code.

Recommended canonical values:

```text
WEEK_NUMBER_CYCLE
WEEKDAY_SEQUENCE
CONTINUOUS_CALENDAR_DAY
INSTRUMENT_SPECIFIC_CYCLE
```

## 6. Quarterly and year-close research branch

The large quarterly node begins with the statement:

> Year close in the direction of the candle; range holds as quarterly high.

It then contains extensive numbered observations involving percentages, rekeys, pullbacks, invalidations, colors, overlap windows, and super-cycle references. The material appears to be a research ledger rather than a finished playbook.

Canonical treatment:

- preserve every observation;
- do not infer one universal rule from the ledger;
- separate each numbered case into instrument, date, starting state, measured move, rekey, pullback, invalidation, and terminal state;
- require definitions for abbreviations such as `T`, `PB`, `INE`, `SS`, and color codes;
- require the missing linked file `trading/ART OF TRADE.md`, which points directly into this branch.

## 7. USD/NOK 60-day cycle

The canvas contains a complete instrument-specific model using non-overlapping 60-calendar-day windows.

### Cycle phases

```text
Day 0–11   Observation
Day 12–22  Measurement
Day 23     Entry
Day 23–60  Delivery
```

### Measurement definitions

During Day 12–22:

```text
Range High = highest price in the window
Range Low  = lowest price in the window
Range Size = Range High - Range Low
TP1        = Range High + 0.25 × Range Size
TP2        = Range High + 0.50 × Range Size
Invalidation = Range Low - 0.32 × Range Size
```

The source describes a long entry on Day 23, targeting TP1, with the 132% level as invalidation.

### Stated evidence

The source lists **18 historical periods**, with **16 TP1 hits and 2 failures**, stated as **88.89%**. The registry extracted 18 historical rows from the canvas table.

This evidence remains classified as:

```text
stated_in_canvas_unverified
```

Before execution or AI recommendation, it requires independent verification of:

- exact price source and timezone;
- whether Day 12–22 means inclusive calendar-day indexing;
- treatment of weekends and holidays;
- entry price on Day 23;
- spread, swap, and gap handling;
- whether TP1 was hit before invalidation;
- sample selection and forward-test separation.

## 8. Temporal engine as a state classifier

The safe canonical interpretation is:

```text
Temporal code
    ↓
Context / state label
    ↓
Pattern or instrument filter
    ↓
Validated execution model
```

The temporal code may condition expectancy, but it does not replace entry qualification, risk management, delivery analysis, or closure logic.

## 9. Machine-readable schema

```json
{
  "clock_id": "",
  "calendar_mode": "",
  "anchor_date": "",
  "anchor_state": "",
  "state_sequence": ["A", "B", "C", "D"],
  "period_length": null,
  "instrument": null,
  "measurement_window": null,
  "entry_window": null,
  "delivery_window": null,
  "conditions": [],
  "targets": [],
  "invalidation": null,
  "evidence_status": "stated_in_canvas_unverified",
  "source_nodes": []
}
```

## 10. Open reconstruction questions

1. What do A, B, C, and D mean behaviorally?
2. Is the week-letter cycle independent of the daily Code 2 sequence?
3. How is a month assigned a letter?
4. What exactly makes Week C + Month C “golden”?
5. Which instruments use the quarterly/super-cycle ledger?
6. What do the color combinations and abbreviations mean?
7. Does the USD/NOK model require a directional filter?
8. Is the Day 23 entry unconditional or structure-confirmed?
9. Does invalidation need to occur before TP1 for a failure?
10. Are the reported 18 periods in-sample or out-of-sample?

## Source nodes

- `ef0182a296470795` — week-letter table
- `e02493f0d0aabb75` — month-by-month weekday calendar
- `cc26ec9243184b29` — continuous daily Code 2 calendar
- `7cc93a1a1c1d5147` — Week C / Month C hypothesis
- `2f4f9df0b072ee62` — quarterly, year-close, and super-cycle research ledger
- `36d840f97e5ba3c0` — USD/NOK 60-day deep dive