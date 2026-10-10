---
id: TASK-241
title: Mark buy products as bought on order
status: Done
assignee:
  - Antigravity
created_date: '2026-10-09 11:30'
updated_date: '2026-10-09 11:50'
labels:
  - feature
  - ui
dependencies: []
ordinal: 417000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In het orderdossier onder 'Order Details' (Itemized Invoice) worden artikelen die niet gebouwd kunnen worden (zoals Faction modules, implants of via item configuratie ingesteld als BUY) getoond onder de sectie 'Buy Products (Jita Price)'.
Momenteel ontbreekt de mogelijkheid om aan te geven of een van deze producten daadwerkelijk gekocht is door een bouwer of beheerder.
Er moet een optie komen om individuele koopproducten als 'Gekocht' (Bought) te markeren en te ontmarkeren, inclusief visuele statusindicator (badge), wie het gekocht heeft en op welke datum, en verwerking in de order-voortgang.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `OrderItem` model uitbreiden met `is_bought` (BooleanField), `bought_at` (DateTimeField) en `bought_by` (ForeignKey EveCharacter).
- [x] #2 Django databasemigratie (`0071_orderitem_is_bought_orderitem_bought_at_orderitem_bought_by.py`) aanmaken.
- [x] #3 Nieuw view endpoint `toggle_order_item_bought` met permissiecontrole (`corp_access` of `industrialist_access`) dat zowel AJAX JSON als form POST redirects ondersteunt.
- [x] #4 In `view_quote.html` bij 'Buy Products (Jita Price)' een duidelijke statusbadge ('Bought' vs 'To Buy') en een toggleknop ('Mark Bought' / 'Unmark') toevoegen.
- [x] #5 Bij gemarkeerde producten de koper en datum inzichtelijk maken (badge/tooltip).
- [x] #6 Order progressie (`MemberOrder.progress_percent` en sidebar weergave) laten meerekenen met voltooide koopproducten.
- [x] #7 Unit tests schrijven en verifiëren dat alle functionaliteit correct werkt.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Model: Voeg `is_bought`, `bought_at` en `bought_by` toe aan `OrderItem` in `industry_reforged/models/orders.py`.
2. Model: Update `progress_percent` in `MemberOrder` zodat gekochte `OrderItem`s ook meetellen in de order completion percentage wanneer er taken en/of koopproducten zijn.
3. Migratie: Genereer migratie `0071_orderitem_is_bought_orderitem_bought_at_orderitem_bought_by.py`.
4. View: Maak `toggle_order_item_bought` in `industry_reforged/views/orders/management.py` en registreer route in `industry_reforged/urls.py`.
5. Template: Pas `view_quote.html` aan om de knop en badges te renderen voor `buy_items`, inclusief AJAX call voor instant feedback zonder paginareload.
6. Template: Update `_order_details_sidebar.html` om voortgangsbalk te tonen wanneer er koopproducten zijn (ook als er geen `production_tasks` zijn).
7. Tests: Voeg tests toe in `industry_reforged/tests/` voor het togglen van `is_bought`, permissies en voortgangsberekening.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Model `OrderItem` uitgebreid met `is_bought`, `bought_at`, `bought_by` en property `is_buy_product`.
- `MemberOrder.progress_percent` berekent voortgang gecombineerd over zowel taken als te kopen producten: `(completed_tasks + bought_items) / (total_tasks + total_buy) * 100`.
- Endpoint `toggle_order_item_bought` toegevoegd (`POST /orders/items/<id>/toggle-bought/`) met permissiechecks voor industriëlen, beheerders of de order-eigenaar.
- In `view_quote.html` zijn interactieve badges en toggleknoppen toegevoegd met instant AJAX feedback en dynamische bijwerking van de order-voortgangsbalk zonder paginareload.
- 8 gerichte unit tests toegevoegd in `test_order_bought.py`, allemaal succesvol geverifieerd.
<!-- SECTION:NOTES:END -->
