---
id: TASK-2
title: Split Large Modules
status: Done
assignee: []
created_date: '2026-07-29 16:32'
labels: []
dependencies: []
type: task
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

As the aa-industry-reforged plugin has grown, some files have become difficult to manage. Most notably, models.py (~37KB) and views/orders.py (~49KB) are too large.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Convert models.py into a models/ directory package
- [ ] #2 Split models logically into core, orders, pi, sde
- [ ] #3 Refactor views/orders.py into smaller files or class-based views
- [ ] #4 Update all import statements across the project
- [ ] #5 No single file exceeds ~1000 lines
- [ ] #6 tox tests and makemigrations run without errors

<!-- AC:END -->
