---
id: TASK-60
title: Implement Research Dashboard
status: Done
assignee: []
created_date: '2026-08-10 12:12'
updated_date: '2026-08-10 12:12'
labels: ['enhancement', 'ui']
dependencies: []
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Create a new Research tab on the Personal Dashboard to display ME/TE/Copying Research (and optionally Invention) jobs across all of a user's characters. Currently, these jobs are mixed with manufacturing jobs in the Industry tab.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Add a "Research & Invention" tab to `personal_dashboard.html`.
- [x] #2 Separate research activities (ME, TE, Copying, Invention) from manufacturing in the Python view (`views/dashboard.py`).
- [x] #3 The new tab should display active and historical research jobs, clearly showing the character performing the job.
- [x] #4 Ensure that the table allows sorting and filtering, or is grouped by character for better visibility.

<!-- AC:END -->
