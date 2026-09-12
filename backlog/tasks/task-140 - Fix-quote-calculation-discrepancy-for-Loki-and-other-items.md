---
id: TASK-140
title: Fix quote calculation discrepancy for Loki (and other items)
status: Done
assignee: []
created_date: '2026-09-07 17:15'
updated_date: '2026-09-07 17:24'
labels: []
dependencies: []
ordinal: 190000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User reported that a Loki job request quotes 625m while the BOM cost is 207m. The quote price calculation is incorrect.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Quote matches expected price
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed BOM cost calculation logic in pricing_engine.py. The get_recursive_bom_tree was improperly appending Blueprint / Reaction Formula costs (activity_id 5) into the flattened BOM, resulting in artificially massive 'true material cost' (e.g. 2.09 billion for a Loki). Added a check in calculate_bom_cost() > \_flatten() to exclude activity_id 5 nodes, which brings the true BOM cost of a Loki down to 261m, thereby fixing the grossly overinflated quote generation floor.

<!-- SECTION:NOTES:END -->
