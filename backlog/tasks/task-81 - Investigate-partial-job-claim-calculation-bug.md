---
id: TASK-81
title: Investigate partial job claim calculation bug
status: Done
assignee: []
created_date: '2026-08-23 12:04'
updated_date: '2026-08-23 12:13'
labels: []
dependencies: []
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Bug report: When claiming jobs for a requirement, if a job's output exceeds the remaining required amount, the system caps the claimed amount at the requirement (e.g. using 5 from a 13-run job to reach 200/200) but fails to account for the remaining runs (e.g. the 8 remaining runs are lost/not calculated as delivered or overdelivered). Expected behavior: The remaining runs should be tracked as overdelivery or made available for other claims, rather than disappearing from total delivered count.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Investigate the job claim logic, identify why partial claims lose remaining runs, and write a report explaining the current behavior and how it can be fixed.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Implemented Option 1: removed capping of runs_to_link in tasks/jobs.py so overdelivery is accurately recorded. Added eve_overdelivered_qty to tasks in views/industrialist.py and displayed the overdelivery in industrialist_dashboard.html

<!-- SECTION:NOTES:END -->
