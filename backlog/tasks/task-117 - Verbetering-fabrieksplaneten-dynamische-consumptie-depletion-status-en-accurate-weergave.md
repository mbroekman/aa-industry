---
id: TASK-117
title: >-
  Verbetering fabrieksplaneten: dynamische consumptie, depletion status en
  accurate weergave
status: Done
assignee: []
created_date: '2026-09-02 20:30'
updated_date: '2026-09-02 20:39'
labels: []
dependencies: []
priority: high
type: enhancement
ordinal: 107000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Implementeer een complete en accurate simulatie en statusweergave voor fabrieksplaneten. 1) Simuleer dynamisch grondstofverbruik in storage pins (categorized_contents). 2) Bepaal accurate status voor fabrieken (Running vs Out of Resources). 3) Toon duidelijke 'Out of Resources' / 'Depleted' status op planeetkaarten en in modals wanneer grondstoffen op zijn. 4) Voeg dashboard indicatoren toe voor karakters met stilstaande fabrieken.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Dynamische aftrek van geconsumeerde grondstoffen in storage pins tussen ESI syncs
- [x] #2 Toon 'Out of Resources' status zodra factory_depletion_time is bereikt of voorraad 0 is
- [x] #3 Fabriekspins tonen 'Running' als ze voorraad hebben en 'Out of Resources' als input op is
- [x] #4 Unit tests voor verbruikssimulatie en factory status

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

1. Dynamische aftrek van geconsumeerde grondstoffen geïmplementeerd in PlanetPin.categorized_contents op basis van verstreken uren/cycli tot aan depletion_time. 2. Accurate fabriekstatussen (Running vs Out of Resources vs Idle) geïmplementeerd in PlanetPin.status_label en CharacterPlanet.grouped_factories. 3. Dashboard weergave uitgebreid met 'Out of Resources' status zodra voorraad 0 is of timer verloopt, en actieve countdown timer zolang er voorraad is. 4. Karakter-dashboard indicators voorzien van waarschuwing voor karakters met stilstaande fabrieken. 5. Unit tests toegevoegd en 126/126 tests geslaagd.

<!-- SECTION:NOTES:END -->
