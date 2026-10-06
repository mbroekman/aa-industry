---
id: TASK-208
title: Refactor BOM material aggregation to flatten recursive tree
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-04 15:05'
updated_date: '2026-10-04 15:15'
labels: []
dependencies: []
ordinal: 384000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update calculate_tasks_bom and calculate_order_bom logic to flatten the full recursive_bom_tree so that base materials like Mexallon show up correctly in shopping lists and aggregated views. Create a flatten_bom_tree function.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Shopping list properly displays raw minerals for deep BOM items like Titans, Views use flattened tree instead of single-depth calculation
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Refactored calculate_order_bom and calculate_tasks_bom in utils/bom_engine.py. They now call calculate_recursive_order_bom and calculate_recursive_tasks_bom respectively and use the newly added flatten_bom_tree utility function to aggregate the leaf nodes. Also fixed base_quantity tracking in recursive_bom_tree to properly reflect the base cost across all depth levels.
<!-- SECTION:NOTES:END -->
