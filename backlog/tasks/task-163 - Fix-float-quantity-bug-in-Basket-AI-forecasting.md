---
id: TASK-163
title: Fix float quantity bug in Basket AI forecasting
status: Done
assignee: []
created_date: '2026-09-12 18:58'
updated_date: '2026-09-12 19:00'
labels: []
dependencies: []
ordinal: 339000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AI forecasting returns float values for target_stock (e.g. 420.80) which leads to fractional shortages (e.g. 0.80). Django truncates this float to 0 when saving the ProductionTask, resulting in jobs with 0 quantity.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Use math.ceil to round up the AI target_stock to a full integer before calculating shortage
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Imported math and used math.ceil to cast ai_resp reorder_point to int
<!-- SECTION:NOTES:END -->
