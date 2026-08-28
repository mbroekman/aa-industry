---
id: TASK-72
title: Fix sorting on date countdown in corp jobs
status: Done
assignee: []
created_date: '2026-08-16 12:00'
updated_date: '2026-08-16 12:00'
labels: []
dependencies: []
ordinal: 72000
---

# Fix sorting on date countdown in corp jobs

## Description

The user reported that sorting on the date and countdown column in the "My Corporate Jobs" tab (and other tabs) is not working correctly.
DataTables fails to parse the datetime mixed with HTML `naturaltime` text accurately.
Adding a `data-sort` attribute with the Unix timestamp of `job.end_date` will fix this across the relevant tables.

## Acceptance Criteria

- [x] Add `data-sort="{{ job.end_date|date:'U'|default:0 }}"` to the `job.end_date` `<td>` in `industrialist_dashboard.html` (Corporate Jobs and My Corporate Jobs tabs).
- [x] Add the same to `personal_dashboard.html` where `job.end_date` is rendered.
