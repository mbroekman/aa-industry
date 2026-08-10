---
id: TASK-46
title: Remove data-parent-id for flat tables
status: Done
assignee: []
created_date: '2026-08-09 06:39'
updated_date: '2026-08-09 06:40'
labels: []
dependencies: []
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Remove data-parent-id HTML attributes from rows in the Industrialist dashboard to completely disable the Javascript tree-rendering logic.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 No plus/minus signs or Javascript tree rendering logic occurs in the tables.
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Removed all data-parent-id attributes from all task rows to prevent the frontend Javascript from converting the tables into collapsible trees.

<!-- SECTION:NOTES:END -->
