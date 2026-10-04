# Chapter 4 — Session Architecture: Truth, Confirmation, and Delivery

**Status:** Canonical reconstruction draft  
**Source basis:** Canvas nodes 23, 27–28, 34–37, 41–42  
**Verification boundary:** Session labels and behavior claims are reconstructed from the canvas and remain unverified unless separately tested.

## 4.1 The three-session state machine

The canvas organizes the trading day as a handoff:

```text
ASIA — Truth / first bias
        ↓
LONDON — Confirmation, conflict, or hedge selection
        ↓
NEW YORK — Delivery, continuation, squeeze, or invalidation
```

This is not merely chronological. Each session has a different epistemic role:

- **Asia reveals** the first risk signal through JPY-linked instruments.
- **London tests** that signal through CHF and European cross-flows.
- **New York resolves** whether USD and North American liquidity confirm or reverse it.

---

## 4.2 Asian Session — truth session

Primary instruments:

- USD/JPY
- CHF/JPY
- Supporting context: AUD/JPY, NZD/JPY, WTI/CAD where relevant

The canvas expects Asia to provide:

- The first meaningful bias of the day.
- The cleanest early read on risk sentiment.
- A direction London may respect, challenge, or overshoot.

### Asian classification rule

```text
IF CHF/JPY falls
AND USD/JPY falls,
THEN classify Asia as risk-off aligned.

IF CHF/JPY rises
AND USD/JPY rises,
THEN classify Asia as risk-on aligned.

IF the two disagree,
THEN classify Asia as mixed and await London.
```

No magnitude threshold is provided in the canvas; therefore the rule is incomplete for automation.

---

## 4.3 London Session — confirmation and hedge selection

Primary instruments:

- CHF/JPY
- EUR/GBP
- EUR/USD
- GBP/USD
- EUR/CHF

The canvas assigns London two jobs:

1. Determine whether European money accepts the Asian risk direction.
2. Determine whether CHF or JPY is the preferred hedge and whether EUR or GBP is the preferred European expression.

### London response states

```text
IF CHF follows the JPY direction established in Asia,
THEN classify London as confirming
AND elevate the probability of a trend day.

IF CHF opposes JPY,
THEN classify London as conflicting
AND downgrade the day toward chop.

IF CHF materially overshoots the Asian signal,
THEN classify the move as a possible reversal or weekly-extreme event.
```

“Overshoot” is undefined in the source and must be quantified before execution.

### European internal selector

```text
IF EUR/GBP rises during the accepted London direction,
THEN EUR is the preferred European leg.

IF EUR/GBP falls,
THEN GBP is the preferred European leg.

IF EUR/GBP remains compressed,
THEN treat Europe as unresolved and rely more heavily on CHF/JPY and CAD/USD confirmation.
```

---

## 4.4 New York Session — delivery session

Primary instruments:

- USD/JPY
- USD/CHF
- EUR/USD
- GBP/USD
- USD/CAD
- CAD/JPY
- WTI and SPX as contextual confirmations

The canvas calls New York the delivery session because it decides whether the earlier state becomes:

- Continuation
- Squeeze
- Reversal
- Invalidation

### NY confirmation rule

```text
IF USD/JPY and USD/CHF agree with the London/Asian state,
THEN classify NY as confirming delivery
AND preserve the swing thesis.

IF USD disagrees with the London state,
THEN classify NY as invalidating or reversing the day
AND do not blindly hold the earlier thesis.
```

### Delivery distinction

New York “delivery” in this chapter means **session-level realization of a prior basket state**. It must remain distinct from the broader T.E.L.I.T. concept of Delivery, which is an ontology state linked to expectancy, risk management, market structure, and closure.

---

## 4.5 Five reconstructed setup families

The canvas references five weekly setup families. The following are reconstructed at the highest fidelity possible from the available node text.

### Setup 1 — Japan Set the Tone

**Conditions**

- Asia establishes a strong common direction in USD/JPY and CHF/JPY.
- Example risk-off state: both pairs fall.

**Interpretation**

- Asia has produced a clear JPY-led risk signal.

**Action candidate**

- Wait for NY entry in the same JPY direction rather than chasing the Asian move.

**Source target claim**

- The canvas suggests these may become multi-day swings.

**Missing requirements**

- Strength threshold
- Entry trigger
- Stop/invalidation
- Exit rule

### Setup 2 — CHF Agrees with Japan

**Conditions**

- Asia establishes the direction.
- London extends CHF/JPY in the same direction.
- NY USD pairs confirm rather than negate the risk state.

**Interpretation**

- Cross-session alignment is present.

**Action candidate**

- Select the clearest aligned risk or USD expression.

**Invalidation**

- NY dollar behavior contradicts the established state.

### Setup 3 — CHF Fights Japan

**Conditions**

- Asia points one way through JPY.
- London CHF flow points the other way.

**Interpretation**

- Hedge selection is unresolved.
- Canvas expectation: chop/fakeout regime.

**Action candidate**

- Reduce size, wait, or avoid broad directional positioning until NY resolves the conflict.

### Setup 4 — USD Confirms London

**Conditions**

- London establishes an accepted European/risk direction.
- USD/CHF and USD/JPY agree in New York.

**Interpretation**

- New York is delivering rather than invalidating the London move.

**Action candidate**

- Maintain the aligned swing thesis, subject to formal risk rules.

### Setup 5 — USD Invalidates London

**Conditions**

- London establishes a direction.
- New York dollar pairs reject that direction.

**Interpretation**

- The earlier move may have been positioning, a squeeze, or a false directional signal.

**Action candidate**

- Exit or avoid holding the London thesis; evaluate a day-level reversal only after a defined trigger.

These setup labels are reconstructed from the visible text and graph context. Exact source wording for all five is not fully preserved in the atomic excerpt, so these remain provisional playbook records.

---

## 4.6 Session handoff matrix

| Asia | London | New York | Regime classification |
|---|---|---|---|
| Clear | Confirms | Confirms | Full three-session alignment |
| Clear | Confirms | Rejects | NY invalidation/reversal candidate |
| Clear | Conflicts | Resolves Asia | Delayed continuation candidate |
| Clear | Conflicts | Resolves London | London reversal candidate |
| Mixed | Establishes direction | Confirms | London-led day |
| Mixed | Mixed | Establishes direction | NY-only day / reduced swing confidence |

This matrix is a normalized reasoning aid. It does not assert historical win rates.

---

## 4.7 Pair-selection logic by session

### Asia

Use JPY crosses to detect early risk condition:

- USD/JPY
- CHF/JPY
- Optional AUD/JPY and NZD/JPY as higher-beta context

### London

Use European crosses to determine acceptance and expression:

- CHF/JPY for hedge confirmation
- EUR/GBP for EUR-versus-GBP selection
- EUR/CHF for European stress

### New York

Use dollar and North America instruments to determine delivery:

- USD/CHF for true USD stance
- USD/JPY for carry/risk continuation
- USD/CAD for oil/CAD/USD interaction
- CAD/JPY for NY risk appetite
- WTI and SPX for contextual confirmation

---

## 4.8 Canonical daily workflow

```text
STEP 1 — Record Asian state
  risk-on / risk-off / mixed

STEP 2 — Record London response
  confirm / conflict / overshoot / unresolved

STEP 3 — Determine European expression
  EUR-led / GBP-led / CHF-protective / unresolved

STEP 4 — Record NY USD state
  confirm / invalidate / squeeze / neutral

STEP 5 — Select pair
  choose the instrument with the cleanest relative divergence

STEP 6 — Apply separate execution logic
  trigger, entry, stop, target, and closure must come from a validated playbook
```

The final step is critical: basket/session analysis provides **state and selection**, not a complete entry model by itself.

---

## 4.9 AI reasoning constraints

An AI using this chapter must follow these constraints:

1. Never infer an entry solely from a session label.
2. Retrieve the risk basket, USD filter, and European selector together.
3. Distinguish “session delivery” from T.E.L.I.T. Delivery.
4. Report conflicting signals instead of forcing a direction.
5. Treat causal and performance claims as unverified unless a test record is attached.
6. Require explicit timezone and session boundaries before automating.
7. Require magnitude thresholds for words such as “hard,” “dumping,” “running,” “coiling,” or “overshoot.”

---

## 4.10 Open reconstruction gaps

- Exact definitions of Asia, London, and NY windows.
- All original text for the five setup families may not be fully recoverable from current excerpts.
- Entry, stop, target, and management rules are largely absent.
- “Weekly swing high/low like clockwork” is an unverified claim.
- “NY money-making candle” needs a precise candle window and statistical test.
- The four missing linked Markdown files may contain the missing operational detail.