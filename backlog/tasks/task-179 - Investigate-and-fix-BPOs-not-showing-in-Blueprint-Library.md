---
id: TASK-179
title: Investigate and fix BPOs not showing in Blueprint Library
status: Done
assignee: []
created_date: '2026-09-26 19:31'
updated_date: '2026-09-26 19:36'
labels: []
dependencies: []
ordinal: 355000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User reported that BPOs (Original Blueprints) are no longer showing up in the blueprint library.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 - BPOs are visible again in the BP library
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added a filter to easily switch between BPOs and BPCs. BPOs were always in the database (8900+), but they were buried among 17000+ BPCs and previously all blueprints were wrongly identified as BPOs before September 12.
<!-- SECTION:NOTES:END -->
