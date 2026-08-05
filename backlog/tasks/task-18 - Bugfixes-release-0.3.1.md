---
id: TASK-18
title: Bugfixes release 0.3.1 (Job Market, PI Sync, Translations)
status: Done
assignee: []
created_date: '2026-08-05 16:00'
updated_date: '2026-08-05 16:48'
labels: []
dependencies: []
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Verhelpen van diverse kleine bugs gerapporteerd op 5 augustus 2026 voor release 0.3.1:

1. PI planet names ontbraken in de UI omdat ESI 304 Not Modified de synchronisatie van EvePlanet oversloeg.
1. Gettext python-format fout doordat procenttekens (%) werden gebruikt in translation strings.
1. Job market inspring-bug: top jobs kregen onterecht een uitklap-knop (minus button) en inspringing.
1. BOM Engine TypeError: `get_blueprint_me` gaf `None` terug als `manual_me` niet geconfigureerd was op een override.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 PI planet namen worden correct als fallback ingeladen als de server 304 geeft
- [x] #2 django-admin compilemessages faalt niet meer op %-tekens
- [x] #3 Job market items worden niet meer onterecht als parents/folders weergegeven als hun child-items toevallig in de Active Production tabel staan
- [x] #4 TypeError in `bom_engine.py` is opgelost door ME default waardes vooraf te berekenen als fallback

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- PI Sync: Fallback toegevoegd in de Pin loop zodat als `fetch_planet` wordt overgeslagen, we alsnog proberen de planeet via `EvePlanet.objects.get_or_create` op te halen.
- Translations: `%` vervangen door het woord "percentage" in de help_text strings in `orders.py`.
- Job Market: `industrialist_dashboard.html` JavaScript `parentIds` logica geïsoleerd met `$('table').each(...)` zodat parent/child status per tabel strikt lokaal blijft.
- BOM Engine: Logica in `bom_engine.py -> get_blueprint_me` geherstructureerd zodat `default_t1`/`default_t2` berekend wordt voordat de overrides worden gecontroleerd, om als veilige fallback te dienen.
- Changelog en versie geüpdatet naar 0.3.1.

<!-- SECTION:NOTES:END -->
