---
id: TASK-215
title: Limit rigs based on structure type
status: Done
assignee: []
created_date: '2026-10-05 15:51'
updated_date: '2026-10-05 15:53'
labels: []
dependencies: []
ordinal: 391000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Filter rig options based on the size/type of the structure (e.g. XL structures can only fit XL rigs, M structures M rigs, etc.)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 When configuring a facility's rigs, the dropdown only shows rigs of the appropriate size class for that structure.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented frontend JavaScript filtering in manage_facility.html. The filter reads the type_id of the facility and hides/disables rig options that do not match the appropriate size class (M-, L-, XL-) in all rig formset dropdowns.
<!-- SECTION:NOTES:END -->
