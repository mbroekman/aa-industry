---
id: TASK-45
title: Fix TypeError in industrialist dashboard
status: Done
assignee: []
created_date: '2026-08-09 06:33'
updated_date: '2026-08-09 06:34'
labels: []
dependencies: []
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Fix TypeError caused by adding a QuerySet to a list after flattening the my_tasks array.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Industrialist dashboard loads without TypeError
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed TypeError by wrapping my_tasks_qs in list(), resolving the crash when it tries to concatenate my_tasks + my_completed_tasks in line 247.

<!-- SECTION:NOTES:END -->
