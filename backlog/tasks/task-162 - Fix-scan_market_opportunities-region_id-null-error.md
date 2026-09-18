---
id: TASK-162
title: Fix scan_market_opportunities region_id null error
status: Done
assignee: []
created_date: '2026-09-12 18:30'
updated_date: '2026-09-12 18:30'
labels: []
dependencies: []
ordinal: 338000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When a scanner has no target_region_id, the celery task crashes because it tries to save a MarketOpportunity with a null region_id.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Fallback to 10000002 when region_id is None
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added fallback to 10000002
<!-- SECTION:NOTES:END -->
