---
id: TASK-187
title: Remove non-blueprint materials from Required Blueprints ME & BPC Overrides
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-01 09:44'
updated_date: '2026-10-01 09:45'
labels: []
dependencies: []
ordinal: 363000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Users have reported that non-blueprint materials are being shown or processed in the Required Blueprints ME and BPC Overrides sections. We need to filter these out so only actual blueprints are considered.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Required Blueprints ME only lists/processes blueprints
- [x] #2 BPC Overrides only lists/processes blueprints
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Modify quotes.py to filter out items without a blueprint (has_bp == False) before appending to products_me list.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Modified quotes.py to filter out non-blueprint materials before appending them to products_me.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Modified quotes.py to filter out items without a blueprint. Verified by running pytest, which passed all quotes views tests successfully.
<!-- SECTION:FINAL_SUMMARY:END -->
