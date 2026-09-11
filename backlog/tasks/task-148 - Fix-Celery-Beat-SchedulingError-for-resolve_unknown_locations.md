---
id: TASK-148
title: Fix Celery Beat SchedulingError for resolve_unknown_locations
status: Done
assignee: []
created_date: '2026-09-11 11:36'
updated_date: '2026-09-11 11:39'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 145000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Vooronderzoek
Celery Beat geeft bij opstarten de volgende foutmelding:
```
celery.beat.SchedulingError: Couldn't apply scheduled task industry_reforged_resolve_unknown_locations: resolve_unknown_locations() missing 1 required positional argument: 'location_ids'
```
In de Django database (`django_celery_beat.models.PeriodicTask`) staat een actieve periodic task genaamd `industry_reforged_resolve_unknown_locations` gekoppeld aan `industry_reforged.tasks.resolve_unknown_locations` met `args=[]` en `kwargs={}`.
In `myauth/myauth/settings/local.py` en `README.md` is deze taak niet geconfigureerd. In `aa-industry/AGENTS.md` staat expliciet:
> Helper tasks (tasks with required positional arguments, e.g. `resolve_unknown_locations(location_ids)`) must NOT be added to `CELERYBEAT_SCHEDULE`.
Omdat `DatabaseScheduler` in Alliance Auth records uit de database laadt, blijft Celery Beat proberen deze taak elke 30 minuten uit te voeren.

### Code-analyse
In `industry_reforged/tasks/utils.py` vereist `resolve_unknown_locations(location_ids)` verplicht het argument `location_ids`. Als dit ontbreekt faalt de argument check van Celery direct.

### Voorgestelde aanpassingen
1. In `industry_reforged/tasks/utils.py`: maak parameter `location_ids=None` optioneel. Indien `location_ids is None`, query de database naar `KnownLocation` records met lege of 'Unknown' namen (max 1000).
2. Verwijder of deactiveer de wees-taak `industry_reforged_resolve_unknown_locations` in `PeriodicTask` van `myauth`.
3. Verifieer dat Celery Beat zonder fouten start en draait.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 resolve_unknown_locations accepteert location_ids=None zonder TypeError
- [x] #2 resolve_unknown_locations zoekt bij location_ids=None automatisch onopgeloste KnownLocation records op
- [x] #3 Wees-PeriodicTask industry_reforged_resolve_unknown_locations is opgeruimd uit django_celery_beat
- [x] #4 Celery Beat start op zonder SchedulingError
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
1. industry_reforged/tasks/utils.py: parameter `location_ids=None` gemaakt. Als `location_ids is None`, worden automatisch maximaal 1000 onopgeloste KnownLocation records uit de DB opgehaald.
2. Wees-PeriodicTask `industry_reforged_resolve_unknown_locations` verwijderd uit `django_celery_beat.models.PeriodicTask` in `myauth`.
3. Unit tests toegevoegd in `industry_reforged/tests/test_tasks.py` voor `resolve_unknown_locations` (zowel leeg, met records, als met argumenten) - alle 4 tests geslaagd.
4. Celery beat startup geverifieerd via `celery -A myauth beat`: gestart en draait foutloos zonder SchedulingError.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fout opgelost: de taak `resolve_unknown_locations` faalt niet meer op ontbrekende argumenten en de achtergebleven PeriodicTask in de database is opgeruimd. Celery Beat start weer probleemloos.
<!-- SECTION:FINAL_SUMMARY:END -->
