---
id: TASK-166
title: Auto-resolve Region from Hub
status: Done
assignee: []
created_date: '2026-09-13 13:20'
updated_date: '2026-09-13 13:21'
labels: []
dependencies: []
ordinal: 342000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

When a Basket or Scanner has a target_hub but no target_region_id, automatically look up the region from the Hub's solar system via EveUniverse rather than defaulting to The Forge.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Region is automatically resolved from target_hub if target_region_id is missing.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated evaluate_baskets and scan_market_opportunities to automatically look up Region ID from EveUniverse using the Hub's solar system ID.

<!-- SECTION:NOTES:END -->
