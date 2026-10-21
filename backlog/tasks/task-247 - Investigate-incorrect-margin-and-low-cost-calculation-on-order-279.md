---
id: TASK-247
title: Investigate incorrect margin and low cost calculation on order 279
status: Done
assignee: []
created_date: '2026-10-20 11:58'
labels:
  - orders
  - pricing
  - calculations
dependencies: []
priority: high
type: bug
ordinal: 247000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Order #279 on devauth reports an unrealistic profit margin of ~84% and the calculated actual costs ('werkelijke kosten') are way too low.
Investigate the cost and margin calculation pipeline (BOM breakdown, material valuation, facility taxes, pricing modifiers, run counts) on order #279, identify why costs are underestimated and margin is inflated, and formulate a detailed findings report and proposed remediation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Inspect Order #279 on devauth: item composition, customer price, recorded cost, BOM breakdown, and profit/margin metrics
- [x] #2 Trace calculation logic in industry_reforged (models, pricing engine, BOM service, quote/order calculation views)
- [x] #3 Document exact root causes of cost underestimation and inflated margin (84%)
- [x] #4 Produce comprehensive analysis report artifact with findings and concrete solution options
<!-- AC:END -->

## Implementation Notes
- Diagnosed 5 root causes on Order #279:
  1. Lowball/troll buy orders (0.01 ISK) on 47 raw materials in Jita Buy order book.
  2. Direct-buy items (Deadspace fittings) without blueprints priced at 0.01 ISK.
  3. `order.true_cost` was not recalculated upon quoting in `provide_quote`.
  4. Datatables column formula calculated markup on cost rather than gross profit margin on revenue.
  5. Blueprint purchase prices (BPOs, 10.1 Trillion ISK) were incorrectly summed into `total_bom_price` in `view_quote`.
- Implemented fixes across `pricing_engine.py`, `quotes.py`, and `datatables.py`.
- Added unit tests in `test_pricing.py` and `test_quotes_views.py`; all 270 test suite checks pass cleanly.

