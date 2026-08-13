---
id: TASK-66
title: Filter activities on corporate dashboard
status: Done
assignee: []
created_date: '2026-08-13'
updated_date: '2026-08-13'
labels: ['feature', 'ui']
dependencies: []
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Voeg een dropdown menu toe aan het Corporate Industry Jobs dashboard waarmee je de tabel kunt filteren op specifieke activiteiten (zoals Manufacturing, Copying, Invention, Reactions, etc).
Dit maakt het veel makkelijker om overzicht te houden als de lijst met actieve of historische jobs erg lang is.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Voeg een HTML `<select>` toe naast de "Active / History" tabjes.
- [x] #2 Zorg ervoor dat de gekozen waarde wordt meegestuurd in de DataTables AJAX requests.
- [x] #3 Verwerk de nieuwe `activity` parameter in de backend (`dt_corporate_jobs`) zodat er op database niveau correct gefilterd wordt.
- [x] #4 Zorg dat bij een verandering van de selectie, de tabellen automatisch herladen worden (`ajax.reload()`).

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- `industry_reforged/templates/industry_reforged/corporate_dashboard.html`: Dropdown met id `activity-filter` toegevoegd in de header, flex classes gebruikt voor uitlijning. DataTables initialisatie herschreven naar variabelen zodat `activeTable.ajax.reload()` uitgevoerd kan worden. `ajax.data` parameter gedefinieerd die `$('#activity-filter').val()` meestuurt.
- `industry_reforged/views/datatables.py`: parameter `activity` wordt opgevraagd; indien aanwezig en numeriek (bijv. 1=Manufacturing, 8=Invention, etc) wordt de `CorporationIndustryJob` queryset verder gefilterd met `activity_id=int(activity_filter)`.

<!-- SECTION:NOTES:END -->
