---
id: TASK-120
title: Auto-refresh functionaliteit toevoegen voor Industry Jobs en PI dashboards
status: Done
assignee: []
created_date: '2026-09-03 16:18'
updated_date: '2026-09-03 16:21'
labels: []
dependencies: []
priority: medium
type: feature
ordinal: 110000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Voeg een configureerbare auto-refresh toe op dashboards met industry jobs en planetary interaction (Personal Dashboard, Corporate Dashboard, Industrialist Dashboard). Opties in een vast setje: Uit, 5, 10, 15, 25 en 30 minuten. Opslag van gebruikerskeuze in localStorage, behoud van actieve tabblad-state bij refresh, en tijdelijke pauze wanneer een modal/dialoog openstaat.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 1. Dropdown/selector aanwezig op Personal, Corporate en Industrialist dashboards met opties: Uit, 5m, 10m, 15m, 25m, 30m
- [x] #2 2. Gekozen interval wordt onthouden in localStorage en toont een live countdown timer
- [x] #3 3. Actieve tabbladen en scroll/state blijven behouden na automatische herlaadactie
- [x] #4 4. Auto-refresh pauzeert automatisch wanneer modals of formulieren geopend zijn

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

1. autorefresh_control.html partial component gecreëerd met intervallen: Uit, 5m, 10m, 15m, 25m en 30m. 2. Geïntegreerd op Personal Dashboard, Corporate Dashboard en Industrialist Dashboard. 3. LocalStorage persistence en live countdown timer ingebouwd met tab-state behoud en modal-pauze. 4. Alle 127 tests geslaagd.

<!-- SECTION:NOTES:END -->
