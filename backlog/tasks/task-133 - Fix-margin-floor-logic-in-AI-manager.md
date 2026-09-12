---
id: TASK-133
title: Fix margin floor logic in AI manager
status: Done
assignee: []
created_date: '2026-09-07 12:30'
updated_date: '2026-09-12 12:29'
labels: []
dependencies: []
ordinal: 197000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Debug pricing engine and use basket min_profit_margin instead of global floor. Ensure calculate_profitability returns proper margin and logs show correct values.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Margin calculation returns non‑zero when prices are available; basket uses its own min_profit_margin; AIMarketLog shows correct margin values.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified that the code already uses basket min_profit_margin.
<!-- SECTION:NOTES:END -->
