---
id: TASK-232
title: Fix v0.15.0 PyPI release failure
status: To Do
assignee: []
created_date: '2026-10-06 10:37'
labels: []
dependencies: []
ordinal: 408000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The previous release v0.15.0 failed to publish to PyPI because the versions in pyproject.toml and __init__.py were not updated from 0.14.4. This task will update those versions and re-run the release.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Versions are updated, Tag v0.15.0 is re-created, PyPI release completes successfully
<!-- AC:END -->
