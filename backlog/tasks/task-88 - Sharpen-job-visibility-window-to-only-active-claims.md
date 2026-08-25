---
id: TASK-88
title: Sharpen job visibility window to only active claims
status: Done
assignee: []
created_date: '2026-08-25 05:51'
updated_date: '2026-08-25 05:51'
labels: []
dependencies: []
ordinal: 78000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Update my_eve_jobs to only use the assigned_at date of currently active claims (not completed tasks) for the time window filter.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Only IN_PRODUCTION tasks are considered for oldest_claim_date.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated oldest_claim_date calculation to only look at IN_PRODUCTION tasks, explicitly ignoring completed tasks. This sharpens the job visibility window for 'My Corporate Jobs'.

<!-- SECTION:NOTES:END -->
