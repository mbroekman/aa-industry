---
id: TASK-69
title: Fix BOM engine yield quantity for reactions
status: Done
assignee: []
created_date: '2026-08-15 07:11'
updated_date: '2026-08-15 07:11'
labels: []
dependencies: []
ordinal: 69000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The BOM engine fallback to legacy materials was hardcoding yield_qty to 1 instead of EveType.portion_size. This caused reaction outputs (like Tungsten Carbide) which have a yield of 10,000 to be calculated as 1, leading to massive time/material requirements.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Tungsten Carbide calculates correct quantity and time

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated get_sde_bom to use portion_size as fallback

<!-- SECTION:NOTES:END -->
