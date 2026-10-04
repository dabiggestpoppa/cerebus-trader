# Chapter 3 — Basket Intelligence Architecture

**Status:** Canonical reconstruction draft  
**Source basis:** Canvas nodes 22–23, 29–33, 35–37, 39–42  
**Verification boundary:** The architecture below faithfully reconstructs the canvas logic. Market claims remain `stated_in_canvas_unverified` unless supported by external testing.

## 3.1 Purpose of the basket architecture

The canvas does not treat an FX pair as an isolated market. It organizes instruments into overlapping baskets that answer different questions:

1. **What is the dollar doing?** — USD Power Index.
2. **Is the market risk-on or risk-off?** — Safe Haven Triangle.
3. **Which European currency is expressing the move?** — European Basket.
4. **How is New York liquidity preparing to deliver?** — North America Basket.
5. **Do risk and economic-flow readings agree?** — Combined alignment layer.

The central integration node states:

> Section 1 (JPY–CHF–USD) tells you **risk**. Section 2 (EUR–GBP–USD) tells you **economy**. When they agree, the canvas expects larger weekly swings; when they disagree, it expects chop and fakeouts.

This is the basket system's governing idea: **do not choose a trade from one pair; first determine whether independent baskets tell the same story.**

---

## 3.2 USD Power Index — core dollar flow

The canvas places three instruments at the top of the dollar hierarchy:

| Instrument | Reconstructed role | Question answered |
|---|---|---|
| DXY | Broad dollar reference | Is the dollar generally appreciating or depreciating? |
| USD/JPY | Dollar plus carry/risk expression | Is dollar movement aligned with global risk and JPY flow? |
| USD/CHF | Independent dollar-strength filter | Is USD strength genuine, or is USD/JPY being driven mainly by JPY? |

The canvas summarizes USD/CHF as the **judge**:

- USD/CHF rising → canvas interpretation: USD strong.
- USD/CHF falling → canvas interpretation: USD weak.
- It is used to prevent a JPY-driven move in USD/JPY from being mistaken for a pure USD move.

### Canonical dollar-state rule

```text
INPUTS: DXY, USD/JPY, USD/CHF

IF broad dollar direction and USD/CHF agree,
THEN classify the USD reading as confirmed.

IF USD/JPY moves but USD/CHF does not confirm,
THEN treat the move as potentially JPY-led rather than USD-led.
```

This is a reconstructed classification rule, not a validated trading signal.

---

## 3.3 Safe Haven Triangle — the tension meter

The safe-haven layer is built from:

- CHF/JPY — “wash meter” and relative hedge contest.
- JPY Index — global/Asian hedge pressure.
- CHF Index — European hedge pressure.

The triangle is intended to answer four questions:

1. Is stress present?
2. Is the stress European or global?
3. Is CHF or JPY winning the hedge flow?
4. Is the observed USD move real or false?

### Three-pair operational core

The canvas simplifies the risk engine into three major pairs:

| Pair | Canvas role | Provisional reading |
|---|---|---|
| USD/JPY | Risk-on engine | Rising = risk-on; falling = risk-off |
| CHF/JPY | Pure risk barometer / wash meter | Rising = money leaving JPY; falling = money entering JPY |
| USD/CHF | USD strength filter | Separates true USD flow from JPY/CHF-driven movement |

### Risk rotation sequence

The canvas proposes a sequence rather than a simultaneous move:

```text
RISK-OFF:
JPY first → CHF second → USD third

RISK-ON:
USD first → CHF → JPY last
```

This sequence should remain a hypothesis until it is formally timestamp-tested across instruments.

### Canonical risk-state rule

```text
IF CHF/JPY falls materially,
AND USD/JPY also falls,
THEN classify the basket as risk-off aligned.

IF CHF/JPY rises materially,
AND USD/JPY also rises,
THEN classify the basket as risk-on aligned.

USE USD/CHF to determine whether USD independently confirms the state.
```

---

## 3.4 European Basket — economy and London expression

The core European basket contains:

- EUR/USD
- GBP/USD
- EUR/GBP

The expanded version adds:

- EUR/CHF
- GBP/JPY

The canvas assigns the following roles:

| Instrument | Role |
|---|---|
| EUR/USD | Weekly European-versus-dollar tone |
| GBP/USD | Higher-volatility expression of European direction |
| EUR/GBP | Internal strength selector between EUR and GBP |
| EUR/CHF | European risk/hedge meter |
| GBP/JPY | UK risk-appetite expression |

The canvas frames EUR as the anchor, GBP as a leveraged/aggressive version, and CHF as the protective version.

### EUR/GBP selection rule

```text
IF EUR/GBP rises,
THEN classify EUR as stronger than GBP
AND prefer EUR/USD as the European expression, subject to USD confirmation.

IF EUR/GBP falls,
THEN classify GBP as stronger than EUR
AND prefer GBP/USD as the European expression, subject to USD confirmation.
```

### Trend-versus-tension rule

```text
IF EUR/GBP trends,
THEN treat the London direction as more credible.

IF EUR/GBP is sideways or tightly coiled,
THEN treat European direction as unresolved
AND use CHF/JPY and CAD-linked instruments to read the release path.
```

The canvas specifically claims that European tension may appear first in CAD, then CHF, then EUR, while GBP exaggerates the eventual move. This remains a research hypothesis.

---

## 3.5 North Atlantic Triangle — political-economy integration

The North Atlantic system combines:

- USD — reserve, liquidity, energy-pricing and Treasury axis.
- CAD — thinner-liquidity proxy connected to U.S. credit and oil.
- EUR — European settlement axis.
- GBP — aggressive/high-beta European expression.
- CHF — European settlement hedge.

This system bridges the European and North American baskets. Its core proposition is that **CAD may reveal developing North American positioning before the larger USD pairs fully move.**

### Reconstructed sequencing model

```text
EUR/GBP tension or neutrality
        ↓
CAD reacts first or acts as proxy
        ↓
CHF confirms the hedge direction
        ↓
USD delivers through NY pairs
        ↓
GBP exaggerates; EUR follows more slowly
```

The canvas summarizes this as:

> Watch CAD → position GBP → hedge with CHF.

Because several causal claims in this section are broad, they must remain `research_reference_only` until tested.

---

## 3.6 North America Basket — NY liquidity chain

The North America Basket contains:

- WTI crude oil
- CAD
- USD/CAD
- CAD/JPY
- S&P 500

The canvas describes it as the heartbeat of New York liquidity and proposes a conveyor-belt sequence:

```text
WTI → CAD → USD/CAD / CADJPY → SPX → USD confirmation
```

### Component roles

| Component | Canvas role |
|---|---|
| WTI | Upstream driver and early-volume market |
| CAD | Commodity-linked transmission currency |
| USD/CAD | Combined USD strength versus CAD/oil strength |
| CAD/JPY | NY risk-on/risk-off barometer |
| SPX | Equity confirmation of the risk state |

### Directional mappings stated in the canvas

```text
Oil rising → CAD stronger → USD/CAD pressure lower
Oil falling → CAD weaker → USD/CAD pressure higher

CAD/JPY rising → risk-on interpretation
CAD/JPY falling → risk-off interpretation
```

These mappings are conditional, not universal. USD/CAD can rise from USD strength, CAD weakness, or both; it can fall from USD weakness, CAD strength, or both.

---

## 3.7 Combined alignment matrix

The canvas's most important synthesis is agreement between the **risk basket** and the **economy/USD basket**.

| Risk layer | Economy/USD layer | Reconstructed interpretation | Action status |
|---|---|---|---|
| Risk-off | USD strong vs EUR/GBP | Broad defensive/USD-aligned environment | Candidate trend regime |
| Risk-on | USD weak | Broad pro-risk/non-USD environment | Candidate trend regime |
| Risk-off | USD weak | Mixed state; hedge demand without clean dollar confirmation | Reduce confidence |
| Risk-on | USD strong | Mixed carry/dollar state | Reduce confidence |

### Canonical alignment rule

```text
IF risk basket and economy/USD basket agree,
THEN elevate the regime to aligned.

IF they disagree,
THEN classify the regime as mixed
AND expect chop, fakeouts, or selective rather than broad movement.
```

The direction and size claims attached to these states remain unverified.

---

## 3.8 Daily basket drill

The strongest operational sequence recovered from the canvas is:

1. **Read EUR/GBP** — determine European internal strength or unresolved tension.
2. **Read USD/CAD/CAD flow** — identify possible early NY positioning.
3. **Read USD/CHF** — confirm genuine USD direction.
4. **Read CHF/JPY and USD/JPY** — confirm risk-on/risk-off state.
5. **Select the expression** — EUR/USD, GBP/USD, USD/CAD, USD/JPY, or CHF/JPY.
6. **Wait for session confirmation** — Asia reveals, London confirms or conflicts, NY delivers or invalidates.

### Formalized decision skeleton

```text
STATE_EUROPE = trend direction from EUR/GBP, or unresolved
STATE_CAD = early NY proxy direction, or neutral
STATE_USD = confirmed/contradicted by DXY and USD/CHF
STATE_RISK = risk-on/risk-off/mixed from CHF/JPY and USD/JPY

IF STATE_EUROPE, STATE_USD, and STATE_RISK align,
THEN select the pair expressing the strongest relative divergence.

IF one or more states conflict,
THEN downgrade confidence or wait for NY resolution.
```

---

## 3.9 Updating the basket map

The canvas includes the note:

> “BASKET WASH — update once a quarter, and once a month.”

Canonical interpretation:

- Review relationships monthly for tactical drift.
- Review basket membership and structural roles quarterly.
- Do not assume a relationship remains stable solely because it once appeared on the canvas.

---

## 3.10 Open validation questions

1. What exact thresholds define “rising,” “dumping,” “coiling,” and “strengthening early”?
2. Which session timestamps and timezone define Asia, London, and NY?
3. Does CAD statistically lead USD, and under what regimes?
4. Does CHF/JPY outperform standard risk measures after transaction costs?
5. How often does EUR/GBP correctly select EUR/USD versus GBP/USD?
6. How should conflicting DXY, USD/CHF, and USD/JPY states be weighted?
7. Are the proposed flow sequences stable across monetary-policy regimes?

Until resolved, these are knowledge-graph claims and candidate rules—not validated production logic.