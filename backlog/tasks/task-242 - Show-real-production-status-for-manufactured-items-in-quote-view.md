---
id: TASK-242
title: Show real production status for manufactured items in quote view
status: Done
assignee:
  - Antigravity
created_date: '2026-10-09 12:10'
updated_date: '2026-10-09 12:15'
labels:
  - feature
  - ui
dependencies: []
ordinal: 418000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In het orderdossier onder 'Order Details' (Itemized Invoice) en bijgesplitste child orders toont de kolom 'Status' voor alle te bouwen artikelen momenteel statisch de badge 'Manufactured'.
Dit wekt ten onrechte de indruk dat alle onderdelen reeds geproduceerd/voltooid zijn, terwijl sommige taken al 'Completed' zijn, anderen 'In Production' of nog 'Unclaimed'.
De kolom 'Status' moet voor te bouwen artikelen de daadwerkelijke productiestatus van de bijbehorende ProductionTask weergeven (Completed, In Production, Unclaimed, of To Build), inclusief wie het bouwt/heeft gebouwd en afrondingstijdstip in een tooltip.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `OrderItem` model uitbreiden met `build_status_info` property / helper om de actuele productiestatus te bepalen op basis van de gekoppelde `ProductionTask`(s).
- [x] #2 In `quotes.py` (`view_quote`) productietaken efficiënt vooraf koppelen aan de order items om N+1 database queries te voorkomen.
- [x] #3 In `view_quote.html` de statische badge 'Manufactured' vervangen door dynamische badges:
  - 'Completed' (groen) met tooltip (datum + bouwer) wanneer de taak voltooid is.
  - 'In Production' (blauw/info) met tooltip (bouwer) wanneer de taak geclaimd is.
  - 'Unclaimed' (geel/warning) wanneer de taak nog niet geclaimd is.
  - 'To Build' (grijs) wanneer de order nog in offerte-/aanvraagfase zit en er nog geen taken zijn aangemaakt.
- [x] #4 Dezelfde dynamische status badges toepassen in de child split orders tabel in `view_quote.html`.
- [x] #5 Unit tests schrijven en verifiëren.
- [x] #6 Wijzigingen synchroniseren naar de remote sandbox.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Model: Voeg `get_build_status()` en `@property build_status_info` toe aan `OrderItem` in `industry_reforged/models/orders.py`.
2. View: In `industry_reforged/views/orders/quotes.py` (`view_quote`), laad alle relevante taken van de orderfamilie vooraf in en ken de statusinfo efficiënt toe aan elk orderitem.
3. Template: Vervang in `industry_reforged/templates/industry_reforged/view_quote.html` de statische badge 'Manufactured' door de dynamische statusbadge (met tooltip bouwer en tijdstip).
4. Template: Doe hetzelfde voor de items in de child orders tabel.
5. Tests: Schrijf unit tests in `test_order_bought.py` om de weergave van de verschillende taakstatussen (COMPLETED, IN_PRODUCTION, UNCLAIMED, TO_BUILD) te valideren.
6. Sandbox: Synchroniseer naar de remote server en herstart webserver.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- In `OrderItem` is de methode `get_build_status()` en `@property build_status_info` toegevoegd, die de top-level productietaak van het item analyseert.
- `view_quote` in `quotes.py` haalt nu alle taken van de order en child orders in één bulk-query op en kent de status direct toe zonder N+1 overhead.
- In `view_quote.html` is de statische badge 'Manufactured' vervangen door contextuele badges:
  - `Completed` (groen, met voltooiingsdatum en wie het gebouwd heeft).
  - `In Production` (blauw/info, met bouwer die het geclaimd heeft).
  - `Unclaimed` (geel, met 'Waiting for builder' tooltip).
  - `To Build` (grijs, indien order nog niet in productie is).
- 11 unit tests in `test_order_bought.py` geslaagd.
- Wijzigingen direct gesynchroniseerd naar `devauth.spral.space` en geverifieerd via Gunicorn.
<!-- SECTION:NOTES:END -->
