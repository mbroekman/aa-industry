---
id: TASK-96
title: Fix expected_output calculation using BlueprintProduct quantity
status: Done
assignee: []
created_date: '2026-08-25 14:53'
updated_date: '2026-08-25 14:54'
labels: []
dependencies: []
ordinal: 86000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

expected_output in jobs.py returns runs instead of actual expected output because it uses EveType portion_size (which is for reprocessing). It should use EveIndustryActivityProduct.quantity.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 expected_output correctly calculates runs * BlueprintProduct quantity

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated expected_output property in jobs.py to use EveIndustryActivityProduct.quantity instead of EveType.portion_size for exact manufacturing outputs.

<!-- SECTION:NOTES:END -->
