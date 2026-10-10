---
id: TASK-237
title: Fix Build Steps not removing in progress from to build amount
status: Done
assignee:
  - Antigravity
created_date: '2026-10-07 16:55'
updated_date: '2026-10-07 16:55'
labels:
  - bug
dependencies: []
ordinal: 413000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Op het Industrialist Dashboard onder de tab 'Build Steps' toont de kolom 'To Build' momenteel het totale aantal geclaimde items (`t.quantity`), in plaats van het resterende aantal dat nog gebouwd moet worden. Wanneer een EVE Industry Job 'In Progress' is (of al voltooid/geleverd is), wordt deze hoeveelheid niet afgetrokken van het 'To Build' getal. Hierdoor blijft 'To Build' op het totale geclaimde aantal staan, waardoor 'To Build' + 'In Progress' + 'Completed' optelt tot meer dan het geclaimde totaal.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 'To Build' kolom in Build Steps toont het daadwerkelijk resterende aantal (`remaining`), waarbij actieve en gereedstaande banen ('In Progress') en voltooide banen ('Completed') correct zijn afgetrokken.
- [x] #2 De som klopt: To Build (remaining) + In Progress + Completed = Claimed totaal.
- [x] #3 Tooltip toegevoegd zodat het oorspronkelijke geclaimde totaal inzichtelijk blijft bij hovering over 'To Build'.
- [x] #4 Voortgangsbalk en filtering (Active, Ready, Completed, All) blijven correct functioneren.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. In `industry_reforged/views/industrialist.py`:
   - Bewaar het totale geclaimde aantal in `claimed = sum(t.quantity for t in tasks_to_summarize)`.
   - Update `sum_item["to_build"] = remaining` en voeg `"claimed": claimed` toe aan de dictionary.
   - Behoud de berekening van `completed = max(0, claimed - in_progress - remaining)` en `progress_percent = (completed / claimed * 100) if claimed > 0 else 100`.
2. In `industry_reforged/templates/industry_reforged/industrialist_dashboard.html`:
   - In tabelrij `#summary-view-table` een title/tooltip toevoegen aan de 'To Build' cel (`title="Claimed: {{ sum_item.claimed }}"`).
   - In het uitgecommentarieerde backup-blok `#summary-view-table-old` de cel `{{ sum_item.to_build }}` aanpassen naar `{{ sum_item.claimed }}` voor de kolom "Claimed".
3. Verifiëren op de server via de live watcher en herstarten van services.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Toegepast in `views/industrialist.py` en `industrialist_dashboard.html`. 'to_build' in de Build Steps samenvatting toont nu accuraat `remaining` (waarbij zowel In Progress als Completed zijn afgetrokken). Het totale geclaimde aantal blijft bewaard en is zichtbaar via hover-tooltip `title="Claimed: X"`. Live gesynchroniseerd naar devauth.spral.space en geverifieerd via supervisor reload.
<!-- SECTION:NOTES:END -->
