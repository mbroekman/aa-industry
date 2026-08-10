---
id: TASK-28
title: Implement smart DataTables pagination across entire app
status: Done
assignee: []
created_date: '2026-08-07 07:09'
updated_date: '2026-08-07 07:10'
labels: []
dependencies: []
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Hide pagination controls and length menu for DataTables when records are less than or equal to 10, or when there is only 1 page. Ensure this UX improvement is applied to all DataTables in the application.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Smart pagination implemented globally or on all pages with DataTables

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Applied $.extend on $.fn.dataTable.defaults in base.html to globally hide dataTables_length if recordsTotal \<= 10 and dataTables_paginate if pages \<= 1. Verified this applies to all tables inheriting from base.html.

<!-- SECTION:NOTES:END -->
