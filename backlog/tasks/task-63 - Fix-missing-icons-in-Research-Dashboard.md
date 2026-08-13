---
id: TASK-63
title: Fix missing icons in Research Dashboard
status: Done
assignee: []
created_date: '2026-08-11'
updated_date: '2026-08-11'
labels: ['bug', 'ui']
dependencies: ['TASK-60']
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

De iconen in de nieuwe "Research & Invention" tab worden niet getoond en geven een fout. Waarschijnlijk wordt de image URL of het item_type niet goed opgebouwd in de template `personal_dashboard.html`.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Zoek uit waarom de iconen falen
- [x] #2 Repareer de icon rendering in de template

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Copied the robust `onerror` image fallback logic from the Manufacturing tabs to the Research & Invention tabs (`industry_reforged/templates/industry_reforged/personal_dashboard.html`). This ensures that blueprint icons correctly fall back to the `/bp` endpoint or generic item icon if the standard `/icon` endpoint returns a 404 from the EVE image server.

<!-- SECTION:NOTES:END -->
