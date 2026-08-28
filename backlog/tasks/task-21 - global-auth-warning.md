---
id: TASK-21
title: Globale Auth-niveau melding bij falende background jobs
status: Done
assignee: []
created_date: '2026-08-06 12:43'
updated_date: '2026-08-06 12:43'
labels: []
dependencies:
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

De eerdere popup (TASK-20) op de Director Dashboard is niet voldoende; als een achtergrond job faalt is dit kritisch en moet dit op **Auth niveau** (dus globaal op elke pagina in Alliance Auth) zichtbaar zijn voor directors, niet alleen wanneer ze toevallig de CP pagina bezoeken.

We injecteren deze globale waarschuwing door gebruik te maken van de `DirectorMenuItem` hook in `auth_hooks.py`. Hierdoor wordt op elke pagina in Alliance Auth gecontroleerd of er gefaalde taken zijn, en wordt er een globale popup/alert getoond.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Pas `DirectorMenuItem.render` aan in `auth_hooks.py`
- [x] #2 Controleer of er `FAILED` entries zijn in `TaskExecutionLog`
- [x] #3 Injecteer een fixed position (of toast) alert via JavaScript zodat deze op alle Auth pagina's verschijnt voor gebruikers met director rechten.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- In `industry_reforged/auth_hooks.py` hebben we `DirectorMenuItem.render` uitgebreid. Naast de standaard menu-generatie voegen we nu een `<script>` toe aan de HTML-output als er `TaskExecutionLog` entries op `FAILED` staan.
- Aangezien menu-items op elke pagina in Alliance Auth worden gerenderd, zal dit ervoor zorgen dat de waarschuwing (een rode toast/alert linksonder/rechtsonder) op **elke pagina** getoond wordt aan directors, totdat de taken gefixt zijn.

<!-- SECTION:NOTES:END -->
