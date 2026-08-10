---
id: TASK-55
title: Add copy icon to item names in Build Steps
status: Done
assignee: []
created_date: '2026-08-09 10:51'
updated_date: '2026-08-09 10:51'
labels: []
dependencies: []
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Add a copy to clipboard icon next to the item name in the Build Steps summary table to easily paste it in-game.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Icon present and copies item name
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added a FontAwesome copy icon with an inline navigator.clipboard.writeText onClick handler that copies the item_type_name. Included visual feedback changing the icon to a green checkmark for 1.5s.

<!-- SECTION:NOTES:END -->
