---
id: TASK-213
title: Remove leftover Fuzzwork bom_source fields
status: Done
assignee: []
created_date: '2026-10-04 16:43'
updated_date: '2026-10-04 16:46'
labels: []
dependencies: []
ordinal: 389000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Fuzzwork BOM API option is still visible in the Director Configuration (Item Config), but Fuzzwork has been deprecated and the field is unused in logic. The field bom_source needs to be removed from the CorpItemConfig model and the director configuration template.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. bom_source is removed from CorpItemConfig in models.orders.py. 2. BOM_CHOICES is removed. 3. Template director_config.html no longer shows bom_source. 4. A Django migration is created to remove the field from the database.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Removed bom_source field and BOM_CHOICES from CorpItemConfig. Generated migration. Tests passed.
<!-- SECTION:NOTES:END -->
