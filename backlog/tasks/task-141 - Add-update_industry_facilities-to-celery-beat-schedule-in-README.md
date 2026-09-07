---
id: TASK-141
title: Add update_industry_facilities to celery beat schedule in README
status: Done
assignee: []
created_date: '2026-09-07 19:30'
updated_date: '2026-09-07 19:30'
labels: []
dependencies: []
ordinal: 138000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The update_industry_facilities celery task is missing from the scheduled background jobs in the README.md instructions. It needs to be added so users will configure it in their local.py, allowing facility resolution for AI manager and hubs to work properly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. update_industry_facilities is present in the CELERYBEAT_SCHEDULE block in README.md; 2. The task is scheduled to run periodically (e.g. daily or hourly).
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added industry_update_facilities task to CELERYBEAT_SCHEDULE in README.md
<!-- SECTION:NOTES:END -->
