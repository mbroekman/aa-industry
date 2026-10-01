---
id: TASK-201
title: Fix missing corporate inventory due to ESI pagination cache
status: Done
assignee: []
created_date: '2026-10-01 18:58'
updated_date: '2026-10-01 18:58'
labels: []
dependencies: []
ordinal: 377000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The recently added pagination logic for ESI corporate assets/jobs fails when ESI returns a 304 Not Modified for page=1, causing the task to abort silently and never update the database.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 - [ ] use_etag=False is passed to paginated .results() calls to prevent HTTPNotModified exceptions aborting the loop
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed the missing pagination cache bug by setting use_etag=False in paginated .results() calls
<!-- SECTION:NOTES:END -->
