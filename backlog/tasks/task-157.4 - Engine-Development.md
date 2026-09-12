---
id: TASK-157.4
title: Engine Development
status: Done
assignee: []
created_date: '2026-09-12 11:46'
updated_date: '2026-09-12 12:09'
labels: []
dependencies: []
parent_task_id: TASK-157
ordinal: 158000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement ROP calculations using blueprint build times and flexible margins.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Engine logic correctly outputs ROP and build quantities based on forecast and current stock
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented engine.py to calculate ROP and qty_to_build using the LightGBM model, and connected to /forecast endpoint.
<!-- SECTION:NOTES:END -->
