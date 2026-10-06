---
id: TASK-219
title: Fix BOM engine picking unpublished test blueprints for reactions
status: Done
assignee: []
created_date: '2026-10-06 07:17'
updated_date: '2026-10-06 07:18'
labels: []
dependencies: []
ordinal: 395000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The get_sde_bom function was fetching the first blueprint for a product without checking if it was published. This caused CCP's 'Test Reaction Blueprint' (yield 20) to be selected instead of the real 'Reaction Formula' (yield 10000) for items like Tungsten Carbide. This resulted in required raw moon materials being multiplied by 500x, causing absurd pricing (16 billion for 3 CONCORD plates).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 BOM engine only selects published blueprints, CONCORD 25000mm Steel plates true cost is now calculated accurately (~191m ISK)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added eve_type__published=True to all EveIndustryActivityProduct.objects.filter() queries in bom_engine.py. Confirmed via shell that the true cost of a CONCORD plate is now correctly computed as ~191m ISK instead of 4.7b ISK.
<!-- SECTION:NOTES:END -->
