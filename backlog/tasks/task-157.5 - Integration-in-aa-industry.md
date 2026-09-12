---
id: TASK-157.5
title: Integration in aa-industry
status: To Do
assignee: []
created_date: '2026-09-12 11:46'
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
- [ ] #1 aa-industry basket evaluation successfully fetches targets from the ML service
<!-- AC:END -->
