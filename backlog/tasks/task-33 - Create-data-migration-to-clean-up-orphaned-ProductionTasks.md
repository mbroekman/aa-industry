---
id: TASK-33
title: Create data migration to clean up orphaned ProductionTasks
status: Done
assignee: []
created_date: '2026-08-07 07:45'
updated_date: '2026-08-07 07:46'
labels: []
dependencies: []
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

A data migration is needed to clean up any orphaned ProductionTasks (tasks with created_from_order=None) in the test/production environment when the new release is deployed, to fix the issue where deleting a split order left jobs behind.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Migration file created, migration safely deletes orphaned tasks

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Created data migration 0040_cleanup_orphaned_tasks to automatically clean up orphaned ProductionTasks when deployed to other environments.

<!-- SECTION:NOTES:END -->
