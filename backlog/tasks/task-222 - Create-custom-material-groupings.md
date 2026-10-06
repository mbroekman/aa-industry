---
id: TASK-222
title: Create custom material groupings
status: Done
assignee: []
created_date: '2026-10-06 07:57'
updated_date: '2026-10-06 07:57'
labels: []
dependencies: []
ordinal: 398000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Map EVE SDE groups to user-friendly custom groups like Moon Goo, Gases, Reaction Materials, and PI, to reduce clutter in the UI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Materials are grouped into logical buckets, Unmapped materials fallback to their SDE group name
- [ ] #2 1,2
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added custom mapping logic in bom_engine.py to group materials into 'Moon Goo', 'Reaction Materials', 'Gases', 'Planetary Commodities', 'Ice Products', 'Salvage', 'Components' and 'Minerals'. Anything else falls back to its default SDE group name.
<!-- SECTION:NOTES:END -->
