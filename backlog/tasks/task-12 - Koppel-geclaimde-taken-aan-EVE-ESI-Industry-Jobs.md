---
id: TASK-12
title: Koppel geclaimde taken aan EVE ESI Industry Jobs
status: Done
assignee: []
created_date: '2026-08-03 18:08'
labels: []
dependencies: []
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Onderzoek en implementatie om geaccepteerde (geclaimde) orders/taken in het systeem te koppelen aan de daadwerkelijke corporate of character industry jobs die in structures draaien (ingelezen via ESI).

**Belangrijke requirement:**
De koppeling moet er rekening mee houden dat een gebruiker een taak accepteert met zijn/haar main karakter, maar de EVE industry jobs gestart kunnen worden door de alts (andere karakters van dezelfde Alliance Auth User).

Er is reeds een Technisch Ontwerp geschreven met de heuristische aanpak (alt-herkenning via CharacterOwnership en matching op basis van tijd, type en activiteit). Zie hiervoor: backlog/docs/doc-1-Technisch-Ontwerp-Koppel-taken-aan-EVE-Jobs.md

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Er is een datamodel (TaskJobLink) om ProductionTask te koppelen aan industry jobs
  Er draait periodiek (via Celery) een heuristic matcher die nieuwe ESI-jobs koppelt
  Gebruikers kunnen in hun 'Mijn Taken' overzicht zien welke ESI jobs daadwerkelijk gekoppeld zijn
  (Optioneel) Als alle gekoppelde ESI jobs Delivered zijn krijgt de taak automatisch status Completed

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- Nieuw model `TaskJobLink` aangemaakt in `models/jobs.py` met koppeling naar Char/Corp job.
- Nieuwe Celery task `link_orphaned_jobs_to_tasks` aangemaakt in `tasks/jobs.py` die opgeroepen wordt via `.delay()` aan het einde van ESI sync.
- `my_tasks_qs` prefetch_related geüpdatet voor UI optimalisatie.
- UI toont nu badges per gekoppelde job (status + runs).

<!-- SECTION:NOTES:END -->
