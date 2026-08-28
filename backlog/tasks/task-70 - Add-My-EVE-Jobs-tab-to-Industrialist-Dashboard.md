---
id: TASK-70
title: Add My EVE Jobs tab to Industrialist Dashboard
status: Done
assignee: []
created_date: '2026-08-16 12:00'
updated_date: '2026-08-16 12:00'
labels: []
dependencies: []
ordinal: 70000
---

# Add My EVE Jobs tab to Industrialist Dashboard

## Description

The user wants to expand the Industrialist Info by adding a separate tab for the EVE jobs installed by the Industrialist.
Currently, they are mixed into the general corporate jobs on the Industrialist Dashboard.
The new tab should show only the corporate jobs that belong to the user's characters, displayed using a DataTable with a filter for active, ready, and delivered jobs.

## Acceptance Criteria

- [x] Add a new "My EVE Jobs" tab to the Industrialist Dashboard.
- [x] Display only `CorporationIndustryJob` records where `installer_id` matches one of the user's characters.
- [x] Use a single DataTable.
- [x] Add a filter dropdown for statuses: Active, Ready (to be delivered), Delivered, and Other (Paused/Cancelled).

## Implementation Notes

- Updated `industry_reforged/views/industrialist.py` to query `CorporationIndustryJob` where `installer_id__in=user_characters` and `status__in=["active", "ready", "delivered", "paused", "cancelled"]`.
- Passed `my_eve_jobs` to the template context.
- Modified `industry_reforged/templates/industry_reforged/industrialist_dashboard.html` to include a new tab button "My EVE Jobs" next to Payment Summary.
- Created the new tab pane with a dropdown filter (`#myevejobs-filter-select`) and a DataTable (`#myevejobs-table`).
- Added JS logic in `$.fn.dataTable.ext.search.push` to filter rows based on `data-job-status` attribute, mapping "other" to paused and cancelled.
