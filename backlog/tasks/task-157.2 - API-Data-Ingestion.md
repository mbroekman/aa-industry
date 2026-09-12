---
id: TASK-157.2
title: API Data Ingestion
status: Done
assignee: []
created_date: '2026-09-12 11:46'
updated_date: '2026-09-12 12:08'
labels: []
dependencies: []
parent_task_id: TASK-157
ordinal: 170000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Setup schemas (Pydantic) and endpoints to receive and store data (historical transactions, pings, market prices) from Alliance Auth.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 /ingest endpoint can receive and validate payloads from Auth
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Created database.py with SQLite models, schemas.py for payloads, and routes.py with /ingest endpoint.
<!-- SECTION:NOTES:END -->
