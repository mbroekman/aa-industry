---
id: TASK-225
title: Disable pagination on Required Raw Materials table
status: Done
assignee: []
created_date: '2026-10-06 08:20'
updated_date: '2026-10-06 08:20'
labels: []
dependencies: []
ordinal: 401000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Because rows are collapsed by default, DataTables pagination causes empty-looking pages if a single group spans the entire pageLength. Disabling pagination fixes this UX issue.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Pagination is disabled on the Required Raw Materials table, All collapsed group headers appear on a single page
- [ ] #2 1,2
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Set paging: false on the DataTables initialization to prevent hidden collapsed rows from disrupting pagination logic.
<!-- SECTION:NOTES:END -->
