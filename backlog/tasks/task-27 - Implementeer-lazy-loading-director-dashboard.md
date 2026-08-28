---
id: TASK-27
title: Implementeer lazy loading (AJAX server-side) voor Director Dashboard tabellen
status: Done
assignee: []
created_date: '2026-08-07 08:30'
updated_date: '2026-08-07 11:52'
labels:
dependencies: []
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

De performance van het Director Dashboard is onder de maat bij grote hoeveelheden active member orders en tasks. Omdat alle data in één keer door Django wordt ingeladen in het template context object (en daarna in enorme HTML-tabellen wordt geplaatst), wordt de responstijd van de server traag en het DOM object voor de browser enorm zwaar.

Hoewel DataTables momenteel wordt gebruikt voor paginering aan de front-end, laadt de server nog steeds alle data in de achtergrond. Dit moet worden omgezet naar DataTables Server-Side Processing (AJAX / Lazy Loading) zodat de database (via Django ORM) uitsluitend de rijen inlaadt die nodig zijn voor de huidige weergave (bijv. 10 of 25 per keer).

Dit betreft in elk geval de tabellen voor:

- Member Orders
- Production Tasks
- Buy Orders

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Er zijn nieuwe JSON data-endpoints (views) gebouwd die het DataTables server-side request format accepteren (draw, start, length) en een JSON-antwoord teruggeven.
- [ ] #2 De HTML-templates voor het Director Dashboard initialiseren DataTables nu met `serverSide: true` en `ajax: "..."` in plaats van direct HTML rijen te renderen via de Jinja/Django context.
- [ ] #3 Zoeken (zoekbalk) en sorteren (op kolommen klikken) werken correct via de ORM binnen de nieuwe AJAX endpoints.
- [ ] #4 De paginalaadtijd van het Director Dashboard is significant korter en de pagina is direct responsive.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Nog niet gestart.

<!-- SECTION:NOTES:END -->
