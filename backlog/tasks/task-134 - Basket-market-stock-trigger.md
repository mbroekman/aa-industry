---
id: TASK-134
title: Basket market stock trigger
status: Done
assignee: []
created_date: '2026-09-07 12:57'
updated_date: '2026-09-12 12:37'
labels: []
dependencies: []
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add logic to evaluate market stock levels (C‑N) for basket items and trigger orders when market stock is below basket target. Include logging for Loki and Maelstrom examples.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 When market stock < target, AI creates ProductionTask; logs show correct stock values.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented get_market_stock to query ESI and added it to effective_stock calculation in evaluate_baskets.
<!-- SECTION:NOTES:END -->
