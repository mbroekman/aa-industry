---
id: TASK-167
title: Replace native confirm with custom modal globally
status: Done
assignee: []
created_date: '2026-09-13 14:06'
updated_date: '2026-09-13 14:08'
labels: []
dependencies: []
ordinal: 343000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Extract actionModal to base.html and refactor all confirm() calls in templates.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 actionModal moved to base.html, JS globally available, native confirm() replaced in all dashboards

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Replaced standard browser confirm() dialogues with a custom Bootstrap modal globally.

<!-- SECTION:NOTES:END -->
