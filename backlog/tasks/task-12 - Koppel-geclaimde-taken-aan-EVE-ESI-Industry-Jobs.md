______________________________________________________________________

## id: TASK-12 title: Koppel geclaimde taken aan EVE ESI Industry Jobs status: To Do assignee: [] created_date: '2026-08-03 18:08' labels: [] dependencies: [] ordinal: 13000

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Onderzoek en implementatie om geaccepteerde (geclaimde) orders/taken in het systeem te koppelen aan de daadwerkelijke corporate of character industry jobs die in structures draaien (ingelezen via ESI).

**Belangrijke requirement:**
De koppeling moet er rekening mee houden dat een gebruiker een taak accepteert met zijn/haar main karakter, maar de EVE industry jobs gestart kunnen worden door de alts (andere karakters van dezelfde Alliance Auth User).

Er is reeds een Technisch Ontwerp geschreven met de heuristische aanpak (alt-herkenning via CharacterOwnership en matching op basis van tijd, type en activiteit). Zie hiervoor: backlog/docs/doc-1-Technisch-Ontwerp-Koppel-taken-aan-EVE-Jobs.md

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Er is een datamodel (TaskJobLink) om ProductionTask te koppelen aan industry jobs
  Er draait periodiek (via Celery) een heuristic matcher die nieuwe ESI-jobs koppelt
  Gebruikers kunnen in hun 'Mijn Taken' overzicht zien welke ESI jobs daadwerkelijk gekoppeld zijn
  (Optioneel) Als alle gekoppelde ESI jobs Delivered zijn krijgt de taak automatisch status Completed

<!-- AC:END -->
