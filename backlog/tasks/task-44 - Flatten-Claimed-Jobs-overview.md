---
id: TASK-44
title: Flatten Claimed Jobs overview
status: Done
assignee: []
created_date: '2026-08-09 06:31'
updated_date: '2026-08-09 06:32'
labels: []
dependencies: []
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Remove the tree/sub-part indentation from the Claimed Jobs (my_tasks) overview in the industrialist dashboard. All claimed tasks should be displayed on a single flat level.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Claimed Jobs overview displays all tasks flatly without indentation or sub-part UI elements
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Removed the tree-building logic and indentation from the industrialist dashboard. Active and completed tasks are now queried without bom_parent filters and displayed as a flat list.

<!-- SECTION:NOTES:END -->
