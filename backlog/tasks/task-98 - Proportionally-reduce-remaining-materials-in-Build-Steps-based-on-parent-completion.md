---
id: TASK-98
title: >-
  Proportionally reduce remaining materials in Build Steps based on parent
  completion
status: Done
assignee: []
created_date: '2026-08-26 21:03'
updated_date: '2026-08-26 21:03'
labels: []
dependencies: []
ordinal: 88000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

When a parent task is partially built (has EVE jobs), the child tasks (materials) should have their remaining quantities reduced proportionally.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Remaining column accurately deducts materials that are already consumed by in-progress parent items

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated industrialist.py to calculate Build Steps 'remaining' dynamically via top-down tree traversal. This accurately accounts for consumed materials when parent tasks are partially built. Also moved 'Add Personal Token' button in the dashboard and removed redundant PI titles.

<!-- SECTION:NOTES:END -->
