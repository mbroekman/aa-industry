---
id: TASK-133
title: Fix margin floor logic in AI manager
status: To Do
assignee: []
created_date: '2026-09-07 12:30'
labels: []
dependencies: []
ordinal: 130000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Debug pricing engine and use basket min_profit_margin instead of global floor. Ensure calculate_profitability returns proper margin and logs show correct values.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Margin calculation returns non‑zero when prices are available; basket uses its own min_profit_margin; AIMarketLog shows correct margin values.

<!-- AC:END -->
