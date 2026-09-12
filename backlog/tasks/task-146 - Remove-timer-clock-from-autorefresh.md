---
id: TASK-146
title: Remove timer clock from autorefresh
status: Done
assignee: []
created_date: '2026-09-09 15:37'
updated_date: '2026-09-09 15:47'
labels: []
dependencies: []
ordinal: 184000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User reports that the autorefresh with a timer clock is causing timeouts. Remove the visual clock, matching the implementation in the opportunity scanner.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Timer clock removed from all autorefresh implementations
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Removed the visual ticking timer clock from autorefresh_control.html and replaced setInterval with setTimeout to prevent excessive DOM updates and potential timeouts, bringing it in line with the AI manager dashboard autorefresh logic.
<!-- SECTION:NOTES:END -->
