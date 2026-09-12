---
id: TASK-145
title: Investigate auto-refresh crash on test server
status: Done
assignee: []
created_date: '2026-09-08 19:20'
updated_date: '2026-09-08 19:31'
labels: []
dependencies: []
ordinal: 185000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User reports that the auto-refresh functionality is causing a crash on the test server, but not locally. This started occurring after adding request.session.modified = True to the dashboard views. Need to investigate root cause.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Root cause identified and resolved
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed personal dashboard unbounded query memory exhaustion by limiting historical jobs to the latest 250 records and filtering directly in the database.
<!-- SECTION:NOTES:END -->
