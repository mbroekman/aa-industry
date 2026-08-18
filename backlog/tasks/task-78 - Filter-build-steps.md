---
id: task-78
title: Filter completed tasks from industrialist build steps
status: Done
created: 2026-08-18
---

# Filter completed tasks from industrialist build steps

## Description

The "Build Steps" tab on the industrialist dashboard was previously showing groups for `ProductionTask`s that were already `COMPLETED`. This caused completed tasks to linger in the active build list and artificially pull in active EVE jobs that were unrelated, making delivered tasks appear as "active".

## Acceptance Criteria

- [x] Only items with tasks currently `IN_PRODUCTION` should appear in the Build Steps.
- [x] Tasks that are `COMPLETED` should not inflate the "Claimed" or "Completed" columns of active tasks.

## Implementation Notes

- Modified `industry_reforged/views/industrialist.py`.
- Changed `status__in=["IN_PRODUCTION", "COMPLETED"]` to `status="IN_PRODUCTION"` in the `all_tasks_grouped` query.
- This ensures that only active tasks are grouped and evaluated for the "Build Steps" view.
