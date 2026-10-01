---
id: TASK-190
title: Remove raw materials from Required Blueprints list
status: Done
assignee: []
created_date: '2026-10-01 11:21'
updated_date: '2026-10-01 15:01'
labels: []
dependencies: []
ordinal: 366000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Raw materials like Tritanium that do not have a blueprint in the game should not appear in the Required Blueprints (ME & BPC Overrides) list.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Raw materials are hidden from the Required Blueprints list, Missing blueprints for manufacturable items are still shown and flagged
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated quotes.py to skip items that do not have an associated blueprint in the SDE (has_bp = False) when building the products_me list for the ME & BPC Overrides form.
<!-- SECTION:NOTES:END -->
