---
id: TASK-183
title: Fix PyPI trusted publishing invalid-publisher error
status: Done
assignee: []
created_date: '2026-09-28 13:03'
updated_date: '2026-09-28 13:09'
labels: []
dependencies: []
type: bug
ordinal: 359000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GitHub Actions deployment to PyPI fails with `invalid-publisher: valid token, but no corresponding publisher (Publisher with matching claims was not found)`. Need to verify the GitHub Actions workflow configuration (environment, file name) against the PyPI Trusted Publisher settings.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. Identify the mismatch between GitHub Actions and PyPI. 2. Fix the workflow file if needed or provide instructions to update PyPI settings. 3. Ensure a successful release can be triggered.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated GitHub Actions release workflow environment from 'pypi-release' to 'release' to match PyPI configuration.
<!-- SECTION:NOTES:END -->
