---
id: task-71
title: Add subdivision and ready status to Build Steps tab
status: Done
created: 2026-08-16
---

# Add subdivision and ready status to Build Steps tab

## Description

The user noted that the "Build Steps" tab did not have the correct subdivision when it comes to the statuses of a job.
Specifically, "EVE In Progress" was combining both active and ready jobs.
The tab needs to be updated to split "Active" and "Ready" EVE jobs into their respective subdivisions, and the table filter needs to be expanded to allow filtering specifically for "Ready" build steps.

## Acceptance Criteria

- [x] Split the "EVE In Progress" column into "EVE Active" and "EVE Ready" values.
- [x] Determine the row's progress status (`active`, `ready`, or `completed`) based on EVE job readiness versus claimed items.
- [x] Expand the dropdown filter to include "Ready" alongside Active and Completed.

## Implementation Notes

- Updated `industry_reforged/views/industrialist.py` to calculate `eve_active` and `eve_ready` separately for `my_claimed_summary` using the `job.is_ready` property.
- Added logic to calculate `row_status` (`ready` if `eve_ready` covers the uncompleted amount, `completed` if `completed >= to_build`, else `active`).
- Updated `industry_reforged/templates/industry_reforged/industrialist_dashboard.html`:
  - Added "Ready" option to the `#summary-filter-select` dropdown.
  - Formatted the "EVE Jobs" column to show yellow checkmarks for `eve_ready` quantities and blue factory icons for `eve_active` quantities.
  - Replaced the hardcoded inline status calculation on `<tr data-status="..">` with `data-status="{{ sum_item.row_status }}"` so the JS filter works smoothly.
