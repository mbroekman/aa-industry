---
id: TASK-212
title: Separate Blueprints in Raw Materials and fix BPC pricing
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-04 16:28'
updated_date: '2026-10-04 16:34'
labels: []
dependencies: []
ordinal: 388000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1. In 'Required Raw Materials', list blueprints separately from normal raw materials. 2. For blueprint items, if there is no manual CorpItemConfig override, set their price to 0 (do not fetch from ESI BPO market). Most BPCs are cheap enough to ignore, and expensive ones will be manually overridden.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Blueprints shown separately. Blueprint prices default to 0 unless overridden. Tests passed.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Blueprints (category_id=9) are now split out from the generic bom_materials list in views (quotes.py, director.py, shopping.py). They are displayed in a separate table underneath the raw materials in both quote_bom_panes.html and shopping_list.html. In pricing_engine.py, get_market_prices is skipped for blueprints and they are defaulted to 0 unless a CorpItemConfig overrides their price.
<!-- SECTION:NOTES:END -->
