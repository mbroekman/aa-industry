---
id: TASK-7
title: 'Verwijder doorgestreepte tekst bij voltooide member tasks'
status: Done
assignee: []
created_date: '2026-08-02 10:40'
updated_date: '2026-08-02 10:40'
labels: []
dependencies: []
type: chore
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Bij voltooide taken in het overzicht van een lid (member task) wordt de naam van het item momenteel doorgestreept (strikethrough) weergegeven.
De wens is om deze tekst normaal (niet doorgestreept) weer te geven, zodat het beter leesbaar blijft.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Voltooide taken (completed tasks) in het member dashboard hebben geen doorgestreepte tekst meer bij de item naam.

<!-- AC:END -->

## Implementation Notes

**Onderzoeksresultaten & Plan van Aanpak:**

1. **Bestand**: `industry_reforged/templates/industry_reforged/industrialist_dashboard.html`
1. **Locatie**: Rond regel 325, in de `<tbody>` tabelweergave van de `my_completed_tasks` loop.
1. **Wijziging**: Verwijder de Bootstrap CSS-klasse `text-decoration-line-through` uit het `<span>` element dat `{{ task.item_type.name }}` weergeeft.
