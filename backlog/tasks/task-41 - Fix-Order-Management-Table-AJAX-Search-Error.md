---
id: TASK-41
title: Fix Order Management Table AJAX Search Error
status: Done
assignee: []
created_date: '2026-08-09 06:04'
updated_date: '2026-08-09 06:05'
labels: []
dependencies: []
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Fix 500 server error when searching in the active member orders table in the CP (order-management-table).

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Search function in order management table works without Ajax error
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed typo in MemberOrder search filter in datatables.py where it was trying to query corporation\_\_corporation_name instead of character\_\_corporation_name.

<!-- SECTION:NOTES:END -->
