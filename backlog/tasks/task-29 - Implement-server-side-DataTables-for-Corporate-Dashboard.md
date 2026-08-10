---
id: TASK-29
title: Implement server-side DataTables for Corporate Dashboard
status: Done
assignee: []
created_date: '2026-08-07 07:28'
updated_date: '2026-08-07 07:30'
labels: []
dependencies: []
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Convert the corporate jobs tables on the Corporate Dashboard to use DataTables server-side processing (AJAX) to improve performance with large datasets, similar to the Director Dashboard.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Corporate Active Jobs uses AJAX
- [x] #2 Corporate History Jobs uses AJAX

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added dt_corporate_jobs endpoint in datatables.py. Created partials for corp installer, item, and status. Refactored corporate_dashboard.html to use server-side DataTables. Removed synchronous DB queries from dashboard.py for active and history jobs.

<!-- SECTION:NOTES:END -->
