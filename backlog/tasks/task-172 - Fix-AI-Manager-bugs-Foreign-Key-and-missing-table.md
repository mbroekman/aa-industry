---
id: TASK-172
title: 'Fix AI Manager bugs: Foreign Key and missing table'
status: Done
assignee: []
created_date: '2026-09-14 15:56'
updated_date: '2026-09-14 15:57'
labels: []
dependencies: []
ordinal: 348000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix EveCorporationInfo foreign key reference in run_all_active_scanners (scanner.corporation.corporation_id instead of scanner.corporation_id) and missing table exception in sync_market_data_to_ml_service (catch Exception when querying OpTimer)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 - [ ] scan_market_opportunities receives the correct EVE corporation_id
- [x] #2 sync_market_data_to_ml_service degrades gracefully when OpTimer table is missing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed foreign key issue in run_all_active_scanners and gracefully degrade on OpTimer error in sync_market_data_to_ml_service
<!-- SECTION:NOTES:END -->
