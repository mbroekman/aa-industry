---
id: TASK-152
title: >-
  Investigate why corporate asset structures (e.g. C-N Keepstar) are not
  resolved after fresh install
status: Done
assignee: []
created_date: '2026-09-11 14:22'
updated_date: '2026-09-11 14:56'
labels: []
dependencies: []
type: bug
ordinal: 149000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Vooronderzoek
De gebruiker geeft aan dat Game of Drones wel degelijk corporate assets heeft in verschillende alliance structures, waaronder de C-N Keepstar. Voor de verse installatie werkte dit wel, maar nu ontbreken deze structuren.

### Code-analyse
1. Onderzoek 'CorpInventory', 'tasks/inventory.py' en 'tasks/facilities.py'.
2. Controleer wat ESI teruggeeft voor corporate assets ('/corporations/{corporation_id}/assets/').
3. Controleer hoe 'location_id', 'location_type' of 'location_flag' worden geparset in 'tasks/facilities.py' en 'tasks/inventory.py'.
4. Bepaal waarom Upwell structure IDs van corporate assets niet worden toegevoegd aan 'IndustryFacility' of 'KnownLocation'.

### Voorgestelde aanpassingen
Onderzoeken, reproduceren en fixen van de detectie en resolutie van asset-locaties.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Corporate assets van Game of Drones gecontroleerd op aanwezigheid van C-N Keepstar location_id
- [x] #2 Oorzaak gevonden waarom deze asset location niet werd geresolved als IndustryFacility of KnownLocation
- [x] #3 Fix geïmplementeerd en geverifieerd via tests en live ESI/DB check
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
1. update_industry_facilities in tasks/facilities.py: corporate assets worden nu recursief geresolved naar root locations (stations en citadels) en toegevoegd aan IndustryFacility en KnownLocation.
2. task_sync_corp_inventory in tasks/inventory.py: breekt niet meer vroegtijdig af wanneer facility_ids leeg is; KnownLocation en ESI structure resolution draaien altijd.
3. resolve_unknown_locations in tasks/utils.py: Upwell structures worden nu ook opgeslagen/geüpdatet in IndustryFacility.
4. get_corporate_structures_for_dropdown in views/facilities.py: toont nu alle ontdekte structures/known locations alfabetisch gesorteerd.
5. Getest in live database (C-N4OD Keepstar ID 1045667241057 succesvol geresolved) en 149 pytest tests geslaagd.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Corporate assets worden nu correct geresolved naar root Upwell structures (waaronder de C-N4OD Keepstar) en direct beschikbaar gemaakt in de IndustryFacility en KnownLocation tabellen, evenals in alle dropdowns en Target Hub keuzes.
<!-- SECTION:FINAL_SUMMARY:END -->
