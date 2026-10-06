---
id: TASK-224
title: Fix DataTables sorting collapsing expanded groups
status: Done
assignee: []
created_date: '2026-10-06 08:15'
updated_date: '2026-10-06 08:15'
labels: []
dependencies: []
ordinal: 400000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When sorting the DataTables, the drawCallback redraws the rows and resets them to hidden, making sorting appear broken. State of expanded groups needs to be saved so sorting works without collapsing groups.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sorting does not collapse expanded groups, Sorting works as expected
- [ ] #2 1,2
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added global Set expandedGroups to preserve the collapse state across DataTables redrawing.
<!-- SECTION:NOTES:END -->
