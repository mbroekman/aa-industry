---
id: TASK-103
title: Fix material overcount on Industrialist Dashboard
status: Done
assignee: []
created_date: '2026-08-28 09:58'
updated_date: '2026-08-28 10:03'
labels: []
dependencies: []
type: bug
ordinal: 93000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Fixes a bug where completed/consumed tasks artificially inflate the 'Claimed' (to_build) counts when new jobs for the same material are added. The fix adjusts how the my_claimed_summary is aggregated in views/industrialist.py by filtering out fully consumed/completed tasks from the 'Active' totals, preventing old job quantities from ballooning the visible numbers.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Dashboard shows correct 'Claimed' counts when new jobs are added while old jobs for the same material are partially or fully consumed

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Applied the material aggregation fix in views/industrialist.py to filter out fully consumed/completed tasks from the 'Active' totals.

<!-- SECTION:NOTES:END -->
