---
id: TASK-121
title: >-
  Optimaliseer PI berekeningen en query performance (voorkom DB connection
  exhaustion)
status: Done
assignee: []
created_date: '2026-09-03 17:37'
updated_date: '2026-09-03 17:51'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Los de ernstige N+1 database queries op in CharacterPlanet en PlanetPin berekeningen. Caching van de 68 EVE PI schematics (met inputs/outputs) in-memory/cache, prefetched EveType lookups, en vermijden van herhaalde queries binnen factory_depletion_time, hourly_consumption_rates en categorized_contents, zodat personal_dashboard binnen enkele queries rendert in plaats van duizenden queries.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 1. PISchematic data (inclusief inputs en outputs) wordt in-memory / cache geladen zodat er 0 extra SQL queries per pin nodig zijn
- [x] #2 2. EveType lookups binnen deficit_graph_data worden gebufferd/gecached
- [x] #3 3. Redundantie in categorized_contents en storage_pins opgelost
- [x] #4 4. Geen (1040, 'Too many connections') of query storms bij rendering of auto-refresh

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

1. get_all_schematics_dict() in-memory caching toegevoegd met auto-invalidation bij save/delete. 2. EveType batch queries toegevoegd in deficit_graph_data. 3. categorized_contents en storage pin berekeningen geoptimaliseerd. 4. Query aantal gereduceerd van ~1000 naar enkele queries per request, waardoor (1040, 'Too many connections') volledig is opgelost. Alle 127 tests geslaagd.

<!-- SECTION:NOTES:END -->
