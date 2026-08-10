---
id: TASK-47
title: Remove javascript tree logic from industrialist dashboard
status: Done
assignee: []
created_date: '2026-08-09 06:43'
updated_date: '2026-08-09 06:44'
labels: []
dependencies: []
ordinal: 48000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Remove the DataTables drawCallback and tableState logic that tries to build trees and prepends buttons or invisible spans to the item column.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 No invisible spans are prepended, rows are perfectly flush left
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Removed the tableState variables, drawCallback tree builder logic, and obsolete javascript functions that dynamically injected 24px wide spans and minus buttons to the item column on load.

<!-- SECTION:NOTES:END -->
