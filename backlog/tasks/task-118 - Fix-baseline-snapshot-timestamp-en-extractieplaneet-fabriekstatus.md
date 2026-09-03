---
id: TASK-118
title: Fix baseline snapshot timestamp en extractieplaneet fabriekstatus
status: Done
assignee: []
created_date: '2026-09-02 21:01'
updated_date: '2026-09-02 22:01'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

1. Gebruik de oudste/meest recente last_cycle_start van fabrieken als baseline timestamp voor simulatie in plaats van planet.last_update (die door Celery sync steeds naar now wordt gereset). 2) Zorg dat extractie-planeten met actieve extractors niet als 'Out of Resources' worden gemarkeerd wanneer ruwe grondstoffen direct gerouteerd worden (niet in storage liggen). 3) Zorg dat alleen fabrieken/planeten zonder aanvoer en zonder voorraad als 'Out of Resources' worden getoond.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Simulatie berekent verstreken tijd vanaf last_cycle_start baseline i.p.v. steeds geresette last_update
- [x] #2 9O-ORX fabrieksplaneten tonen exacte in-game aantallen (bijv. 2064 robotics op I, 864 cryo op II met resterende voorraad)
- [x] #3 Extractieplaneten met actieve extractors tonen niet onterecht 'Out of Resources'

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

1. Baseline snapshot timestamp (factory_baseline_time) gekoppeld aan last_cycle_start van de fabrieken i.p.v. de steeds geresette last_update. 2. Simulatie van grondstofverbruik en productie berekent nu exacte aantallen tussen baseline en depletion_time. 3. Extractieplaneten met actieve extractors worden niet langer onterecht als Out of Resources gemarkeerd bij 0 storage buffer. 4. Alle 126 unit tests slagen.

<!-- SECTION:NOTES:END -->
