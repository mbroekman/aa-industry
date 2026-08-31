---
id: TASK-109
title: Load all rigs available on demand
status: Done
assignee: []
created_date: '2026-08-31 09:17'
updated_date: '2026-08-31 09:59'
labels: []
dependencies: []
ordinal: 99000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

GitHub Issue #43: Initial load of all rigs available in the game and possibility to start a job to reload all rigs by using a button in the CP configuration page.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 A button is added to the CP configuration page to trigger a rig reload job
- [ ] #2 The job successfully loads all available rigs in the game (not just a seeded list)

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added task_sync_all_rigs celery task, director_config_sync_rigs view, and integrated the sync button into director_config.html. It parses ME/TE bonuses from rig names automatically.

<!-- SECTION:NOTES:END -->
