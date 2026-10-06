---
id: TASK-223
title: Make material groups collapsible and collapsed by default
status: Done
assignee: []
created_date: '2026-10-06 08:01'
updated_date: '2026-10-06 08:02'
labels: []
dependencies: []
ordinal: 399000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update the DataTables drawCallback to add toggle icons and click handlers to the group headers. Hide the material rows by default unless the user is actively searching in the table.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Group headers have a toggle icon, Clicking a group header toggles the visibility of its materials, Materials are collapsed by default, Materials are expanded automatically when a search filter is applied
- [ ] #2 1,2,3,4
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated DataTables drawCallback to add group collapse functionality. Group rows act as toggle buttons. Material rows are hidden by default unless there is an active search filter.
<!-- SECTION:NOTES:END -->
