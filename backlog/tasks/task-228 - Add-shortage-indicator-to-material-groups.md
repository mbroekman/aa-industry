---
id: TASK-228
title: Add shortage indicator to material groups
status: Done
assignee: []
created_date: '2026-10-06 08:42'
updated_date: '2026-10-06 08:42'
labels: []
dependencies: []
ordinal: 404000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Since material groups are collapsed by default, users cannot see which groups have stock shortages. Add a visual indicator to the group header if any underlying item has a shortage.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Group headers display a shortage badge if any child item has a shortage, Badge updates dynamically, Shortage is determined by corp_stock < quantity
- [ ] #2 1,2,3
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added data-shortage attributes to rows using Django template logic. Added a post-draw loop in Javascript to check if any child of a group has a shortage, and if so, appends a red 'Shortage' badge to the group header.
<!-- SECTION:NOTES:END -->
