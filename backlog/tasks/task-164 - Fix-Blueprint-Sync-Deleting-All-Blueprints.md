---
id: TASK-164
title: Fix Blueprint Sync Deleting All Blueprints
status: Done
assignee: []
created_date: '2026-09-12 19:12'
updated_date: '2026-09-12 19:12'
labels: []
dependencies: []
ordinal: 340000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Refactoring blueprint sync to support pagination changed the HTTPNotModified exception catch from returning early to breaking the loop. This causes the sync to process an empty list of blueprints and execute the cleanup deletion logic, deleting all blueprints in the database when receiving a 304 Not Modified from ESI.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Return early on HTTPNotModified during page 1. Skip deletion logic if any page fetch fails.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fixed the exception handler so HTTPNotModified on page 1 returns early, and added page_success flag to conditionally skip deletion logic on failure.

<!-- SECTION:NOTES:END -->
