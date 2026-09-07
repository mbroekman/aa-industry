---
id: TASK-110
title: Fix calculation of amount against runs
status: Done
assignee: []
created_date: '2026-08-31 09:17'
updated_date: '2026-09-05 12:25'
labels: []
dependencies: []
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

GitHub Issue #38: Calculation of amount against runs is still not correct.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Investigate the calculation logic for amounts vs runs
- [x] #2 Fix the logic so the calculated output matches expectations

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Changed 'int()' to 'math.ceil()' in industry_reforged/tasks/jobs.py when calculating required_runs from quantity / portion_size

<!-- SECTION:NOTES:END -->
