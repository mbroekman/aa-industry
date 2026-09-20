---
id: TASK-168
title: Fix Foreign Key constraint in scan_market_opportunities
status: Done
assignee: []
created_date: '2026-09-13 14:47'
updated_date: '2026-09-13 14:47'
labels: []
dependencies: []
ordinal: 344000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

MarketOpportunity creation was using the EVE corporation_id instead of the EveCorporationInfo database Primary Key.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 scan_market_opportunities correctly maps EVE corp id to EveCorporationInfo PK for all MarketOpportunity operations

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Fetched EveCorporationInfo explicitly by corporation_id (EVE ID) and assigned the resulting object to the 'corporation' field of MarketOpportunity and Basket models.

<!-- SECTION:NOTES:END -->
