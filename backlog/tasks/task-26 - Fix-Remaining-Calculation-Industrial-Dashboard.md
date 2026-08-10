---
id: TASK-26
title: Fix remaining calculation and EVE job matching on Industrialist Dashboard
status: Done
assignee: []
created_date: '2026-08-06 15:45'
updated_date: '2026-08-06 15:45'
labels: []
dependencies: []
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Op het Industrialist Dashboard in de 'Build Steps' / 'Claimed Jobs' tabel klopten de `Completed` en `Remaining` kolommen niet met de `To build` hoeveelheden. EVE jobs in progress werden ten onrechte in mindering gebracht op het `Remaining` veld, waardoor het resterende aantal om af te leveren onjuist werd weergegeven. Daarnaast werden EVE jobs niet op de juiste activiteit (bijv. Manufacturing vs Copying) gefilterd.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 EVE jobs (char/corp) moeten gefilterd worden op zowel `product_type_id` als `activity_id`.
- [x] #2 `Remaining` (resterend) moet enkel gebaseerd zijn op `to_build - completed` om aan te geven wat de speler nog in totaal moet afronden, in plaats van te corrigeren voor `in_progress`.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- Aangepast in `industry_reforged/views/industrialist.py`.
- Filter logica veranderd van `j.product_type_id == type_id` naar `j.product_type_id == type_id and j.activity_id == activity_id`.
- Berekening veranderd van `remaining = max(0, to_build - completed - in_progress)` naar `remaining = max(0, to_build - completed)`.

<!-- SECTION:NOTES:END -->
