---
id: TASK-5
title: 'Fix bug: Fort is seen as type tatara'
status: Done
assignee: []
created_date: '2026-07-31 12:59'
updated_date: '2026-07-31 12:59'
labels: []
dependencies: []
type: bug
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The system is currently misidentifying a fort as a tatara type instead of recognizing it correctly.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 A fort is correctly identified as a fort in the system.
- [x] #2 A fort is no longer identified as a tatara.

<!-- AC:END -->

## Implementation Notes

**Oorzaak & Oplossing:**
De ID's voor de structure types klopten niet in `industry_reforged/models/facilities.py`. De EVE Type ID's voor Astrahus, Athanor, Fortizar en Tatara stonden door elkaar. Dit is nu gecorrigeerd door de correcte mapping toe te passen:

- 35832: Astrahus
- 35833: Fortizar
- 35835: Athanor
- 35836: Tatara
