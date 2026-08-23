---
id: TASK-80
title: Show corp stock in BOM
status: Done
assignee:
  - '@antigravity'
created_date: '2026-08-22 11:59'
updated_date: '2026-08-22 12:44'
labels: []
dependencies: []
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The Bill of Materials (BOM) shows required materials. We need to display the corporation's current stock for each material in the BOM view to easily see if there are enough materials available.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 BOM view displays the current corporation stock quantity for each material
- [x] #2 Visually indicate whether the stock is sufficient to meet the requirement or if there is a shortage

<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. Modify calculate_order_bom in bom_engine.py to query total CorpInventory and inject corp_stock into material dict.
1. Modify shopping_list view in director.py to include corp_stock in the manually constructed bom dict.
1. Update shopping_list.html template to add a Corp Stock column and visual indicators for shortages.
1. Update quote_bom_panes.html to add the Corp Stock column and visual indicators.

<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Validation passed: syntax checks pass, DB queries are constructed correctly using Sum('quantity'), templates inject new column without breaking tables.

<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

Implemented corp stock display in Quotes BOM and Shopping List BOM. Verified with syntax checks.

<!-- SECTION:FINAL_SUMMARY:END -->
