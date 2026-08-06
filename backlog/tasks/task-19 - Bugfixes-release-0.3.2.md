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

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 TypeError in `bom_engine.py` is opgelost door ME default waardes vooraf te berekenen als fallback
- [x] #2 Faction blueprints en reactions krijgen standaard ME = 0, maar eventuele handmatige `max_runs` overrides worden nog wel verwerkt

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- BOM Engine: Logica in `bom_engine.py -> get_blueprint_me` geherstructureerd zodat `default_t1`/`default_t2` berekend wordt voordat de overrides worden gecontroleerd, om als veilige fallback te dienen bij missende overrides.
- BOM Engine: Logica aangepast zodat blueprints zonder ME-research activity (zoals Faction) expliciet `default_me = 0` krijgen. De eerdere "vroege return" hiervoor is verwijderd, zodat de rest van de functie (zoals `max_runs` evaluatie) wel gewoon doorloopt voor deze types items.
- Versie verhoogd naar 0.3.2 in `__init__.py`.

<!-- SECTION:NOTES:END -->
