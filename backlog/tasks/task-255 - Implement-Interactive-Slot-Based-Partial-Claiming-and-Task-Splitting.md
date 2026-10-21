---
id: TASK-255
title: Implement Interactive Slot-Based Partial Claiming and Task Splitting
status: Done
assignee: []
created_date: '2026-10-21 16:02'
labels: []
dependencies: []
ordinal: 429000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable industrialists to claim partial quantities of production tasks based on their available slots without Corptools dependency, with automatic task splitting and dynamic reward recalculation for both the claimed batch and remaining work.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Determine user manufacturing/industry slots live via Alliance Auth tokens/ESI and CharacterIndustryJob without Corptools dependency
- [x] #2 Provide Bootstrap 5 Claim Modal allowing user to specify slots to allocate and quantity/runs to claim
- [x] #3 Live preview of duration, runs per slot, and calculated builder reward in Claim Modal
- [x] #4 Split original task: create new task in IN_PRODUCTION for claimed batch and keep remaining quantity on Job Market as UNCLAIMED
- [x] #5 Accurately recalculate builder rewards for both claimed batch and remaining task
- [x] #6 Write discrete unit tests and verify 100% test pass rate
<!-- AC:END -->
