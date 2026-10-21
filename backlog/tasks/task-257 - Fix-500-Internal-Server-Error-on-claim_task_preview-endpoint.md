---
id: TASK-257
title: Fix 500 Internal Server Error on claim_task_preview endpoint
status: Done
assignee: []
created_date: '2026-10-21 19:05'
labels:
  - bugfix
dependencies: []
ordinal: 431000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix 500 Internal Server Error returned by `claim_task_preview` endpoint (`/industry/industrialist/claim-preview/?task_id=11910&claim_quantity=432&allocated_slots=84`) when opening Claim Modal.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Inspect devauth gunicorn / django error log for task 11910 to identify exact root cause
- [x] #2 Resolve calculation or type issue in `claim_task_preview` view
- [x] #3 Add unit test reproducing the error condition
- [x] #4 Run pytest suite and ensure 100% test pass rate
- [x] #5 Deploy to devauth and verify claim-preview returns 200 OK
<!-- AC:END -->
