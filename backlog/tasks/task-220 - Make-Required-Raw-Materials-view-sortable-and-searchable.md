---
id: TASK-220
title: Make Required Raw Materials view sortable and searchable
status: Done
assignee: []
created_date: '2026-10-06 07:39'
updated_date: '2026-10-06 07:39'
labels: []
dependencies: []
ordinal: 396000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User requested to make the Required Raw Materials view sortable by name and quantity. Also, a search functionality needs to be added.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Required Raw Materials view is sortable by name, Required Raw Materials view is sortable by quantity, A search functionality is available in the Required Raw Materials view
- [ ] #2 1,2,3
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented DataTables for Required Raw Materials view. Sortable by name and quantity via data-order attributes, integrated searching, and maintained separate groups for materials and blueprints using drawCallback.
<!-- SECTION:NOTES:END -->
