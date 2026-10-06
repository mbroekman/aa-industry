---
id: TASK-217
title: Fix BOM recursion for BUY items inflating cost
status: Done
assignee: []
created_date: '2026-10-05 19:27'
updated_date: '2026-10-05 19:28'
labels: []
dependencies: []
ordinal: 393000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Stop get_recursive_bom_tree from recursively calculating components in both Pricing Engine and visual tree if the item is configured as 'BUY' in CorpItemConfig. This prevents inflating prices for T2 components that should be bought.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 BOM engine respects build_or_buy == 'BUY'|Quote generation no longer calculates raw materials for BUY items|Pricing engine includes build_or_buy in config_dict
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed missing build_or_buy flag in config_dict construction inside bom_engine.py and pricing_engine.py.
<!-- SECTION:NOTES:END -->
