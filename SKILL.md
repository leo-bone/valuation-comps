---
name: valuation-comps
title: Valuation Comps — Trading Comparable Company Analysis
summary: Give it a ticker and it runs the full 8-step comparable-company analysis, producing a definition-aligned comps table and an implied valuation range. The first-principles tool of equity analysis — a relative valuation anchor.
read_when:
  - user wants relative valuation / comparable company analysis (comps / trading comps)
  - user names a company and asks whether it is expensive or cheap versus peers, and where a fair range sits
  - user wants a multiples table (EV/Revenue, EV/EBITDA, P/E)
  - user mentions "comps" "comparable companies" "relative valuation" "peer multiples" "too expensive"
---

> **English** · [简体中文](SKILL_CN.md)

# Valuation Comps

A reusable skill that lets a coding agent run **comparable company analysis (trading comps)**.
Same design philosophy as Zara Zhang's `frontend-slides`: code is only the medium —
**reusable, reproducible, verifiable** is what makes it worth building.

This skill does not forecast price levels. It gives a relative anchor — *what multiple is the market
currently willing to pay for this kind of business* — and forces cross-checking against absolute
valuation (DCF). `scripts/comps_calc.py` is the calculation core:
**the agent fetches data and aligns definitions; the script does the arithmetic.** That removes mental
math errors and definition mismatches.

## When to use
- Judge whether a target is expensive or cheap relative to peers (whether "cheap" is real).
- Produce a standardised comps table quickly for banking / investing / research work.
- Serve as the cross-check layer against DCF and precedent transactions.

## The eight steps (run in order, leave a trace at each)

1. **Define target and vantage**: the subject (A-share / HK / US ticker or company name) plus the
   vantage (buy-side: should I buy; sell-side: what should it fetch). Record current price, shares
   outstanding, market cap and net debt (net debt = interest-bearing debt − cash).
2. **Screen peers (three axes, not an industry label)**:
   - Same business (same track / business model, not merely the same four-digit GICS code);
   - Comparable scale (revenue / market cap within 0.3×–3× of the target; large deviations get a
     separate "scale adjustment" note);
   - Same market (same listing venue, so liquidity and discount-rate environment are comparable).
   - Target 3–8 names; record why each was included or excluded (see `references/peer_selection.md`).
3. **Pull multiples**: at minimum EV/Revenue, EV/EBITDA and P/E. Add EV/Gross Profit for growth
   names; use P/B and P/E for financials (never the EV family — their balance sheets are structurally
   different). State the applicability condition for every multiple (see `references/multiples.md`).
4. **Align definitions (the easiest place to get it wrong)**:
   - Use **normalised multiples** (NTM or FY+1 forward basis), not a single LTM point;
   - Strip one-off items (restructuring, impairments, investment gains, FX);
   - EV includes net debt, P/E does not — mixing them requires an explicit conversion (the script
     handles it);
   - Companies with negative EBITDA / negative EPS: **exclude from the multiple sample but do not
     delete them** — note the reason, so the median isn't dragged down and distorted.
5. **Compute the centre**: report the **median** as primary, with mean and 25th/75th percentiles as
   secondary. The median is steadier against outliers. Run `scripts/comps_calc.py` directly (input:
   peer multiples plus the target's forecast metrics).
6. **Run sensitivity**: 25th / 50th / 75th percentile multiples against the target's matching forecast
   metric to produce a **valuation range**, not a point. The script outputs this directly.
7. **Implied check**: reconcile the comps-implied value against DCF and precedent transactions. A gap
   above 20% forces a review of peer selection or definitions — "just average them" is not allowed.
8. **Conclude**: state expensive / fair / cheap explicitly, and name the **variables that would
   trigger a re-rating** (not a price target). Cheap without a reason is a value trap and must be
   explained (see `references/value_trap.md`).

## Data sources (in priority order; never fabricate)
- **`westock-data` skill first** (structured market data covering A-share / HK / US): market cap, EV,
  revenue, EBITDA, net income, consensus estimates (NTM / FY+1).
- Fallbacks: `akshare-stock` / `neodata-financial-search` for A-share detail and consensus.
- Last resort: `WebSearch` / `WebFetch` — company IR pages, annual reports, quote pages.
- **Mark any missing field `N/A` with a reason.** Never fill placeholder numbers into the report.
  `scripts/comps_calc.py` skips `N/A` samples automatically and flags them in the output.

## Output format
Produce two things:
1. **Markdown report** (structure in `examples/sample-comps.md`): screening logic + comps table (with
   median / percentiles) + sensitivity range + conclusion and re-rating triggers + data date and source.
2. **Calculation trace**: the raw output of `scripts/comps_calc.py` appended verbatim, so it's
   reproducible.

### Minimum comps table structure
| Peer | EV/Rev | EV/EBITDA | P/E | Why included |
|---|---|---|---|---|
| Peer A | 4.2x | 14.1x | 22.0x | Leader in the same track |
| Peer B | 3.6x | 12.8x | 19.5x | Comparable scale |
| **Median** | **4.2x** | **14.1x** | **22.0x** | — |

## Checks and red lines (reliability floor)
- Fewer than 3 samples: do not report a median conclusion, only "insufficient sample, indicative only".
- Any sample multiple deviating more than 2× from the median gets flagged in red for review (likely a
  definition mismatch or an outlier).
- If the target's resulting price conflicts with the DCF conclusion by more than 20%, you may not
  state both "buy" and "cheap" — resolve the conflict first.
- Every multiple must carry its basis (LTM / NTM / FY+1) and currency; unify currencies before
  comparing.

## Boundaries and disclaimer
- Comps reflect **market sentiment**, not intrinsic value; always cross-check against absolute valuation.
- Multiple differences must be explained (growth, leverage, inflection, liquidity), not just labelled
  cheap or expensive.
- Stamp every conclusion with data date and source. Investment decisions belong to a human; this skill
  produces a reproducible analysis skeleton.

## Layout
```
valuation-comps/
  SKILL.md                  # this file (English)
  SKILL_CN.md               # 简体中文版
  README.md                 # usage + data sources + example
  references/
    peer_selection.md       # three-axis peer screening checklist + exclusion logic
    multiples.md            # applicability conditions and definition traps per multiple
    value_trap.md           # value trap checklist
  scripts/
    comps_calc.py           # calculation core (median / percentiles / implied range / checks)
    comps_calc_test.py      # unit tests, so the arithmetic is trustworthy
  examples/
    sample-comps.md         # anonymised sample report
```
