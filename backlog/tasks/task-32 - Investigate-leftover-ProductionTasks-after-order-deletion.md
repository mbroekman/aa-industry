---
id: TASK-32
title: Investigate leftover ProductionTasks after order deletion
status: Done
assignee: []
created_date: '2026-08-07 07:41'
updated_date: '2026-08-07 07:42'
labels: []
dependencies: []
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User deleted orders, but claimed jobs (ProductionTasks) remain. Need to find out why tasks aren't cascading correctly on order deletion.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Root cause found and tasks are properly deleted with their associated orders

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed cascade deletion bug where deleting an order didn't delete tasks belonging to its sub-orders, causing them to become orphaned when Django set created_from_order to NULL. Deleted 609 existing orphaned tasks in the database.

<!-- SECTION:NOTES:END -->
