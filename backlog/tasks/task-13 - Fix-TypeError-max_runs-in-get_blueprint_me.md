---
id: TASK-13
title: Fix TypeError max_runs in get_blueprint_me
status: Done
assignee: []
created_date: '2026-08-03 19:11'
updated_date: '2026-08-03 19:13'
labels: []
dependencies: []
type: bug
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Bugfix voor TypeError: `'>' not supported between instances of 'NoneType' and 'int'`.

**Oorzaak:**
Tijdens de implementatie van TASK-6 retourneerde `get_blueprint_me()` voor items zonder blueprint `(0, None)` in plaats van `(0, 0)`. Dit zorgde ervoor dat in `bom_engine.py` bij de chunking logica (`if max_runs > 0`) een TypeError optrad als er een quote werd berekend.

**Oplossing:**
In `industry_reforged/utils/bom_engine.py` regel 147 de return waarde aangepast naar `return 0, 0`.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 De quote view (/industry/orders/<id>/) crasht niet meer met een TypeError

<!-- AC:END -->
