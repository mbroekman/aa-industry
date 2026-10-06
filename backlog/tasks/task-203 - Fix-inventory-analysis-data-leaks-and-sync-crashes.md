---
id: TASK-203
title: Fix inventory analysis data leaks and sync crashes
status: Done
assignee: []
created_date: '2026-10-03 17:42'
updated_date: '2026-10-03 17:53'
labels: []
dependencies: []
ordinal: 379000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1. Fix the bug where task_sync_corp_inventory crashes and wipes inventory when an unknown EveType is encountered. 2. Fix the data leaks in director_inventory and director_config where inventory, configs, and tasks from all corporations are merged together due to missing corporation filtering.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 1. Ensure ensure_eve_type returns boolean success. 2. Skip assets in sync loop if type fails to resolve. 3. Filter CorpInventory, CorpItemConfig, ProductionTask, and IndustryFacility by corporation in director_inventory view. 4. Filter configs by corporation in director_config view.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed the fatal IntegrityError crash in task_sync_corp_inventory by ensuring ensure_eve_type returns a boolean and skipping assets that fail to resolve. Fixed the data leaks in director_inventory and director_config by filtering all inventory, configs, facilities, and tasks by the current corporation.

\n- Follow-up: Reverted the 'corporation' filter on ProductionTask since it does not have a corporation field and is meant to act as a global production pool. This resolves the FieldError on the inventory analytics view.
<!-- SECTION:NOTES:END -->
