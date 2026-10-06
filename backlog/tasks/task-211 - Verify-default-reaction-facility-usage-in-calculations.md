---
id: TASK-211
title: Verify default reaction facility usage in calculations
status: Done
assignee: []
created_date: '2026-10-04 16:05'
updated_date: '2026-10-04 16:07'
labels: []
dependencies: []
ordinal: 387000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure that BOM/pricing calculations correctly use the default reaction facility for reaction tasks instead of the standard manufacturing facility.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Code inspected and verified. Fix applied if needed.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The BOM calculation logic correctly attempts to use the 'is_default_reaction' facility when the activity_id == 11 (Reaction). However, the query was missing an 'owner_id' filter, meaning it could fetch a reaction facility belonging to a different corporation if there were multiple registered. Fixed this by including the corporation filter.
<!-- SECTION:NOTES:END -->
