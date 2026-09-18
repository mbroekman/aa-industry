---
id: TASK-160
title: Include BPOs in Missing Blueprints Scanner check
status: In Progress
assignee: []
created_date: '2026-09-12 17:10'
updated_date: '2026-09-13 12:42'
labels: []
dependencies: []
ordinal: 336000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The missing blueprints list for Opportunity Scanners currently only checks for available BPCs. It should also check for BPOs, as items are often built directly from BPOs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Scanner checks both BPO and BPC availability for a blueprint, Missing Blueprint list excludes items where either a BPO or BPC is available
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Onderzocht de scanner code in ai_manager.py. Het lijkt erop dat CorpBlueprint.objects.filter() al alle eve_type_id's ophaalt (zowel BPO als BPC) en deze correct uitsluit van missing_types. Mogelijk is dit al zijdelings opgelost tijdens TASK-161. Wachtend op input van de gebruiker of er nog specifieke aanpassingen nodig zijn.
<!-- SECTION:NOTES:END -->
