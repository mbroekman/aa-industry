---
id: TASK-210
title: Investigate missing Tatara facility
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-04 15:47'
updated_date: '2026-10-04 15:51'
labels: []
dependencies: []
ordinal: 386000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User added a Tatara as default for reactions, but it is not showing up in the list of facilities and cannot be re-added.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root cause found and resolved
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The form for adding a new facility didn't explicitly set the 'owner_id' for manually added structures. As a result, the facility was saved with 'owner_id=None' and didn't appear in the corporate table. Also, since it was marked as a 'production facility', it was excluded from the dropdown to prevent duplicates. Modified 'add_facility' in facilities.py to inject the 'owner_id' before saving. Migrated the existing broken Tatara.
<!-- SECTION:NOTES:END -->
