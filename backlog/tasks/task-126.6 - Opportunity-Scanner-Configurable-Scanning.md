---
id: TASK-126.6
title: Opportunity Scanner Configurable Scanning
status: Done
assignee: []
created_date: '2026-09-06 12:53'
updated_date: '2026-09-06 12:56'
labels: []
dependencies: []
parent_task_id: TASK-126
ordinal: 124000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Allow users to select a Region and multiple Market Groups to scan for opportunities. Stores results in a new MarketOpportunity model and displays them in a UI.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Region selector works, Market Group selector works, Celery task scans correctly, UI displays opportunities, User can add to basket from UI

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Implemented MarketOpportunity model and migration. Created OpportunityScanForm allowing selection of Corp, Region, and EVE Item Categories. Added scan_market_opportunities celery task. Updated views and templates to display form and datatable.

<!-- SECTION:NOTES:END -->
