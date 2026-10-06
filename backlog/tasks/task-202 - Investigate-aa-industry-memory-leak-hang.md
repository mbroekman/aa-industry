---
id: TASK-202
title: Investigate aa-industry memory leak / hang
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-02 15:12'
updated_date: '2026-10-04 13:49'
labels: []
dependencies: []
ordinal: 378000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Version 0.14.1 of aa-industry causes the system to hang and MariaDB to run out of memory. Suspected infinite loop or memory leak.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Find root cause of the memory leak, Fix the bug causing the hang
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fixed infinite loops in models/orders.py and views/industrialist.py by adding visited sets for parent relationships (parent_order and bom_parent). This prevents MariaDB hangs on cyclical data.
<!-- SECTION:FINAL_SUMMARY:END -->
