---
id: TASK-136
title: Investigate missing jobs for basket
status: Done
assignee: []
created_date: '2026-09-07 14:23'
updated_date: '2026-09-07 14:25'
labels: []
dependencies: []
ordinal: 133000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User reports a basket that should generate jobs is not generating them. Investigate the cause in the codebase.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Find root cause of missing jobs for baskets

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

The AI manager was creating ProductionTasks with status='DRAFT' instead of 'UNCLAIMED'. This meant that they were completely hidden from the user interface, which filters for 'UNCLAIMED' tasks. Also fixed ai_engine.py to check 'UNCLAIMED' and 'IN_PRODUCTION' instead of 'DRAFT' and 'ACTIVE' for checking availability.

<!-- SECTION:NOTES:END -->
