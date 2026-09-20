---
id: TASK-165
title: Fix Basket market_stock region fallback
status: Done
assignee: []
created_date: '2026-09-13 13:12'
updated_date: '2026-09-13 13:13'
labels: []
dependencies: []
ordinal: 341000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

evaluate_baskets does not check market_stock if Basket.target_region_id is not set. It should fallback to 10000002 (Jita) just like scan_market_opportunities.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 evaluate_baskets fetches market stock even if target_region_id is blank, by falling back to 10000002

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated evaluate_baskets to fallback to region_id 10000002 when Basket.target_region_id is blank. This fixes the issue where market stock returned 0 for missing region IDs.

<!-- SECTION:NOTES:END -->
