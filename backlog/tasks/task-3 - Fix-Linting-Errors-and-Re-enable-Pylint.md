______________________________________________________________________

## id: TASK-3 title: Fix Linting Errors and Re-enable Pylint status: Done assignee: [] created_date: '2026-07-29 16:32' labels: [] dependencies: [] type: chore ordinal: 3000

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The project has a well-configured pre-commit, but some tools are catching errors or have been disabled. Fix flake8 errors, commit formatting changes, and re-enable pylint.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Fix remaining flake8 errors in tasks/utils.py
- [ ] #2 Commit auto-formatted changes from black and isort
- [ ] #3 Uncomment pylint in .pre-commit-config.yaml
- [ ] #4 Resolve or suppress pylint warnings
- [ ] #5 pre-commit run --all-files passes completely

<!-- AC:END -->
