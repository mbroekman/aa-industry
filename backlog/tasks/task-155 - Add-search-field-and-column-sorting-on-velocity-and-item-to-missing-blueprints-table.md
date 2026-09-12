---
id: TASK-155
title: >-
  Add search field and column sorting on velocity and item to missing blueprints
  table
status: Done
assignee: []
created_date: '2026-09-12 07:55'
updated_date: '2026-09-12 07:57'
labels: []
dependencies: []
ordinal: 152000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Upgrade missing blueprints list page (scanner_missing_bpos.html) with DataTables to provide search functionality and sorting on item name, velocity, and margin.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 DataTables initialized on missing blueprints table
- [ ] #2 Search input available to filter items
- [ ] #3 Sorting available on Item and Velocity columns
- [ ] #4 Optimized queryset with select_related
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Upgraded scanner_missing_bpos.html with DataTables for dynamic search and column sorting (item name, velocity, margin, found at date). Added query optimization select_related('eve_type') and URL test. All 150 tests passed.
<!-- SECTION:NOTES:END -->
