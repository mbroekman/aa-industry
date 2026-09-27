---
id: TASK-181
title: Investigate ME/TE settings usage in material calculation
status: Done
assignee: []
created_date: '2026-09-27 13:48'
updated_date: '2026-09-27 13:55'
labels: []
dependencies: []
ordinal: 357000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User reported that the configured ME (Material Efficiency) values do not seem to be used when calculating the required materials for an order.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 - Configured ME/TE values from CorpPricingConfig or ItemConfig are applied correctly during Bill of Materials (BOM) calculation.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Found and resolved an issue where T1 blueprints were incorrectly evaluated as non-researchable due to a flawed check on 'eve_market_group_id'. Replaced this with a reliable check for the presence of the ME research activity. This ensures Corporate Pricing ME overrides are now correctly applied to BOM calculations.
<!-- SECTION:NOTES:END -->
