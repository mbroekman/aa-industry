---
id: TASK-128
title: Use EVE API for Sovereignty Hubs list
status: Done
assignee: []
created_date: '2026-09-05 18:07'
updated_date: '2026-09-05 18:13'
labels: []
dependencies: []
ordinal: 204000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Investigate and implement using the EVE API 'List Sovereignty Hubs' endpoint instead of the current method for listing hubs, as the current implementation is failing.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Identify current hub listing implementation; Identify EVE API endpoint for List Sovereignty Hubs; Implement API call to fetch hubs; Update UI to use new data source

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Replaced the target_hub dropdown with a target_hub_id integer field in BasketForm. Added logic to clean() to fetch the facility name from ESI /universe/stations/ or /universe/structures/ if it's not already in the database.

<!-- SECTION:NOTES:END -->
