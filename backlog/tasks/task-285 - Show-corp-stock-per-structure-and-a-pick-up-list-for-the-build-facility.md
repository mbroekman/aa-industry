---
id: TASK-285
title: Show corp stock per structure and a pick-up list for the build facility
status: Done
assignee: []
created_date: '2026-10-31 10:05'
updated_date: '2026-10-31 10:08'
labels:
  - inventory
  - ui
dependencies: []
ordinal: 459000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Material tables show one Corp Stock total over every location, so a builder cannot see whether the stock sits in the structure they build in. Show stock per structure (build facility first) on the order page, the industrialist Missing Materials tab and the shopping lists, plus a pick-up list per source structure of what must be hauled to the build facility.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Corp Stock cells list the quantity per structure, build facility highlighted
- [x] #2 Order page, industrialist Missing Materials and shopping list show a pick-up list grouped by source structure when there is one build facility
- [x] #3 Pick-up list only covers what the build facility lacks, largest piles first
- [x] #4 Blueprints are left out (their stock is counted in runs)
- [x] #5 Tests cover the split, the pick-up list and facility detection
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
utils/stock_locations.py: per-structure stock (IndustryFacility/KnownLocation names), split into build facility vs elsewhere, to_haul and a greedy pick-up list per source structure. Wired into view_quote + htmx facility update, industrialist Missing Materials (single shared facility of claimed jobs), shopping list (also fixed NameError on corp_info / sorted_bps for order-only lists) and the director deficit list (locations only). Partials stock_locations.html and haul_list.html. Verified on devauth: builders see a pick-up list from the 3G0DS Repro to the Foundry.
<!-- SECTION:FINAL_SUMMARY:END -->
