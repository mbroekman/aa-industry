---
id: TASK-17
title: Fix Python 3.13 test failure
status: Done
assignee: []
created_date: '2026-08-04 21:12'
updated_date: '2026-08-04 21:15'
labels: []
dependencies: []
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Onderzoek en verhelp de python 3.13 test failure en/of test coverage issues in GitHub Actions.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Tests en coverage werken correct op Python 3.13 in GitHub Actions

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Opgelost: (1) tox-gh-actions configuratie toegevoegd aan tox.ini zodat tox niet faalt op ontbrekende interpreters, (2) database vereiste weggehaald uit Codecov stap in automated-checks.yml zodat coverage weer succesvol wordt geüpload.

<!-- SECTION:NOTES:END -->
