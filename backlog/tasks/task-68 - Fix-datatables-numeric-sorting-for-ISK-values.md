---
id: TASK-68
title: Fix datatables numeric sorting for ISK values
status: Done
assignee: []
created_date: '2026-08-15 07:04'
updated_date: '2026-08-15 07:04'
labels: []
dependencies: []
ordinal: 68000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Sort by reward and cost yields weird sorting because DataTables sorts formatted ISK alphabetically. Added data-sort attributes with raw values to fix this.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Clicking sort on ISK columns sorts numerically

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added data-sort to templates

<!-- SECTION:NOTES:END -->
