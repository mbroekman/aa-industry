---
id: TASK-197
title: Investigate why corp stock is not being updated
status: Done
assignee: []
created_date: '2026-10-01 15:27'
updated_date: '2026-10-01 15:41'
labels: []
dependencies: []
ordinal: 373000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user reports that the corporation stock/inventory is not being updated. Need to investigate the sync logic and celery tasks responsible for updating corporate assets.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root cause for corp stock not updating is found and fixed
- [x] #2 Corporate stock syncs successfully
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added missing ESI pagination to GetCorporationsCorporationIdAssets endpoints in inventory.py and facilities.py. ESI returns a max of 1000 items per page, so corporations with more assets would not have their stock synced properly.
<!-- SECTION:NOTES:END -->
