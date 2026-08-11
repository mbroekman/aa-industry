---
id: TASK-61
title: Fix Job Market Rollup
status: Done
assignee: []
created_date: '2026-08-11 06:48'
updated_date: '2026-08-11 06:49'
labels: []
dependencies: []
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Tijdens de 0.3.3 update (flattening the production tasks lists) is de `bom_parent__isnull=True` filter uit de `unclaimed_tasks_qs` query in `industry_reforged/views/industrialist.py` verwijderd. Hierdoor haalt de applicatie nu zowel root-taken als alle onderliggende sub-taken op, wat leidt tot een overvolle Job Market. Tevens werkt de cascade-selectie van de checkboxes niet meer doordat `data-parent-id` mist in de HTML-weergave, en is de individuele Claim-knop onzichtbaar omdat de `depth == 0` check faalt zonder de `build_task_tree` logica.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 De filter `bom_parent__isnull=True` wordt weer toegevoegd aan de Job Market lijst, zodat enkel hoofdtaken worden getoond
- [x] #2 Bij het claimen van een hoofdtaak rolt dit correct uit naar de children
- [x] #3 De Claim-knop op de individuele hoofdtaken wordt weer zichtbaar gemaakt

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Restored bom_parent\_\_isnull=True in views/industrialist.py and fixed template logic for Claim button (used not task.bom_parent_id instead of depth) and cascade select (added data-parent-id).

<!-- SECTION:NOTES:END -->
