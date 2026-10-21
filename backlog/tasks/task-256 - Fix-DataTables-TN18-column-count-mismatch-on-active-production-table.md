---
id: TASK-256
title: Fix DataTables TN18 column count mismatch on active-production-table
status: Done
assignee: []
created_date: '2026-10-21 18:46'
labels:
  - bugfix
  - ui
dependencies: []
ordinal: 430000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix DataTables warning TN/18 ("Incorrect column count") on `#active-production-table` in the Industrialist Dashboard caused by a missing Origin `<td>` column in `<tbody>`, which left only 7 columns in table rows while `<thead>` has 8 columns.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Restore missing Origin `<td>` column with `dt_task_origin.html` in `#active-production-table` tbody
- [x] #2 Verify column count between `<thead>` (8) and `<tbody>` (8) matches exactly
- [x] #3 Verify DataTables `config1.columnDefs` targets `[0, 7]` align with table structure
- [x] #4 Run full pytest suite and ensure 100% tests pass
- [x] #5 Deploy to devauth sandbox and verify error is resolved
<!-- AC:END -->
