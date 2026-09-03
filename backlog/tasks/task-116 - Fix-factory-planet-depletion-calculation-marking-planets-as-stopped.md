---
id: TASK-116
title: Fix factory planet depletion calculation marking planets as stopped
status: Done
assignee: []
created_date: '2026-09-02 16:50'
updated_date: '2026-09-02 16:58'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 106000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Code-onderzoek toont aan dat commit 041c471 een check heeft toegevoegd die controleert of f.last_cycle_start + cycle_time < planet.last_update. In EVE ESI wordt last_cycle_start van fabrieken echter alleen geüpdatet wanneer de speler in-game interageert met de planeet, waardoor last_cycle_start dagen oud kan zijn terwijl fabrieken gewoon doordraaien zolang er voorraad in storage is. Hierdoor werden alle fabrieksplaneten onterecht als stilstaand gemarkeerd (depletion_time = last_update). We moeten deze check verwijderen of corrigeren zodat de depletion tijd correct berekend wordt op basis van beschikbare voorraad en deficit.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Onjuiste last_cycle_start vergelijking verwijderen uit factory_depletion_time
- [x] #2 Planeten met voorraad (zoals 9O-ORC II) tonen weer de juiste resterende depletion tijd
- [x] #3 Tests toevoegen/updaten om regressie te voorkomen

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Onjuiste last_cycle_start check verwijderd uit CharacterPlanet.factory_depletion_time. Unit tests toegevoegd in test_models.py.

<!-- SECTION:NOTES:END -->
