______________________________________________________________________

## id: TASK-15 title: Verbeteringen Industrialist Dashboard UI (Groepering en tabnamen) status: Done assignee: [] created_date: '2026-08-04 18:55' updated_date: '2026-08-04 18:55' labels: [] dependencies: [] ordinal: 16000

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

UI/UX updates voor het industrialist dashboard:

- Tabblad 'Member Tasks' hernoemd naar 'Claimed Jobs'.
- Tabblad 'Task Summary' hernoemd naar 'Build Steps'.
- Het overzicht in 'Build Steps' wordt nu visueel gegroepeerd per type activiteit (bijv. Reactions, Manufacturing) in plaats van een platte alfabetische lijst, zodat het veel overzichtelijker is en de benodigde stappen duidelijker zijn.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Tabbladen hebben intuïtievere namen
  Build Steps lijst is gegroepeerd via Django regroup op activity_name

<!-- AC:END -->
