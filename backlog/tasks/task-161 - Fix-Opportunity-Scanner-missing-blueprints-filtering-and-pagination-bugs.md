---
id: TASK-161
title: Fix Opportunity Scanner missing blueprints filtering and pagination bugs
status: Done
assignee: []
created_date: '2026-09-12 17:35'
updated_date: '2026-09-12 17:38'
labels: []
dependencies: []
ordinal: 337000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1. The Opportunity Scanner incorrectly uses the EVE Corporation ID to filter CorpBlueprint by database ID, causing all items to be marked as missing. 2. ESI Blueprint synchronization lacks pagination, limiting sync to 1000 items. 3. CorpBlueprint is_original property incorrectly identifies BPCs as BPOs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Scanner filters CorpBlueprint using corporation__corporation_id, ESI blueprint sync fetches all pages, CorpBlueprint is_original returns False for BPCs (quantity == -2)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated ai_manager to query CorpBlueprint using corporation__corporation_id instead of corporation_id, which fixed missing blueprints scanner logic. Updated blueprints.py to use a pagination loop for ESI get blueprints call. Fixed is_original to only trigger for BPOs.
<!-- SECTION:NOTES:END -->
