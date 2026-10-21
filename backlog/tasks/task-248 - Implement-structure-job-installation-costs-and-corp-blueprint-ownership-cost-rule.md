---
id: TASK-248
title: Implement structure job installation costs and corp blueprint ownership cost rule
status: Done
assignee: []
created_date: '2026-10-20 13:42'
updated_date: '2026-10-20 14:02'
labels:
  - orders
  - pricing
  - facilities
  - calculations
dependencies: []
priority: high
type: feature
ordinal: 248000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per user directive:
1. Ensure Option A is fully implemented (gross profit margin % on revenue).
2. General rule: any blueprint (BPO/BPC) owned by the corporation in CorpBlueprint is NOT counted as a cost (0 ISK). Only missing blueprints not in corp possession represent an acquisition cost.
3. Include the costs to manufacture the product in a structure (industry job installation fees: System Cost Index + Facility/TaxConfig tax rate) in true_cost and quote build cost calculations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Verify and ensure blueprint ownership rule: if corp owns BPO or BPC (CorpBlueprint), blueprint cost is 0 ISK; only unowned/missing blueprints have acquisition cost
- [x] #2 Implement ESI system cost index caching and structure job installation fee calculation for manufacturing and reactions
- [x] #3 Include structure job installation fees in order.true_cost and view_quote estimated build cost
- [x] #4 Display profit margin % on revenue (Option A) in view_quote.html alongside the ISK profit margin
- [x] #5 Add unit tests covering blueprint ownership rule and structure installation fees
- [x] #6 Verify on devauth with Order #279 live recalculation
<!-- AC:END -->
