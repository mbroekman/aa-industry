---
id: TASK-94
title: Show output quantity in Corporate Jobs tab
status: Done
assignee: []
created_date: '2026-08-25 14:03'
updated_date: '2026-08-25 14:12'
labels: []
dependencies: []
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Feature request #33: differentiate between runs and output in Corporate Jobs. Show the number of runs and underneath the expected output quantity.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 - Corporate jobs list shows expected output quantity beneath the runs.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added expected_output property to CharacterIndustryJob and CorporationIndustryJob models. Updated industrialist_dashboard.html tables to show the expected_output below the runs.

<!-- SECTION:NOTES:END -->
