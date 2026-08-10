---
id: TASK-58
title: Hide Material Progress for completed tasks
status: Done
assignee: []
created_date: '2026-08-09 11:36'
updated_date: '2026-08-09 11:36'
labels: []
dependencies: []
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Do not show the Material Progress badge when a task status is COMPLETED.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Badge hidden for completed tasks
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added task.status != 'COMPLETED' check to the Material Progress badge if-statement in both the Unclaimed Jobs and Claimed Jobs lists so it hides itself once a task is fully built.

<!-- SECTION:NOTES:END -->
