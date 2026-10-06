---
id: TASK-207
title: Investigate missing base materials in BOM calculations
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-04 14:53'
updated_date: '2026-10-04 15:04'
labels: []
dependencies: []
ordinal: 383000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate why base materials like Mexallon are not correctly displaying for large jobs (e.g., Erebus build). Write a report with the findings to prepare for a fix.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Investigation report is written and saved as an artifact
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Investigated BOM depth issue. The recursive BOM correctly calculates depths down to Mexallon, but the shopping list and aggregated views use calculate_tasks_bom and calculate_order_bom which only calculate a single depth. A report has been saved outlining the refactor needed to fix this.
<!-- SECTION:FINAL_SUMMARY:END -->
