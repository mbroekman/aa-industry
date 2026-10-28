---
id: TASK-283
title: >-
  Inventory sync: keep stock at the structure, not the solar system; show spare
  stock on claimed jobs
status: Done
assignee: []
created_date: '2026-10-28 12:11'
updated_date: '2026-10-28 12:16'
labels: []
dependencies: []
ordinal: 457000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Asset root-location walk climbs past corp-owned structures to the solar system, so since 2026-09-07 all Foundry stock is stored under 9O-ORX (30004582) and order acceptance never deducts facility stock. Same walk in facilities.py. Also show spare stock (facility stock minus output already delivered for open order tasks) on claimed jobs so builders can build fewer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root-location walk stops at a structure/station and never resolves to a solar system ID
- [x] #2 Inventory and facility sync share one helper
- [x] #3 Claimed jobs show spare stock at the order facility, excluding output already delivered for open tasks of that type
- [x] #4 Tests cover nested containers in a corp-owned structure and the spare-stock calculation
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Root walk now stops before a solar system ID (utils/locations.resolve_root_location), used by inventory and facility sync. Spare stock: utils/spare_stock.annotate_spare_stock = facility stock minus delivered output of open tasks and unconsumed completed tasks of the same type; shown as a badge on Claimed Jobs. Existing orders are not recalculated.
<!-- SECTION:NOTES:END -->
