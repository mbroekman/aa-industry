---
id: TASK-97
title: Show corp jobs in personal industry jobs view
status: Done
assignee: []
created_date: '2026-08-26 19:54'
updated_date: '2026-08-26 20:00'
labels: []
dependencies: []
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Update the personal industry jobs view to include corp jobs started by the user. Add a filter to toggle between 'All', 'Personal only', and 'Corp only'.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Corp jobs started by user are fetched and displayed. Filter dropdown/buttons exist to select all/personal/corp. Filtering works correctly.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added corp jobs installed by characters to the Personal dashboard. Added Ownership dropdown to both Manufacturing and Research tabs. Appended job_type badge and column. Updated javascript DataTables and research rows to handle filtering.

<!-- SECTION:NOTES:END -->
