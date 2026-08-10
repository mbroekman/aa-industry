---
id: TASK-42
title: Filter completed tasks by reward > 0
status: Done
assignee: []
created_date: '2026-08-09 06:20'
updated_date: '2026-08-09 06:21'
labels: []
dependencies: []
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Update the 'Recent Completed Tasks' query to only show tasks that have a builder_reward > 0 so that tasks without rewards are hidden.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Completed tasks list only shows tasks with reward > 0
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added builder_reward\_\_gt=0 to the 'recent' task type query in datatables.py.

<!-- SECTION:NOTES:END -->
