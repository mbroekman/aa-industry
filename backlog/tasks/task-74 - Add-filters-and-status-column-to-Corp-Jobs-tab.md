---
id: task-74
title: Add filters and status column to Corp Jobs tab
status: Done
created: 2026-08-16
---

# Add filters and status column to Corp Jobs tab

## Description

The user requested that the general "Corporate Jobs Overview" tab also receives the same filtering capabilities and status column that were added to the "My Corporate Jobs" tab.
Currently, it only displays "active" jobs and lacks a dropdown filter or a visual indicator for jobs that are ready to deliver.

## Acceptance Criteria

- [x] Update the `corp_active_jobs` query to fetch all relevant statuses (active, ready, delivered, paused, cancelled).
- [x] Add a status column to the table with badges.
- [x] Add a dropdown filter (Active, Ready, Delivered, Other, All).
- [x] Link the DataTables search to the dropdown filter via JS.

## Implementation Notes

- Updated `industry_reforged/views/industrialist.py` to use `status__in`.
- Updated `industry_reforged/templates/industry_reforged/industrialist_dashboard.html` to mirror the structure and logic of the `myevejobs` tab.
