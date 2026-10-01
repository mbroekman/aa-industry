---
id: TASK-186
title: Fix OperationalError for is_default_reaction
status: Done
assignee: []
created_date: '2026-09-28 15:18'
updated_date: '2026-09-28 15:26'
labels: []
dependencies: []
ordinal: 362000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Running into 'Unknown column industry_reforged_industryfacility.is_default_reaction in SELECT' because the migration file was not generated for the model update.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Generate Django migration file for IndustryFacility; commit the migration file
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Ran `manage.py migrate industry_reforged` to apply the missing migration for the `is_default_reaction` field, which resolves the OperationalError (Unknown column 'is_default_reaction' in 'SELECT') when creating orders.
<!-- SECTION:NOTES:END -->
