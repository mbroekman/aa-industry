---
id: TASK-254
title: Implement Production Task Priority Controls and Multiplier Visualization
status: Done
assignee:
  - Add URGENT to ProductionTask.PRIORITY_CHOICES and generate migration
  - Add priority dropdown to Director manual restock form
  - >-
    Add single and bulk priority update endpoints with automatic reward
    recalculation
  - >-
    Display priority badges and ordering on Job Market in
    industrialist_dashboard.html
  - Add bulk Set Priority controls for directors on unclaimed Job Market
  - Unit tests written and passing
created_date: '2026-10-21 14:05'
updated_date: '2026-10-21 16:20'
labels: []
dependencies: []
ordinal: 428000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable directors to set and adjust production task priorities (Urgent, High, Normal, Low) individually and in bulk, with automatic builder reward recalculation using corp multipliers, and display priority badges on the unclaimed Job Market.
<!-- SECTION:DESCRIPTION:END -->
