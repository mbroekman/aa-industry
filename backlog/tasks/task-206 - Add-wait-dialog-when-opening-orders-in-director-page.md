---
id: TASK-206
title: Add wait dialog when opening orders in director page
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-04 14:42'
updated_date: '2026-10-04 14:43'
labels: []
dependencies: []
ordinal: 382000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a wait dialog (loader overlay) when clicking on orders in the director page.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Wait dialog is shown when clicking to open an order from the director page
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Changed event listeners in base.html to use event delegation so that dynamic DataTables links with the show-loader class trigger the wait dialog.
<!-- SECTION:FINAL_SUMMARY:END -->
