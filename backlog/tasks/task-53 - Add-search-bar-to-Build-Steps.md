---
id: TASK-53
title: Add search bar to Build Steps
status: Done
assignee: []
created_date: '2026-08-09 07:32'
updated_date: '2026-08-09 07:32'
labels: []
dependencies: []
ordinal: 54000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Add a text search input to the Build Steps (Summary) tab and update the javascript filter to apply both the status dropdown and the text search.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Search bar filters rows by text
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Replaced the empty dt-search-placeholder with a custom input-group containing a search icon and text input. Updated filterSummaryTable() javascript to filter rows where the text content matches the search string, combined with the active/completed dropdown filter.

<!-- SECTION:NOTES:END -->
