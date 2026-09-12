---
id: TASK-126.7
title: 'Opportunity Scanner: Support Structure Selection'
status: Done
assignee: []
created_date: '2026-09-06 15:42'
updated_date: '2026-09-06 16:25'
labels: []
dependencies: []
parent_task_id: TASK-126
ordinal: 202000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Allow users to select a specific structure (Target Hub) in addition to/instead of a Region for the Opportunity Scanner. Update form, models, and celery tasks to accommodate this.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 OpportunityScanForm includes target_hub_id, MarketOpportunity model tracks target_hub, Celery task handles structure-specific profitability

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed target_hub_id structure names and items list in the basket edit view.

<!-- SECTION:NOTES:END -->
