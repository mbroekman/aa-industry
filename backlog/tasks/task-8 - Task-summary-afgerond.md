______________________________________________________________________

## id: TASK-8 title: 'Task summary overzicht: Toon ook afgeronde taken' status: Done assignee: [] created_date: '2026-08-02 10:50' labels: [] dependencies: [] type: feature ordinal: 9000

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Het "Task Summary" overzicht op het Industrialist dashboard toont momenteel alleen taken met de status "IN_PRODUCTION".
Gebruikers willen ook kunnen zien welke taken zij in het verleden hebben afgerond.
Er moet een selectiemogelijkheid/filter komen in het overzicht (bijv. Actief, Afgerond, Alles) zodat gebruikers eenvoudig kunnen inzien wat ze al gedaan hebben.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Het Task Summary overzicht kan afgeronde taken (COMPLETED) tonen.
- [x] #2 Gebruikers kunnen via een filter/selectie kiezen of ze Actieve, Afgeronde, of Alle taken willen zien.
- [x] #3 De totalen (Claimed, In Progress, Completed, Remaining) kloppen nog steeds per geselecteerd item type.

<!-- AC:END -->

## Implementation Notes

**Onderzoeksresultaten & Plan van Aanpak:**

1. **Backend (`industry_reforged/views/industrialist.py`)**:

   - `claimed_grouped` en `completed_grouped` queries zijn samengevoegd in één query `all_tasks_grouped` die `ProductionTask` objecten ophaalt met status in `["IN_PRODUCTION", "COMPLETED"]`.
   - Via Django's `Sum` en `Q` (filter) worden direct `total_claimed` (voor IN_PRODUCTION) en `total_completed` gesommeerd.
   - De berekening voor `remaining` kijkt nog steeds correct naar in productie min wat al fysiek op het industriepanel staat (in_progress).

1. **Frontend (`industry_reforged/templates/industry_reforged/industrialist_dashboard.html`)**:

   - Een HTML `<select>` dropdown (Active, Completed, All) is toegevoegd naast de "Task Summary" header.
   - De tabelrijen `<tr>` hebben een `data-status="active|completed"` attribuut gekregen. Dit wordt bepaald door of `remaining <= 0` (completed) of anders (active).
   - Er is een kleine Javascript-functie `filterSummaryTable()` toegevoegd die de tabel direct lokaal filtert op basis van de geselecteerde dropdown-waarde. Deze functie draait ook op `DOMContentLoaded`.
