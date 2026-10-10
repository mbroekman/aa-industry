---
id: TASK-239
title: Keep ready jobs visible in my corporate jobs until delivered
status: Done
assignee:
  - Antigravity
created_date: '2026-10-08 09:05'
updated_date: '2026-10-08 09:05'
labels:
  - bug
  - ui
dependencies: []
ordinal: 415000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Op het Industrialist Dashboard onder de tab 'My Corporate Jobs' (en 'Corporate Jobs Overview') verdwenen jobs die klaar waren met produceren ('ready' / op deliver staan) direct uit het overzicht wanneer het standaard filter 'Active' geselecteerd stond. Hierdoor zagen industrialisten hun voltooide banen niet meer in de actieve lijst en leek het alsof banen verdwenen waren voordat ze in EVE Online werden afgeleverd ('delivered').
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Banen met status 'Ready' (klaar om te leveren) blijven zichtbaar onder het standaardfilter 'Active' in de tab 'My Corporate Jobs'.
- [x] #2 Banen verdwijnen pas uit het 'Active' overzicht zodra ze daadwerkelijk zijn afgeleverd ('delivered') in het spel.
- [x] #3 Het specifieke filter 'Ready' blijft functioneren en toont uitsluitend banen die gereed zijn voor levering.
- [x] #4 Zelfde consistentie doorgevoerd voor de algemene tab 'Corporate Jobs Overview'.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. In `industry_reforged/templates/industry_reforged/industrialist_dashboard.html`:
   - Pas de DataTables zoekextensie (`$.fn.dataTable.ext.search.push`) aan voor zowel `#myevejobs-table` als `#corporate-jobs-table`.
   - Zorg dat wanneer `filter === 'active'`, zowel rijen met `data-job-status="active"` als `data-job-status="ready"` worden getoond.
2. Synchroniseer naar de remote server en herstart Gunicorn.
3. Verifieer werking.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Aangepast in `industrialist_dashboard.html`. Wanneer het filter op 'Active' staat, toont de DataTables filterfunctie nu zowel actieve (`status === 'active'`) als gereedstaande banen (`status === 'ready'`). Banen blijven dus zichtbaar met een gele 'Ready' badge totdat de status via ESI daadwerkelijk overgaat naar 'delivered'.
<!-- SECTION:NOTES:END -->
