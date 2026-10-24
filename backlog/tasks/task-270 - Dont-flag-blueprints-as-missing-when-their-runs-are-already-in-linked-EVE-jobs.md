---
id: TASK-270
title: >-
  Don't flag blueprints as missing when their runs are already in linked EVE
  jobs
status: Done
assignee: []
created_date: '2026-10-24 17:14'
updated_date: '2026-10-24 17:17'
labels:
  - bug
dependencies: []
priority: high
ordinal: 444000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Order view's Missing Blueprints analysis only counts COMPLETED tasks as built. When a member has already run (or is running) the job in EVE but hasn't marked the task complete, the BPC runs are consumed so corp stock drops, and the page reports a shortage for a product that is already built. Seen on devauth order #279: Capital Ship Maintenance Bay task IN_PRODUCTION with 61 delivered runs linked, reported 53 runs missing. User decision: if parts of an order are already built, their blueprint is not missing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Runs of EVE jobs linked to the order's not-yet-completed tasks (active, paused, ready, delivered) count as completed blueprint runs
- [x] #2 Cancelled/reverted linked jobs don't count (the blueprint comes back)
- [x] #3 Runs aren't double-counted for COMPLETED tasks that also have linked jobs
- [x] #4 Tests cover the above; full suite green
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Root cause confirmed on devauth order #279: Capital Ship Maintenance Bay task IN_PRODUCTION with 40+21 delivered runs linked, reported 53 runs short. Extracted run counting into views/orders/quotes.py::_built_blueprint_runs(); COMPLETED tasks count by quantity/yield, unfinished tasks count linked_runs of jobs in active/paused/ready/delivered. Tests: test_missing_blueprints.py (10). A task with consumed BPC runs but no linked EVE job (e.g. #279 Jump Bridge Array) still shows missing: nothing proves it was built until link_orphaned_jobs links the job.
<!-- SECTION:NOTES:END -->
