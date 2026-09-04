---
id: TASK-125
title: Implement True Material Cost (BOM-Based) Pricing
status: Done
assignee: []
created_date: '2026-09-04 15:30'
updated_date: '2026-09-04 15:54'
labels: []
dependencies: []
references:
  - backlog/docs/doc-12 - Proposal-Alternative-Cost-Calculation-Methodology.md
type: feature
ordinal: 115000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Implement Alternative Cost Calculation Methodology based on doc-12, replacing or complementing the Jita Sell Quote with a Bottom-Up Bill of Materials Cost Model.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Create calculate_bom_cost function in pricing_engine.py
- [ ] #2 Add material valuation configuration setting (Jita Buy, Jita Sell, Corp Manual)
- [ ] #3 Display True Cost on Director Dashboard
- [ ] #4 Implement Minimum Margin Floor hybrid option

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Implemented True Material Cost (BOM-Based) Pricing, configuration in CorporationPricingConfig, calculating true cost and minimum margin in calculate_quote(), added true_cost to MemberOrder and exposed on director dashboard.

<!-- SECTION:NOTES:END -->
