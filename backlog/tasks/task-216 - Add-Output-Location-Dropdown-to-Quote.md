---
id: TASK-216
title: Add Output Location Dropdown to Quote
status: Done
assignee: []
created_date: '2026-10-05 15:57'
updated_date: '2026-10-05 16:09'
labels: []
dependencies: []
ordinal: 392000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1. Add a dropdown to the Quote view to select the Output Location.\n2. Add a list of Output Locations to settings, allowing the user to configure them, and the ability to add new ones directly while quoting.\n3. Add a suggested output container name that incorporates the order number and the name of the user who ordered it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 - Quotes have an Output Location dropdown.\n- Director settings has a configurable list of Output Locations.\n- New locations can be added directly from the Quote UI.\n- Suggested container name uses order number and orderer name.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
1. Created OutputLocation model, linked to MemberOrder. 2. Updated view_quote.html to show location/container fields with suggested value functionality. 3. provide_quote handles dynamic creation of new output locations. 4. Display output locations on sidebar and order table.
<!-- SECTION:NOTES:END -->
