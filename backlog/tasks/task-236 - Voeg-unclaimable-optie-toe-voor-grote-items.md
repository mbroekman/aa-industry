---
id: TASK-236
title: Voeg "unclaimable" optie toe voor grote items
status: Done
assignee:
  - Antigravity
created_date: '2026-10-06 19:53'
updated_date: '2026-10-06 19:59'
labels: []
dependencies: []
ordinal: 412000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Grote objecten zoals Capital ships (Erebus) hebben heel veel sub-onderdelen en worden vaak door de corp geassembleerd. Het is daarom niet wenselijk dat één speler de hele taak claimt. Door een "unclaimable" vlag toe te voegen aan de item configuratie en de gerelateerde ProductionTask, kunnen we de UI aanpassen zodat de parent-taak niet geclaimd kan worden, maar de sub-componenten wel. Dit moet de boomstructuur intact houden voor visualisatie.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Voeg veld is_unclaimable_parent (of soortgelijk) toe aan CorpItemConfig
- [ ] #2 Voeg vinkje toe in de Item Rules configuratie-UI (Director Dashboard)
- [ ] #3 Voeg veld is_claimable toe aan ProductionTask model
- [ ] #4 Zet is_claimable op False wanneer een task wordt aangemaakt en het item als unclaimable is geconfigureerd
- [ ] #5 Pas Industrialist Dashboard aan zodat unclaimable taken niet in de lijst staan, maar hun claimable children WEL (als top-level items)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add is_unclaimable_parent to CorpItemConfig. 2. Add is_claimable to ProductionTask. 3. Update CorpItemConfigForm and director_config.html. 4. In quotes.py build_tasks, set is_claimable=False if item is unclaimable. 5. In industrialist.py, update unclaimed_tasks_qs and my_tasks_qs to include is_claimable=True and allow tasks whose parent has is_claimable=False. 6. Make migrations and migrate.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented all requested features in models, views, and templates. Did not run 'makemigrations' because the local virtual environment was missing dependencies (aa_kanban). You will need to run 'python manage.py makemigrations industry_reforged' and 'python manage.py migrate' in your active environment.
<!-- SECTION:NOTES:END -->
