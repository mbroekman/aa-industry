---
id: TASK-151
title: Investigate and document missing alliance structures (e.g. C-N Keepstar)
status: Done
assignee: []
created_date: '2026-09-11 14:16'
updated_date: '2026-09-11 14:16'
labels: []
dependencies: []
type: task
ordinal: 179000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Vooronderzoek
De gebruiker meldt dat niet alle structures van de alliance zichtbaar zijn in industry_reforged, waaronder de C-N Keepstar.
Onderzoek toont aan dat:
1. In EVE Online ESI bestaat er geen alliance-level endpoint voor structures (alleen GET /corporations/{corporation_id}/structures/).
2. De periodic task 'update_industry_facilities' en de dropdown 'get_corporate_structures_for_dropdown' pollen alleen de structuren van corporations die geregistreerd staan in 'CorporationSyncConfig'.
3. Momenteel is alleen 'Game of Drones' geconfigureerd in CorporationSyncConfig. De 18 structuren van Game of Drones zijn succesvol ingeladen (zoals 9O-ORX Foundry en Paddock).
4. Alliance staging structures zoals de C-N Keepstar zijn eigendom van de alliance holding corp (bijv. 'Initiative Holding') of een andere corporation binnen The Initiative, niet van Game of Drones.

### Code-analyse
- 'industry_reforged/tasks/facilities.py': haalt structuren op via ESI per geconfigureerde corporation.
- 'industry_reforged/views/facilities.py': dropdown 'get_corporate_structures_for_dropdown' toont alleen eigen corp structures en al bekende IndustryFacility records.
- Als een structuur van een andere corp is, kan deze handmatig worden toegevoegd via het Structure ID veld (/industry/director/facilities/add/) met behulp van 'esi-universe.read_structures.v1'.

### Voorgestelde oplossingen
1. Directe uitleg aan de gebruiker over de ESI-restricties en eigenaarschap van alliance structures.
2. Instructies hoe de C-N Keepstar handmatig toegevoegd kan worden via het Structure ID veld.
3. Eventuele uitbreiding om structuren van andere alliance-corporaties automatisch te synchroniseren indien tokens aanwezig zijn.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Oorzaak van ontbrekende alliance-structures duidelijk vastgesteld en gedocumenteerd
- [x] #2 Uitleg en handelingsperspectief verstrekt aan de gebruiker
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Onderzoek afgerond: ESI biedt geen alliance-level structure endpoint, alleen /corporations/{id}/structures/. De C-N Keepstar is eigendom van de alliance holding corp (Initiative Holding) en niet van Game of Drones. Omdat alleen Game of Drones in CorporationSyncConfig staat en er nog geen jobs/assets in de Keepstar zijn geregistreerd, wordt deze niet automatisch gedetecteerd. Duidelijke uitleg en 3 oplossingsrichtingen (handmatig toevoegen via Structure ID, corp sync config toevoegen, of job/asset registreren) gedocumenteerd.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Oorzaak van ontbrekende alliance-structures (zoals de C-N Keepstar) geïdentificeerd en gedocumenteerd. Advies en instructies verstrekt aan de gebruiker over handmatige invoer en ESI-structuurbeperkingen.
<!-- SECTION:FINAL_SUMMARY:END -->
