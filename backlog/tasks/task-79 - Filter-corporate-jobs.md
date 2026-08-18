---
id: task-79
title: Filter corporate jobs to only show linked active tasks
status: Done
created: 2026-08-18
---

# Filter corporate jobs to only show linked active tasks

## Description

The user requested that the "My Corporate Jobs" and "Corporate Jobs Overview" tabs in the industrialist dashboard ONLY show EVE jobs that are directly linked to a claimed task that has not yet been completed.
Unlinked jobs, or jobs linked to completed tasks, should no longer be visible in these views to prevent unrelated or old jobs from cluttering the active interface.

## Acceptance Criteria

- [x] `corp_active_jobs` strictly filters by `taskjoblink__task__status="IN_PRODUCTION"` and uses `.distinct()`.
- [x] `my_eve_jobs` strictly filters by `taskjoblink__task__status="IN_PRODUCTION"` and uses `.distinct()`.

## Implementation Notes

- Modified `industry_reforged/views/industrialist.py`.
- Added the relation lookup filter to only fetch jobs with an active task link.
