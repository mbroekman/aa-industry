---
id: TASK-157.5
title: Integration in aa-industry
status: Done
assignee: []
created_date: '2026-09-12 11:46'
updated_date: '2026-09-12 12:10'
labels: []
dependencies: []
parent_task_id: TASK-157
ordinal: 159000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Write an Auth Celery task to periodically push data to /ingest and trigger /retrain. Adapt the evaluate_baskets module to call /forecast instead of using static target levels.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 aa-industry basket evaluation successfully fetches targets from the ML service
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated ai_manager.py with sync_market_data_to_ml_service task and patched evaluate_baskets to query /forecast API.
<!-- SECTION:NOTES:END -->
