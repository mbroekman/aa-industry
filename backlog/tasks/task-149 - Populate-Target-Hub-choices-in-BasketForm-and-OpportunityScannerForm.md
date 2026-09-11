---
id: TASK-149
title: Populate Target Hub choices in BasketForm and OpportunityScannerForm
status: Done
assignee: []
created_date: '2026-09-11 11:59'
updated_date: '2026-09-11 12:02'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 146000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Vooronderzoek
Bij het aanmaken of bewerken van een Basket of Opportunity Scanner in de AI Market Manager is de dropdown `Target Hub (Structure ID)` leeg (bevat alleen `---------`).

### Code-analyse
In `industry_reforged/forms.py` (`BasketForm` en `OpportunityScannerForm`) wordt de dropdown choices voor `target_hub_id` uitsluitend gevuld via:
```python
locations = (
    KnownLocation.objects.filter(corporations__in=user_corps)
    .distinct()
    .order_by("name")
)
```
Oorzaken:
1. `KnownLocation` wordt alleen gevuld door `task_sync_corp_inventory` wanneer asset sync aan staat en assets worden gevonden. In de praktijk is `KnownLocation` vaak leeg.
2. De daadwerkelijke productie- en industriële hubs worden in Alliance Auth opgeslagen in het `IndustryFacility` model (waar er in de database 36 actieve faciliteiten van de corp/alliantie aanwezig zijn).
3. Zowel `Basket.target_hub` als `OpportunityScanner.target_hub` zijn `ForeignKey` velden naar `IndustryFacility`, en de `clean()` methode koppelt `target_hub_id` direct aan `IndustryFacility`.
4. Omdat `IndustryFacility` nooit geraadpleegd werd in `__init__`, bleef de dropdown leeg.

### Voorgestelde aanpassingen
1. Breid de keuzelijst voor `target_hub_id` in `BasketForm` en `OpportunityScannerForm` uit zodat geconfigureerde `IndustryFacility` records (van de eigen corp, alliantie-corps, NPC stations en productiefaciliteiten) worden opgenomen.
2. Behoud eventuele extra `KnownLocation` records indien aanwezig.
3. Zorg voor deduplicatie en alfabetische sortering.
4. Schrijf unit tests om te valideren dat de dropdown opties bevat voor zowel `BasketForm` als `OpportunityScannerForm`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 target_hub_id keuzelijst in BasketForm bevat geconfigureerde IndustryFacility opties
- [x] #2 target_hub_id keuzelijst in OpportunityScannerForm bevat geconfigureerde IndustryFacility opties
- [x] #3 target_hub_id keuzelijst bevat geen duplicaten
- [x] #4 Alle geautomatiseerde tests slagen
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
1. Helperfunctie `get_target_hub_choices(user_corps=None, current_target_hub=None)` toegevoegd aan `industry_reforged/forms.py`.
2. In `get_target_hub_choices` worden zowel geconfigureerde `IndustryFacility` records (gefilterd op eigenaar/alliantie van de corporaties van de gebruiker, NPC-stations en productiefaciliteiten) als `KnownLocation` records opgenomen.
3. Deduplicatie ingebouwd en alfabetische sortering op naam toegepast.
4. Zowel `BasketForm` als `OpportunityScannerForm` maken nu gebruik van deze helperfunctie, zodat de dropdown niet meer afhankelijk is van asset sync alleen.
5. Unit tests toegevoegd in `industry_reforged/tests/test_ai_forms.py` die alle scenario's dekken. Alle 6 tests geslaagd.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Target Hub dropdown in BasketForm en OpportunityScannerForm gevuld met alle relevante IndustryFacility structuren/stations en KnownLocations.
<!-- SECTION:FINAL_SUMMARY:END -->
