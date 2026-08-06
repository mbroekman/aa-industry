---
id: TASK-19
title: Bugfixes release 0.3.2 (BOM Engine)
status: Done
assignee: []
created_date: '2026-08-06 11:00'
updated_date: '2026-08-06 11:00'
labels: []
dependencies: []
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Verhelpen van ME calculatie bugs in BOM Engine voor release 0.3.2:

1. BOM Engine TypeError: `get_blueprint_me` gaf `None` terug als `manual_me` niet geconfigureerd was op een override.
1. Faction blueprints moeten uitgesloten worden van ME berekeningen (ME = 0), net als reactions, omdat ze niet ME-onderzocht kunnen worden. Dit moet echter zonder de max_runs overrides over te slaan.
1. `FieldError` op shopping list: `activity_id` werd gezocht op `EveIndustryActivity` in plaats van `EveIndustryActivityDuration`.
1. `ImportError` in `tasks/wallets.py`: `EveCorporationInfo` werd lokaal geïmporteerd in plaats van uit `allianceauth.eveonline.models`.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 TypeError in `bom_engine.py` is opgelost door ME default waardes vooraf te berekenen als fallback
- [x] #2 Faction blueprints en reactions krijgen standaard ME = 0, maar eventuele handmatige `max_runs` overrides worden nog wel verwerkt
- [x] #3 `FieldError` op shopping list is opgelost door `EveIndustryActivityDuration` te gebruiken.
- [x] #4 `ImportError` op Celery wallet sync task is opgelost door de juiste import.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- BOM Engine: Logica in `bom_engine.py -> get_blueprint_me` geherstructureerd zodat `default_t1`/`default_t2` berekend wordt voordat de overrides worden gecontroleerd, om als veilige fallback te dienen bij missende overrides.
- BOM Engine: Logica aangepast zodat blueprints zonder ME-research activity expliciet `default_me = 0` krijgen. De check op `EveIndustryActivityDuration(activity_id=4)` bleek echter ook `True` terug te geven voor Faction BPCs zoals de Vindicator, doordat deze stiekem wél een duration in de SDE hebben. Daarom is de check uitgebreid: blueprints die niet op de markt beschikbaar zijn (waarbij `eve_market_group_id is None` en `is_invented=False`) worden nu correct herkend als Faction/Storyline BPCs en krijgen ME = 0.
- BOM Engine: Bugfix voor ontbrekende `activity_id` query opgelost door `EveIndustryActivityDuration` te bevragen in plaats van `EveIndustryActivity`.
- Taken: Bugfix voor `tasks/wallets.py` om `EveCorporationInfo` via Alliance Auth core in te laden in plaats van locale app models.
- Versie verhoogd naar 0.3.2 in `__init__.py`.

<!-- SECTION:NOTES:END -->
