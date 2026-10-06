---
id: TASK-218
title: Fix BOM engine exploding BUY items at depth 0
status: Done
assignee: []
created_date: '2026-10-06 06:40'
updated_date: '2026-10-06 06:40'
labels: []
dependencies: []
ordinal: 394000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CONCORD 25000mm Steel Plates and other BUY items were still being exploded if they were the root item in a quote (depth 0). This caused their cost to be calculated based on moon materials instead of Jita price.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Root BUY items do not explode in BOM engine, Quote cost for CONCORD items is now realistic
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Removed the 'if depth > 0' check in bom_engine.py. Now, if an item is configured as BUY in CorpItemConfig (or defaults to BUY if no build config), it will NOT explode its materials even if it is the root item of a quote (depth 0). This fixes the issue where CONCORD items would be exploded into moon materials, causing absurd pricing (16 billion for 3 plates).
<!-- SECTION:NOTES:END -->
