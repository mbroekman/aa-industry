---
id: TASK-79
title: Filter corporate jobs to only show linked active tasks
status: Done
assignee: []
created_date: '2026-08-18 12:00'
updated_date: '2026-08-18 12:00'
labels: []
dependencies: []
ordinal: 79000
---

# Filter corporate jobs to only show linked tasks

## Description

The user requested that the "My Corporate Jobs" and "Corporate Jobs Overview" tabs in the industrialist dashboard ONLY show EVE jobs that are directly linked to a claimed task.
Unlinked jobs should no longer be visible in these views to prevent unrelated or personal jobs from cluttering the active interface. Jobs linked to `COMPLETED` tasks are still preserved so users can use the "Delivered" filter to see their past claimed job history.

## Acceptance Criteria

- [x] `corp_active_jobs` strictly filters by `taskjoblink__isnull=False` and uses `.distinct()`.
- [x] `my_eve_jobs` strictly filters by `taskjoblink__isnull=False` and uses `.distinct()`.

## Implementation Notes

- Modified `industry_reforged/views/industrialist.py`.
- Added the relation lookup filter to only fetch jobs with an active task link.
