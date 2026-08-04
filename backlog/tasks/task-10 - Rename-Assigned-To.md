---
id: TASK-10
title: 'Hernoem "Assigned To" naar "Claimed By" in productie tabellen'
status: Done
assignee: []
created_date: '2026-08-03 19:00'
labels: []
dependencies: []
type: chore
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Op de verschillende overzichten (zoals Corp production tasks op het director dashboard en actieve/afgeronde taken op het industrialist dashboard) stonden de tabelkolommen gelabeld als "Assigned To". Omdat taken door bouwers zelf geclaimd worden in dit systeem, is "Claimed By" passender.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Tabel headers in dashboards voor productietaken zijn hernoemd naar "Claimed By".

<!-- AC:END -->

## Implementation Notes

De teksten in de tabellen zijn geüpdatet met de juiste vertalingstags. Aangepaste bestanden:

- `industry_reforged/templates/industry_reforged/director_dashboard.html`
- `industry_reforged/templates/industry_reforged/industrialist_dashboard.html`
