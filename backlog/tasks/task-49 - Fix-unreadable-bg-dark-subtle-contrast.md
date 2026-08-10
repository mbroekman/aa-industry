---
id: TASK-49
title: Fix unreadable bg-dark-subtle contrast
status: Done
assignee: []
created_date: '2026-08-09 06:53'
updated_date: '2026-08-09 06:54'
labels: []
dependencies: []
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Replace bg-dark-subtle with bg-dark across all templates to fix white text being unreadable on light gray backgrounds in the Darkly theme.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 bg-dark-subtle is removed from all templates
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Replaced all bg-dark-subtle classes with bg-dark in industrialist_dashboard.html, director_dashboard.html, and director_wallets.html to improve contrast with white text in the Darkly theme.

<!-- SECTION:NOTES:END -->
