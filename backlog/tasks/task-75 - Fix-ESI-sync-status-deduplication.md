---
id: task-75
title: Fix ESI sync status deduplication ignoring delivered jobs
status: Done
created: 2026-08-17
---

# Fix ESI sync status deduplication ignoring delivered jobs

## Description

The user reported that jobs (like Avatars) remain stuck on "ready" in the app even after being delivered in-game and refreshing the data.
The root cause was found in `industry_reforged/tasks/jobs.py`: the sync loops over `include_completed=False` then `include_completed=True`. Due to ESI caching, the `False` request returns a stale "active" status, while the `True` request returns the accurate "delivered" status.
Because the deduplication loop `if job_id in seen_jobs: continue` kept the first occurrence, the "active" status from the first request was overriding the "delivered" status from the second request.

## Acceptance Criteria

- [x] Ensure that "delivered" and "cancelled" statuses are prioritized over "active" and "ready" statuses during job deduplication.
- [x] Fix the issue for both Character jobs and Corporation jobs sync tasks.
- [x] Ensure jobs that inexplicably drop off the ESI response are automatically marked as "delivered" to prevent them from being stuck.

## Implementation Notes

- Added a `status_priority` dictionary mapping `{"delivered": 0, "cancelled": 1, "ready": 2, "active": 3}`.
- Sorted `all_jobs` by this priority before running the `seen_jobs` deduplication loop.
- This guarantees the final state is always saved to the database.
- **Deep Analysis Update:** Discovered that ESI occasionally drops recently delivered jobs entirely from the `include_completed=True` payload.
- Added a self-healing cleanup routine in `update_corporation_jobs` and `update_character_jobs`: if we successfully fetch jobs (`len(all_jobs) > 0`) but active/ready jobs in our DB are missing from the `seen_jobs` set, we automatically update their status to `delivered` so they don't get stuck indefinitely.
