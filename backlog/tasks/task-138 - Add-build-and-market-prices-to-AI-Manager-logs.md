---
id: TASK-138
title: Add build and market prices to AI Manager logs
status: Done
assignee: []
created_date: '2026-09-07 16:53'
updated_date: '2026-09-07 16:53'
labels: []
dependencies: []
ordinal: 192000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User requested to add the exact build price and sell price to the AI logs to make the reason for skipping clearer.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Logs include sell_price and build_cost

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated calculate_profitability to return the breakdown and ai_manager to log it.

<!-- SECTION:NOTES:END -->
