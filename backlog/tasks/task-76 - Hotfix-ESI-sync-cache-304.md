---
id: task-76
title: Hotfix ESI sync cache 304 skipping cleanup
status: Done
created: 2026-08-17
---

# Hotfix ESI sync cache 304 skipping cleanup

## Description

The aggressive self-healing cleanup mechanism introduced in TASK-75 relied on `len(all_jobs) > 0` to determine if it was safe to prune stale jobs from the database.
However, this check failed in two specific scenarios:

1. When ESI returned a `304 Not Modified` cached response, `all_jobs` would be empty, causing the cleanup to be completely skipped even if jobs were stuck.
1. If a user or corporation legitimately had exactly 0 active or recently completed jobs, ESI would return `200 OK` with an empty list. The cleanup would again be skipped due to `len(all_jobs) > 0`, stranding their final job indefinitely.

## Acceptance Criteria

- [x] Ensure that aggressive cleanup runs when ESI is successfully polled, even if the user has 0 jobs.
- [x] Ensure that aggressive cleanup is safely skipped if an `HTTPNotModified` (304) is received (to prevent wiping all jobs due to a cache hit).
- [x] Update logic to use a successful HTTP fetch counter instead of `len(all_jobs)`.

## Implementation Notes

- Replaced the `len(all_jobs) > 0` check in `industry_reforged/tasks/jobs.py` with a new `successful_fetches = 0` counter.
- For character jobs, `successful_fetches` must equal 2 (both `include_completed=False` and `True` must return 200 OK without errors or 304s).
- For corporation jobs, `successful_fetches` is incremented for each successful full-pagination run.
- If the required endpoints return 200 OK, the aggressive cleanup runs, reliably updating any dropped jobs to `delivered`.
