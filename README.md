# valuation-comps

> **English** · [简体中文](README_CN.md) · [Site](https://leo.uichain.org/)

[![CI](https://github.com/leo-bone/valuation-comps/actions/workflows/test.yml/badge.svg)](https://github.com/leo-bone/valuation-comps/actions/workflows/test.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen.svg)](scripts/)
[![Agent Skill](https://img.shields.io/badge/agent--skill-Claude%20%C2%B7%20Codex%20%C2%B7%20WorkBuddy-blueviolet.svg)](SKILL.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Trading comps that survive scrutiny.** Hand a coding agent a ticker and it runs the full 8-step
comparable-company analysis — peer screening, multiple alignment, quartiles, implied valuation
range — and writes up what the market is actually paying for this kind of business.

The catch most LLM finance workflows hit: **the model does the arithmetic in its head and the
numbers drift.** This skill refuses that. Every median, quartile and implied share price is
computed by a unit-tested script. The agent fetches data and interprets; it never multiplies.

---

## What you get

```
**样本数**：4 家 peer

| 倍数 | 可用样本 | 中位数 | 均值 | 25 分位 | 75 分位 | 隐含每股(25/中/75) |
|---|---|---|---|---|---|---|
| EV/Revenue | 4 | 4.05x | 4.2x | 3.83x | 4.42x | 22.41 / 23.81 / 26.16 |
| EV/EBITDA  | 4 | 13.8x | 14.18x | 13.32x | 14.65x | 13.49 / 14.03 / 14.98 |
| EV/GrossProfit | 0 | — | — | — | — | 无有效样本 |
| P/E | 4 | 21.6x | 22.03x | 20.77x | 22.85x | 51.94 / 54.0 / 57.12 |
```

Missing data shows up as `N/A` and gets **skipped**, never filled with a plausible-looking guess.
That one rule is the difference between a comps table you can defend and one that quietly lies.

## Quick start

```bash
python3 scripts/comps_calc_test.py                       # verify the math (CI runs this too)
python3 scripts/comps_calc.py --input examples/input.json # run the sample
```

Input is plain JSON — peer multiples plus the target's forecast metrics:

```json
{
  "net_debt": 1200,
  "shares": 800,
  "target": { "revenue": 5000, "ebitda": 900, "eps": 2.5 },
  "peers": [
    {"name": "Peer A", "EV/Revenue": 4.2, "EV/EBITDA": 14.1, "P/E": 22.0},
    {"name": "Peer B", "EV/Revenue": 3.6, "EV/EBITDA": 12.8, "P/E": 19.5}
  ]
}
```

Point your agent at [`SKILL.md`](SKILL.md) and it will gather the peers, fill this in, and run it.
Zero third-party dependencies — Python stdlib only.

## The 8 steps

1. **Frame** the target and the viewpoint (control vs minority, equity vs EV)
2. **Screen peers** on business model, size and geography — see [`references/peer_selection.md`](references/peer_selection.md)
3. **Pull multiples** from a real data source
4. **Align the calendar** (LTM / NTM / FY+1) and the currency — see [`references/multiples.md`](references/multiples.md)
5. **Compute central tendency** — median and quartiles, not the mean
6. **Build the sensitivity range**
7. **Cross-check** against DCF
8. **Conclude**, and name the variable that would make you re-underwrite

## Guardrails

- **EV multiples include net debt; P/E does not.** The script keeps the two lanes separate so
  they never get mixed in the same sentence.
- **Negative or missing denominators are dropped**, not patched.
- **A >20% gap vs. DCF blocks the conclusion.** You must reconcile methodology or peer set first.
- **Cheap is not cheap.** [`references/value_trap.md`](references/value_trap.md) lists the
  structural reasons a low multiple is correct.

## Data sources — no fabrication

1. `westock-data` — structured A-share / HK / US data with forward consensus
2. `akshare-stock`, `neodata-financial-search`
3. `WebSearch`, company IR, annual reports as fallback

Anything unavailable is written as `N/A`. The skill would rather hand you a hole than a number.

## Part of a three-skill loop

| Skill | Question it answers |
|---|---|
| [**macro-dashboard**](https://github.com/leo-bone/macro-dashboard) | Should I be deploying capital at all right now? |
| **valuation-comps** (here) | Is this cheap or expensive relative to its peers? |
| [**dcf-quick**](https://github.com/leo-bone/dcf-quick) | What is it worth, what is my downside, how big a position? |

Macro switch → screen → price. Each one is independently useful; together they keep you from
sizing a position off a valuation you ran in isolation.

## License

MIT. Analysis is a tool for thinking, not a substitute for it — the decision stays yours.
