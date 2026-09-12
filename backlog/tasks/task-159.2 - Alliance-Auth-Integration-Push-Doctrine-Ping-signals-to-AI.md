---
id: TASK-159.2
title: 'Alliance Auth Integration: Push Doctrine/Ping signals to AI'
status: Done
assignee: []
created_date: '2026-09-12 16:24'
updated_date: '2026-09-12 16:47'
labels: []
dependencies: []
parent_task_id: TASK-159
type: task
ordinal: 164000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Modify tasks/ai_manager.py to push ping history to /ingest
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Modified ai_manager.py to query OpTimer and send pings. Extract type_id from doctrine string by searching for Ship types.
<!-- SECTION:NOTES:END -->
