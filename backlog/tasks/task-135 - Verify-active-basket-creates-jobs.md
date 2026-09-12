---
id: TASK-135
title: Verify active basket creates jobs
status: Done
assignee: []
created_date: '2026-09-07 13:43'
updated_date: '2026-09-12 12:29'
labels: []
dependencies: []
ordinal: 195000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Run active basket evaluation and check for ProductionTask entries
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Active basket evaluation runs without errors; at least one ProductionTask created for active basket
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified via automated test test_evaluate_baskets_recreates_deleted_tasks_when_criteria_met.
<!-- SECTION:NOTES:END -->
