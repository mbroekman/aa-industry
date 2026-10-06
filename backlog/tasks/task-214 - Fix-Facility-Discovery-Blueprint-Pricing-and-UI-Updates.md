---
id: TASK-214
title: 'Fix Facility Discovery, Blueprint Pricing, and UI Updates'
status: Done
assignee: []
created_date: '2026-10-04 22:09'
updated_date: '2026-10-04 22:09'
labels: []
dependencies: []
ordinal: 390000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1. Fix shared structure filtering (KnownLocation) for reaction/production facilities. 2. Auto-link KnownLocation when adding facility. 3. Blueprint pricing overridden to 0 unless configured. 4. Reduce size of location/set target buttons. 5. Confirm Wait Dialog for Inventory Analytics.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 - Facilities owned by holding corps are usable.\n- Blueprints without config cost 0 ISK.\n- UI elements updated.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
1. Fixed IndustryFacility filtering in director.py and bom_engine.py to use KnownLocation\n2. Modified add_facility to register KnownLocation immediately\n3. Updated shopping.py to use get_prices_with_overrides\n4. Refactored Inventory Overview buttons\n5. Verified existing show-loader implementation for Inventory Analytics
<!-- SECTION:NOTES:END -->
