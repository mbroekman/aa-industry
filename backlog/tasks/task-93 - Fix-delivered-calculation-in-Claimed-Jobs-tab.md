---
id: TASK-93
title: Fix delivered calculation in Claimed Jobs tab
status: Done
assignee: []
created_date: '2026-08-25 14:02'
updated_date: '2026-08-25 14:12'
labels: []
dependencies: []
ordinal: 83000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Fix issue #36 where the delivered quantity calculation misses overproduced items because linked_runs is capped at exactly the required amount.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 - Delivered amounts correctly reflect all runs linked to the job, including overproduction.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated char_jobs and corp_jobs queries to sum linked_runs and filter on remainder. Updated TaskJobLink creation to properly subtract remaining required_runs to allow job splitting.

<!-- SECTION:NOTES:END -->
