---
id: TASK-6
title: 'Geen ME voor niet-BP producten (zoals reactions)'
status: Done
assignee: []
created_date: '2026-08-01 15:30'
updated_date: '2026-08-01 15:30'
labels: []
dependencies: []
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Als er geen Blueprint gebruikt wordt (zoals bij reactions), moet de Material Efficiency (ME) altijd op 0 staan en mag deze niet aan te passen zijn door de gebruiker.

Acties:

- ME berekening voor niet-BP producten (reactions) forceren naar 0.
- Geen ME-vermelding tonen bij deze onderdelen in de interface.
- Geen ME-aanpassingen toestaan voor deze onderdelen, en ze dus ook niet tonen in de lijst voor mogelijke ME/BPC-correcties.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Bij producten zonder manufacturing blueprint wordt ME altijd als 0 berekend.
- [x] #2 In de overzichten/lijsten wordt geen ME-waarde of aanpassingsveld getoond voor deze items.
- [x] #3 De lijst met mogelijke ME/BPC correcties verbergt de instellingen voor niet-BP producten.

<!-- AC:END -->

## Implementation Notes

**Uitgevoerde wijzigingen:**

1. **Logica (`bom_engine.py`)**: `get_blueprint_me()` is geüpdatet. Als er via `EveIndustryActivityProduct` (met activity_id=1) geen blueprint gevonden kan worden voor het item (zoals bij reactions), retourneert de functie altijd 0 voor ME.
1. **Models (`orders.py`)**: Er is een `@property def has_blueprint(self):` toegevoegd aan `CorpItemConfig` en `OrderBlueprintOverride` om makkelijk vanuit de frontend te kunnen checken of het item gebouwd wordt via een reguliere blueprint.
1. **UI/Templates (`director_config.html` en `view_quote.html`)**: De input velden en data presentaties rond ME/TE/BPC runs zijn conditioneel verborgen en vervangen door een "N/A" of vergelijkbare placeholder als `has_blueprint` op `False` staat. Voor quote berekeningen (`quotes.py`) is ook een `has_blueprint` key meegegeven aan `products_me`.
