---
id: TASK-14
title: Fix in_progress quantity showing as runs on dashboard
status: Done
assignee: []
created_date: '2026-08-04 18:21'
updated_date: '2026-08-04 18:21'
labels: []
dependencies: []
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Bugfix: Op het industrialist dashboard toonde de kolom 'In Progress (EVE)' voor sommige items (met name reacties) het aantal runs in plaats van de geproduceerde hoeveelheid.

**Oorzaak:**
Tijdens de automatische aanmaak van `ProductionTask`s in `bom_engine.py` werd de `activity_id` hardcoded op `1` gezet, ongeacht de werkelijke activiteit in EVE (zoals `11` voor Reactions). Hierdoor kon het dashboard later de `portion_size` niet ophalen uit de SDE (omdat de `activity_id` mismatchte), waardoor het terugviel op een portie van 1. Hierdoor werd `runs * 1` getoond in plaats van `runs * 10000`.

**Oplossing:**
In `bom_engine.py` is `get_sde_bom()` aangepast om de werkelijke `activity_id` uit de SDE mee terug te geven (1 of 11).
Daarna is de `get_recursive_bom_tree` functie aangepast zodat het deze `activity_id` dynamisch invult in de geretourneerde databoom, in plaats van de hardcoded `1`.
Daarnaast is er een Django shell script gedraaid dat 350 bestaande `ProductionTask`s retroactief heeft gerepareerd met de juiste `activity_id`s.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Reactions vertonen correcte in progress getallen
  Dashboard berekent `portion_size` niet langer default op 1 door mismatch in activity ID

<!-- AC:END -->
