---
id: TASK-193
title: Add PLEX as upfront payment option on quotes
status: Done
assignee: []
created_date: '2026-10-01 12:27'
updated_date: '2026-10-01 15:01'
labels: []
dependencies: []
ordinal: 369000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Allow directors to specify upfront payment in PLEX instead of or alongside ISK. The UI should display the current Jita value of 1 PLEX and dynamically calculate the total ISK value of the entered PLEX amount.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 PLEX upfront payment input added to Provide Quote form.,Current ISK value of 1 PLEX displayed.,Dynamic calculation of total ISK value of entered PLEX.,Order model updated to store PLEX payment amount.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added upfront_payment_plex field to MemberOrder. Fetched PLEX market price and injected into quote context. Added PLEX input field and dynamic ISK valuation to Provide Quote form.
<!-- SECTION:NOTES:END -->
