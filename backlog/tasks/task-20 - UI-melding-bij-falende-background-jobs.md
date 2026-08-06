---
id: TASK-20
title: UI melding bij falende background jobs (Director Dashboard)
status: Done
assignee: []
created_date: '2026-08-06 12:35'
updated_date: '2026-08-06 12:35'
labels: []
dependencies: []
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Als er een fout optreedt in één van de background jobs (zoals vastgelegd in `TaskExecutionLog` met status = `FAILED`), moet er automatisch een popup of melding (slide in) getoond worden op het moment dat een gebruiker (director) de Control Panel / Director Dashboard pagina bezoekt.

Deze melding moet een link bevatten naar de configuratie-overzichtspagina (`director_config`), waar de specifieke status van de background taken ingezien kan worden.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Er wordt gecontroleerd op `FAILED` entries in `TaskExecutionLog` bij het laden van `director_dashboard`
- [x] #2 Als er een foutieve log entry is, wordt er een UI melding (via Django `messages` framework) weergegeven aan de director
- [x] #3 De melding bevat een duidelijke link naar de task execution logs op de `director_config` pagina

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- In `industry_reforged/views/director.py` is een check toegevoegd die zoekt naar `TaskExecutionLog.objects.filter(status="FAILED").exists()`.
- Als dat het geval is, wordt `django.contrib.messages.error()` gebruikt in combinatie met `format_html` en `reverse` om de gebruiker een popup met link naar `/director/config/#task-logs-pane` te tonen.

<!-- SECTION:NOTES:END -->
