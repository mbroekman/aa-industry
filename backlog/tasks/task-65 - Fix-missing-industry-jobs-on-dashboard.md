---
id: TASK-65
title: Fix missing industry jobs on dashboard
status: Done
assignee: []
created_date: '2026-08-13'
updated_date: '2026-08-13'
labels: ['bug']
dependencies: []
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Langlopende jobs (zoals Titans en Avatars) verdwijnen van het corporation industry dashboard, terwijl ze in EVE Online nog steeds actief zijn.
Dit wordt veroorzaakt door het ontbreken van paginatie bij de ESI API calls in combinatie met de ESI 90-dagen bug waarbij `include_completed=True` oudere actieve jobs weghaalt. Ook was de cleanup logica in de backend te agressief, doordat alle missende jobs direct als 'delivered' werden aangemerkt.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Implementeer paginatie in de ESI job calls.
- [x] #2 Voer de ESI calls twee keer uit per token: een keer met `include_completed=False` (om bugged active jobs mee te pakken) en `include_completed=True` (voor recent afgeronde).
- [x] #3 Zorg dat de agressieve cleanup logica is vervangen door een veiligere check gebaseerd op de `end_date` (> 90 dagen geleden) van de job.
- [x] #4 Schrijf een data migration script (`0043`) om bestaande gecorrumpeerde jobs in productie (jobs onterecht op 'delivered' terwijl `end_date` in de toekomst ligt) te herstellen naar 'active'.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

In `industry_reforged/tasks/jobs.py` zijn zowel `update_character_jobs` als `update_corporation_jobs` grondig aangepast.

1. Er is een loop toegevoegd die over `include_completed` [False, True] itereert.
1. Voor corporation jobs is een paginatie loop toegevoegd (ESI max 1.000 results) waarbij eventuele HTTPNotModified of 404 errors netjes worden opgevangen.
1. De regel die alle niet-gematchte actieve jobs direct `delivered` maakte, is vervangen door een SQL update die alleen jobs aanpast waarvan `end_date < timezone.now() - 90 dagen` geldt (om ESI behavior exact na te bootsen zonder risico voor actieve Titans).
1. `industry_reforged/migrations/0043_restore_active_titans_and_long_jobs.py` aangemaakt. Dit migratiescript corrigeert bestaande foutief "delivered" jobs waarvan de einddatum in de toekomst ligt door ze terug te zetten naar "active".

<!-- SECTION:NOTES:END -->
