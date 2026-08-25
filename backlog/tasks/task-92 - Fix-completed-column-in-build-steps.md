---
id: TASK-92
title: Fix completed column in build steps
status: Done
assignee: []
created_date: '2026-08-25 13:55'
updated_date: '2026-08-25 13:56'
labels: []
dependencies: []
ordinal: 82000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The 'completed' column in build steps is not being updated with the amounts that have been produced from claimed jobs for the main items.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 - Completed column in build steps correctly reflects produced quantities from Eve jobs

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated 'completed' quantity calculation in industrialist.py to include eve_delivered, correctly reflecting the items produced by completed Eve Jobs in the Build Steps.

<!-- SECTION:NOTES:END -->
