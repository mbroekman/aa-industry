---
id: TASK-159.1
title: AI Database & Ingestion updates for Pings/Doctrines
status: Done
assignee: []
created_date: '2026-09-12 16:24'
updated_date: '2026-09-12 16:47'
labels: []
dependencies: []
parent_task_id: TASK-159
type: task
ordinal: 163000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add Ping/Doctrine event models to database.py
- [x] #2 /ingest accepts new payloads
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added PingEvent and DoctrineEvent to database.py and updated /ingest route in routes.py with matching schemas.
<!-- SECTION:NOTES:END -->
