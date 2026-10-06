---
id: TASK-235
title: Fix missing reaction blueprints in BOM
status: Done
assignee: []
created_date: '2026-10-06 13:34'
updated_date: '2026-10-06 13:51'
labels: []
dependencies: []
ordinal: 411000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The recursive BOM tree is missing some intermediate blueprints, specifically reaction formulas like Tungsten Carbide Reaction Formula. Ensure that when resolving intermediate materials, their corresponding blueprint/reaction formula is also included in the BOM.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reaction formulas and other intermediate blueprints are present in the recursive BOM.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed quotes.py logic to include activity_id=11 when determining if an item is buildable. This prevents reaction products from being misclassified as BUY items without a blueprint. Also improved the missing blueprints logic to completely exclude BPOs from the shortage list if the corporation already owns one, preventing false shortage reports for reaction formulas.
<!-- SECTION:NOTES:END -->
