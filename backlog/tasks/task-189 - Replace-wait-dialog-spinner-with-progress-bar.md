---
id: TASK-189
title: Replace wait dialog spinner with progress bar
status: Done
assignee: []
created_date: '2026-10-01 11:06'
updated_date: '2026-10-01 11:09'
labels: []
dependencies: []
ordinal: 365000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When opening an order, replace the spinning icon in the wait dialog with a progress bar.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Wait dialog uses a progress bar instead of a spinner when opening an order, Progress bar is visually integrated with the UI
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Replaced the spinning icon (spinner-border) with a Bootstrap animated progress bar in the global wait dialog (base.html), as well as in the shopping list wait modals and tree expansion overlays for consistency.
<!-- SECTION:NOTES:END -->
