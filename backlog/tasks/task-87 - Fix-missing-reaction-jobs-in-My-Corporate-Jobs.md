---
id: TASK-87
title: Fix missing reaction jobs in My Corporate Jobs
status: Done
assignee: []
created_date: '2026-08-25 05:46'
updated_date: '2026-08-25 05:49'
labels: []
dependencies: []
ordinal: 77000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Reaction jobs are missing from the 'My Corporate Jobs' (My EVE Jobs) tab. The intention is to show all jobs that fall in the period from the date of a claimed job, rather than just directly linked active tasks.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Reaction jobs are visible in 'My Corporate Jobs' again based on the time window of claimed jobs.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated `my_eve_jobs` query in `industrialist.py` to show all EVE jobs installed by the user that started after the oldest `assigned_at` date of their currently visible claimed tasks (active + recent completed). This ensures Reaction jobs are visible in 'My Corporate Jobs' as long as they fall in the time window of a claimed task, while still hiding old unrelated jobs.

<!-- SECTION:NOTES:END -->
