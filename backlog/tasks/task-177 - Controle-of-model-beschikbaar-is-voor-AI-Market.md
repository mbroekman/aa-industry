---
id: TASK-177
title: Controle of model beschikbaar is voor AI Market
status: Done
assignee: []
created_date: '2026-09-26 18:35'
updated_date: '2026-09-26 18:39'
labels: []
dependencies: []
ordinal: 353000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Er moet een check komen of het model beschikbaar is voor de AI Market. Als het model niet beschikbaar is, moet er een foutmelding worden getoond, vergelijkbaar met de melding die nu verschijnt wanneer een celery job faalt.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 - Er is een validatie ingebouwd die controleert of het model beschikbaar is voor AI Market., - Bij afwezigheid/onbeschikbaarheid van het model, wordt er een duidelijke foutmelding getoond in de UI (in dezelfde stijl als een celery job failure).
- [ ] #2 Er is een validatie ingebouwd die controleert of het model beschikbaar is voor AI Market.
- [ ] #3 Bij afwezigheid/onbeschikbaarheid van het model, wordt er een duidelijke foutmelding getoond in de UI (in dezelfde stijl als een celery job failure).
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Toegevoegd een availability check in ai_market_manager_dashboard via request module naar INDUSTRY_REFORGED_AI_URL met een timeout. Als deze faalt toont het een 'messages.error' in de UI.
<!-- SECTION:NOTES:END -->
