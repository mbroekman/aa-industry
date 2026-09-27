---
id: TASK-180
title: Remove % sign from ME values in corporate pricing settings
status: Done
assignee: []
created_date: '2026-09-26 19:58'
updated_date: '2026-09-26 19:59'
labels: []
dependencies: []
ordinal: 356000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User reported that ME for T1 and T2 in corporate pricing settings has a % sign behind it, which is incorrect. ME should be displayed without the % sign.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 - ME values in corporate pricing settings do not have a % sign behind them
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Removed the '%' sign from the ME and TE values in director_config.html (both for Specific Item Rules and Corporate Pricing Configurations) as they are absolute efficiency levels, not percentages.
<!-- SECTION:NOTES:END -->
