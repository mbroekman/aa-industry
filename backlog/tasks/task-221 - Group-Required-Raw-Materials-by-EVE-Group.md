---
id: TASK-221
title: Group Required Raw Materials by EVE Group
status: Done
assignee: []
created_date: '2026-10-06 07:51'
updated_date: '2026-10-06 07:53'
labels: []
dependencies: []
ordinal: 397000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enrich the BOM materials with their EVE Online market group name and group them visually in the DataTables view using drawCallback.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Materials are grouped by EVE Group (e.g. Minerals, PI), Blueprints remain in their own Blueprint group, DataTables sorting still functions correctly within and across groups
- [ ] #2 1
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Enriched bom materials with eve_group names in bom_engine.py. Updated quote_bom_panes.html to dynamically render DataTables groups based on these group names, replacing the generic 'Material' label. Blueprints are explicitly kept in their own 'Blueprints' group.
<!-- SECTION:NOTES:END -->
