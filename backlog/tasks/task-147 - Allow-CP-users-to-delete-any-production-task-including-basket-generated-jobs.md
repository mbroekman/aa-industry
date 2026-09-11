---
id: TASK-147
title: Allow CP users to delete any production task (including basket-generated jobs)
status: Done
assignee: []
created_date: '2026-09-10 19:50'
updated_date: '2026-09-10 20:21'
labels: []
dependencies: []
priority: high
type: enhancement
ordinal: 144000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Gebruikers met Corporation Permissions (CP / corp_access) moeten in staat zijn om elke ProductionTask te verwijderen, inclusief jobs die automatisch zijn aangemaakt door een Basket (AI Market Manager).

### Analyse & Doel:
- AI Market Manager (evaluate_baskets) maakt ProductionTasks aan (`created_from_order=None`).
- Zorg dat een CP/Director-gebruiker via de interface en endpoints alle jobs/taken kan verwijderen.
- Zorg voor duidelijke foutafhandeling en feedback in de UI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CP-gebruikers (met corp_access permissie) kunnen elke ProductionTask verwijderen, inclusief basket-gegenereerde jobs
- [x] #2 Verwijderknop/actie is beschikbaar en functioneel voor basket-taken
- [x] #3 Niet-geautoriseerde gebruikers zonder CP-rechten kunnen geen taken verwijderen
- [x] #4 Tests dekken het verwijderen van basket-gegenereerde taken door CP-gebruikers af
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Geïmplementeerd:
- `delete_production_task` uitgebreid in `views/director.py` om ook sub-tasks op te ruimen (`task.bom_children.all().delete()`) en netjes terug te redirecten naar de aanroepende pagina via referer.
- `bulk_delete_tasks` view toegevoegd voor CP gebruikers (`industry_reforged.corp_access`) in `views/director.py` en gerouteerd in `urls.py`.
- UI uitgebreid in `industrialist_dashboard.html` zodat CP gebruikers taken (Available / Unclaimed jobs en Active claimed jobs) direct individueel kunnen verwijderen of via bulk selectie.
- Unit tests toegevoegd in `tests/test_task_deletion.py` (4 tests) en geintegreerd in `test_all_urls.py`. Alle 139 tests slagen.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
CP gebruikers kunnen nu alle production tasks (inclusief basket-gegenereerde taken) verwijderen via de interface (zowel individueel als via bulk delete), met volledige permissievalidatie en tests.
<!-- SECTION:FINAL_SUMMARY:END -->
