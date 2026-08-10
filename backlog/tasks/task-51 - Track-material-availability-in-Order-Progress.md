---
id: TASK-51
title: Track material availability in Order Progress
status: Done
assignee: []
created_date: '2026-08-09 07:06'
updated_date: '2026-08-09 07:09'
labels: []
dependencies: []
ordinal: 52000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Calculate and display the actual availability of completed materials for an order, subtracting materials that have already been consumed by higher-level tasks in production or completed.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Dashboard shows Available / Total instead of just Completed / Total
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated backend logic to calculate available items by subtracting items consumed by completed higher-level tasks. Updated UI to show Available / Total and added a tooltip with raw completed/consumed counts.

<!-- SECTION:NOTES:END -->
