---
id: TASK-59
title: Add confirmation dialog for deleting orders
status: Done
assignee: []
created_date: '2026-08-09 11:58'
updated_date: '2026-08-09 12:01'
labels: []
dependencies: []
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Add a confirmation dialog to the Delete Order button in the Director Control Panel.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Delete button triggers confirmation dialog
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated director_dashboard.html Javascript to use event delegation (document.body.addEventListener) for '.require-confirmation' forms and '.payment-modal-btn' buttons so that they correctly bind to elements loaded dynamically by DataTables via AJAX. The delete confirmation dialog will now correctly display for orders in the CP.

<!-- SECTION:NOTES:END -->
