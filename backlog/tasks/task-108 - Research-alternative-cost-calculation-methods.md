---
id: TASK-108
title: Research alternative cost calculation methods
status: Done
assignee: []
created_date: '2026-08-30 10:56'
updated_date: '2026-08-30 10:57'
labels: []
dependencies: []
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Research and advise on how to calculate costs in the right way (based on BOM/materials) instead of just using Jita price for the end product. Output needs to be an English proposal document.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 1. Document outlining alternative cost models 2. Recommendations for BOM-based pricing 3. Written in English

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Completed research into BOM-based cost calculations. Created an English proposal document outlining 3 models: True Material Cost, Hybrid Safe Margin, and Value-Added payouts. Recommended starting with True Material Cost calculation via extending pricing_engine.py to use bom_engine.py outputs.

<!-- SECTION:NOTES:END -->
