---
id: TASK-85
title: Fix empty corp stock in shopping list flat overview
status: Done
assignee: []
created_date: '2026-08-24 21:03'
updated_date: '2026-08-24 21:05'
labels: []
dependencies: []
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The Corp Stock column in the Flat Overview of the Shopping List is empty. Investigate and fix why the value is not showing.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 The Corp Stock column shows the stock quantity (or 0) instead of being empty.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated `bom_engine.py` and `views/orders/shopping.py` to retrieve CorpInventory stock levels when calculating tasks BOMs or generating custom shopping lists, fixing the empty 'Corp Stock' column in the shopping list's flat overview.

<!-- SECTION:NOTES:END -->
