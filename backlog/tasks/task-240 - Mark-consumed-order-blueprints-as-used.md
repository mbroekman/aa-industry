---
id: TASK-240
title: Mark consumed order blueprints as used
status: Done
assignee:
  - Antigravity
created_date: '2026-10-08 10:20'
updated_date: '2026-10-08 10:25'
labels:
  - bug
  - ui
dependencies: []
ordinal: 416000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Wanneer een sub-component of onderdeel van een order klaar is (bijvoorbeeld een Doomsday of Capital onderdeel via `ProductionTask`), wordt de bijbehorende BPC in EVE Online verbruikt. Hierdoor zakt de voorraad van de BPC in de corp blueprint library naar 0 (of minder dan vereist).
Voorheen vergeleek het systeem enkel `corp_stock < req`, waardoor verbruikte blueprints van reeds voltooide onderdelen ten onrechte als ontbrekend ("Missing") met een tekort ("Shortage") in de lijst 'Missing Blueprints' werden getoond.
Deze blueprints moeten niet als 'Missing' worden gemarkeerd, maar de status 'Used' krijgen met een tekort van 0 en niet meetellen voor de rode waarschuwingsteller.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reeds voltooide productieonderdelen koppelen aan hun corresponderende blueprint via `EveIndustryActivityProduct`.
- [x] #2 Wanneer `completed_runs >= req_runs`, toont de status in de tabel 'Missing Blueprints' een grijze 'Used' badge met checkmark.
- [x] #3 Het tekort ('Shortage') voor voltooide blueprints staat op 0 en is niet rood gemarkeerd.
- [x] #4 De rode tellerbadge in de tabknop 'Missing Blueprints' telt uitsluitend daadwerkelijk ontbrekende blueprints (`actual_missing_count`) en negeert 'Used' blueprints.
- [x] #5 In de tab 'ME & BPC Overrides' verdwijnt de rode waarschuwingsdriehoek voor voltooide blueprints en wordt een subtiele 'Used' badge getoond.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. In `industry_reforged/views/orders/quotes.py`:
   - Query alle voltooide `ProductionTask`s voor de order en eventuele split/sub-orders (`order.root_order.child_orders`).
   - Koppel `EveIndustryActivityProduct` om het aantal voltooide runs per blueprint te berekenen (`math.ceil(completed_quantity / yield_qty)`).
   - Bereken `remaining_runs = max(0, req_runs - completed_runs)` en `shortage = max(0, remaining_runs - stock_runs)`.
   - Markeer `is_used = True` en `shortage = 0` wanneer `completed_runs >= req_runs`.
   - Voeg alleen voltooide items met `stock < req` toe als `is_used` en hoog `actual_missing_count` enkel op voor `shortage > 0`.
   - Update `products_me` zodat `missing_bp = False` en `is_used = True` voor voltooide items.
2. In `industry_reforged/templates/industry_reforged/view_quote.html`:
   - Werk de tab header bij zodat de rode pill badge `actual_missing_count` gebruikt.
   - Voeg `Used` status badge toe aan de 'Missing Blueprints' tabel en toon shortage 0 zonder rode tekst.
   - Toon subtiele 'Used' badge in 'ME & BPC Overrides'.
3. Synchroniseer naar sandbox en herstart Gunicorn.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Geïmplementeerd in `quotes.py` en `view_quote.html`. Voltooide `ProductionTask`s worden nu direct gematcht aan vereiste BOM-blueprints. Reeds geproduceerde componenten waarvan de BPC verbruikt is tonen nu netjes status 'Used' met shortage 0, en beïnvloeden de 'Missing Blueprints' waarschuwingsteller niet langer.
<!-- SECTION:NOTES:END -->
