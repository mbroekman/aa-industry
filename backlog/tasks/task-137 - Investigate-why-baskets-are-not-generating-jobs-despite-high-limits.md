---
id: TASK-137
title: Investigate why baskets are not generating jobs despite high limits
status: Done
assignee: []
created_date: '2026-09-07 16:48'
updated_date: '2026-09-07 16:49'
labels: []
dependencies: []
ordinal: 193000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User reports that even after fixing the DRAFT status issue, setting basket limits high still does not result in jobs being generated. Need to investigate if baskets are being evaluated, and if so, why they are failing the checks.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Find root cause of missing basket jobs and fix it

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

calculate_profitability in ai_engine.py was looking for 'sell_price' and 'adjusted_price' keys from get_detailed_prices(). However, get_detailed_prices() returns 'original_jita_price' and 'final_price'. This caused the margin to always be calculated as 0.0%, meaning it was always skipped because it was below the minimum margin. I updated calculate_profitability to correctly use 'final_price', and to separately query EveMarketPrice for 'adjusted_price'.

<!-- SECTION:NOTES:END -->
