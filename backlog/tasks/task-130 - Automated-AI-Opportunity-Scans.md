---
id: TASK-130
title: Automated AI Opportunity Scans
status: Done
assignee: []
created_date: '2026-09-06 17:10'
updated_date: '2026-09-06 17:16'
labels: []
dependencies: []
ordinal: 127000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Schedule Opportunity Scanners to run periodically and allow them to automatically add discovered opportunities to a Basket.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 OpportunityScanner has auto_add_basket and stock_days fields, scan_market_opportunities auto-adds BasketItems if thresholds are met, A periodic celery task runs all active scanners daily.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added auto_add_basket and target_stock_days to OpportunityScanner. Updated scan_market_opportunities to automatically create BasketItems when thresholds are met. Registered run_all_active_scanners celery beat task.

<!-- SECTION:NOTES:END -->
