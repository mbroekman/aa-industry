---
id: TASK-230
title: Update wipe_industry_data command to include new order models
status: Done
assignee: []
created_date: '2026-10-06 09:08'
updated_date: '2026-10-06 09:08'
labels: []
dependencies: []
ordinal: 406000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update the wipe_industry_data management command to also wipe CorpBuyOrder and ensure it fully cleans the system of all order-related data while preserving config.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Command deletes CorpBuyOrder, Command deletes MemberOrder, Command deletes ProductionTask
- [ ] #2 1,2,3
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated the wipe_industry_data command to also safely delete all CorpBuyOrders, along with MemberOrders and ProductionTasks.
<!-- SECTION:NOTES:END -->
