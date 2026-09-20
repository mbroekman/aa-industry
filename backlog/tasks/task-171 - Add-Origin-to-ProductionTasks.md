---
id: TASK-171
title: Add Origin to ProductionTasks
status: Done
assignee: []
created_date: '2026-09-14 15:29'
updated_date: '2026-09-14 15:29'
labels: []
dependencies: []
ordinal: 347000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Voeg een Origin kolom toe aan de jobs in de interface om te zien waar ze vandaan komen (BASKET, MANUAL, etc.).

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Origin field added to ProductionTask model\\nOrigin populated on creation\\nOrigin visible and filterable in datatables UI

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Created Origin column for ProductionTask. Added BASKET, MANUAL, MEMBER_ORDER, BOM, BLUEPRINT tags to all backend generation points. Updated datatables.py to return origin and allow search. Updated Director and Industrialist dashboards to render the Origin column.

<!-- SECTION:NOTES:END -->
