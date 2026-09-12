---
id: TASK-143
title: Fix AI Manager Celery Beat schedule in README
status: Done
assignee: []
created_date: '2026-09-07 20:10'
updated_date: '2026-09-07 20:11'
labels: []
dependencies: []
ordinal: 187000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The celery beat schedule for AI Market Manager in README.md is incomplete. It's missing run_all_active_scanners and evaluate_baskets is incorrectly scheduled instead of run_all_active_baskets (which respects the interval settings). This needs to be corrected in the setup documentation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. Replace evaluate_baskets with run_all_active_baskets in CELERYBEAT_SCHEDULE; 2. Add run_all_active_scanners to CELERYBEAT_SCHEDULE
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated README.md to use run_all_active_baskets instead of evaluate_baskets, and added run_all_active_scanners to the celery beat schedule.
<!-- SECTION:NOTES:END -->
