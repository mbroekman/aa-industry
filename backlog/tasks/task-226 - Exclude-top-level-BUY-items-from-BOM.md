---
id: TASK-226
title: Exclude top-level BUY items from BOM
status: Done
assignee: []
created_date: '2026-10-06 08:24'
updated_date: '2026-10-06 08:24'
labels: []
dependencies: []
ordinal: 402000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Items that are on the order but cannot be built (or are set to BUY) currently show up in the Required Raw Materials list. Because they are top-level items, they should be excluded from the BOM since they are already listed on the order details.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Top-level order items that have no sub-materials are not added to the flattened BOM, Sub-components that are bought are still included in the BOM
- [ ] #2 1,2
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added is_top_level flag to _flatten in flatten_bom_tree. Top-level nodes with no sub-materials (like BUY items) are now ignored and won't pollute the Required Raw Materials list.
<!-- SECTION:NOTES:END -->
