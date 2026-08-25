---
id: TASK-86
title: Fix broken icon in inventory analysis
status: Done
assignee: []
created_date: '2026-08-24 21:12'
updated_date: '2026-08-24 21:14'
labels: []
dependencies: []
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The inventory analysis page has an incorrect blueprint icon (bp icon). Fix it.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 The inventory analysis displays the correct icon.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated `director_inventory.html` to use the `handleImageFallback` function instead of hardcoding the Tritanium icon placeholder on errors. This ensures that blueprint icons (which fail on `/icon?size=32`) will automatically retry on `/bp?size=32` and `/bpc?size=32`. Also added icons to the 'Restock Needed' alerts table for consistency.

<!-- SECTION:NOTES:END -->
