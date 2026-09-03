---
id: TASK-119
title: Automatisch controleren en inladen van PI schematics indien tabel leeg is
status: Done
assignee: []
created_date: '2026-09-03 09:05'
updated_date: '2026-09-03 16:15'
labels: []
dependencies: []
priority: high
type: enhancement
ordinal: 109000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Code-onderzoek toont aan dat op nieuwe installaties of na migratie de PISchematic tabel 0 records bevat totdat de Celery taak handmatig of periodiek draait. Hierdoor werkt de consumptie/deficit berekening en grafiek niet. Aanpassingen: 1) Controleer in update_character_pi en bij trigger_pi_sync of PISchematic.objects.exists(). Indien leeg: laad automatisch de schematics in via update_pi_schematics_from_sde. 2) Zorg voor foutafhandeling en fallback zodat de applicatie altijd direct over de juiste formules beschikt.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 1. update_character_pi controleert of PISchematic tabel leeg is en laadt deze direct in
- [x] #2 2. trigger_pi_sync zorgt dat schematics aanwezig zijn bij handmatige refresh
- [x] #3 3. Unit tests dekken de automatische bootstrapping van schematics af

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

1. update_character_pi controleert bij aanvang of PISchematic.objects.exists() en laadt deze direct in via update_pi_schematics_from_sde indien leeg. 2. trigger_pi_sync en personal_dashboard view triggeren eveneens de achtergrond synchronisatie van schematics indien de tabel leeg is. 3. Unit test test_update_character_pi_autoboots_schematics_when_empty toegevoegd en geslaagd; alle 127 tests geslaagd.

<!-- SECTION:NOTES:END -->
