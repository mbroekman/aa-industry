---
id: TASK-150
title: Update Dutch translations for industry_reforged
status: Done
assignee: []
created_date: '2026-09-11 12:20'
updated_date: '2026-09-11 12:43'
labels: []
dependencies: []
priority: medium
type: enhancement
ordinal: 180000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Vooronderzoek
De Nederlandse vertaalbestanden (`django.po` en `django.mo`) in `industry_reforged/locale/nl/` zijn voor het laatst bijgewerkt op 4 augustus 2026 (versie 0.3.0). Alle features die daarna zijn geïntroduceerd (AI Market Manager, Basket management, Opportunity Scanners, Auto-refresh, Rig-sync, taakverwijderingen, etc.) ontbreken in de Nederlandse vertaling en vallen terug op het Engels.

### Code-analyse
In de Python modules (`forms.py`, `views/`, `models/`, `tasks/`) en Django templates (`templates/industry_reforged/`) zijn tientallen nieuwe translatable strings toegevoegd via `gettext_lazy` (`_()`) en Django template tags. Deze moeten worden geëxtraheerd naar `django.po`.

### Voorgestelde aanpassingen
1. Draai `makemessages` voor de Nederlandse locale (`nl`).
2. Vertaal alle nieuwe en niet-vertaalde strings naar natuurlijk, correct Nederlands passend bij EVE Online en Alliance Auth.
3. Draai `compilemessages` om de binaire `django.mo` catalogus bij te werken.
4. Controleer dat het project en de tests foutloos draaien.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 makemessages geëxecuteerd voor de Nederlandse taal (nl)
- [x] #2 Alle nieuwe en gewijzigde strings vertaald naar het Nederlands in django.po
- [x] #3 compilemessages compileert foutloos naar django.mo
- [x] #4 Geautomatiseerde tests slagen
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Alle 254 ontbrekende en gewijzigde translatable strings (uit forms, views, models en templates van versies 0.4.0 t/m 0.11.0+) zijn geëxtraheerd en accuraat vertaald naar het Nederlands. F-strings in gettext-aanroepen zijn gecorrigeerd naar format strings. Beide fuzzy entries in django.po zijn hersteld. Binaire catalogus django.mo is gecompileerd (55.4 KB). Test suite met test_translations.py slaagt 100% (147/147 tests).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Nederlandse vertalingen voor aa-industry / industry_reforged zijn volledig bijgewerkt tot en met de laatste wijzigingen (AI Market Manager, Basket management, Opportunity Scanners, Rig sync, taakbeheer, grootboek, etc.). Alle 147 geautomatiseerde tests slagen foutloos.
<!-- SECTION:FINAL_SUMMARY:END -->
