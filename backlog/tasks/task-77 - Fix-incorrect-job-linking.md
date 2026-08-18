---
id: task-77
title: Fix incorrect job linking due to missing claim date filter
status: Done
created: 2026-08-18
---

# Fix incorrect job linking due to missing claim date filter

## Description

The background task `update_task_links` associates completed or active EVE jobs with user-claimed Production Tasks. Previously, it matched these jobs solely based on `character_id`, `product_type_id`, and `activity_id`. Since there was no time-based constraint, older jobs that the user completed *before* claiming the task were incorrectly linked to the new task, thereby prematurely completing the task without new effort.

## Acceptance Criteria

- [x] Ensure that EVE jobs are only linked if their expected completion time (`end_date`) is strictly after the task's claim date (`assigned_at` or `created_at`).
- [x] Allow no grace period (per user instruction) so that jobs finished before the exact claim moment are correctly excluded.

## Implementation Notes

- Added `cutoff = task.assigned_at or task.created_at`.
- Updated the `char_jobs` and `corp_jobs` queries in `industry_reforged/tasks/jobs.py` to filter using `Q(end_date__gte=cutoff) | Q(end_date__isnull=True)`.
- This strictly requires jobs to be actively running or finished *after* the task was claimed, preventing historical jobs from satisfying new task requirements.
