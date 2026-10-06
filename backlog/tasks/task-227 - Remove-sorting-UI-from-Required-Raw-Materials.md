---
id: TASK-227
title: Remove sorting UI from Required Raw Materials
status: Done
assignee: []
created_date: '2026-10-06 08:31'
updated_date: '2026-10-06 08:31'
labels: []
dependencies: []
ordinal: 403000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User requested to remove the ability to sort the BOM table manually. Sorting will be disabled in the UI, but the initial internal sort (by group, then by name) will be preserved.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sorting arrows are removed from table headers, Clicking headers does not sort the table, Items within groups remain sorted alphabetically by name
- [ ] #2 1,2,3
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added orderable: false to all column targets. This hides the sorting arrows and disables the manual sorting UI, while keeping the internal [[0, 'asc'], [1, 'asc']] ordering active for proper grouping and alphabetical listing.
<!-- SECTION:NOTES:END -->
