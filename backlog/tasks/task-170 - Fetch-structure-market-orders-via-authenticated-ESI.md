---
id: TASK-170
title: Fetch structure market orders via authenticated ESI
status: Done
assignee: []
created_date: '2026-09-13 16:32'
updated_date: '2026-09-13 16:32'
labels: []
dependencies: []
ordinal: 346000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The get_market_stock function was using public ESI endpoints, which excluded player citadels. Added logic to use esi-markets.structure_markets.v1 tokens and fetch structure market orders with pagination when the location is an Upwell structure.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 get_market_stock correctly identifies citadels by ID, fetches orders via authenticated endpoint, handles pagination and filters by type_id

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated get_market_stock in ai_engine.py to use Token objects for authenticated fetching of Upwell structures.

<!-- SECTION:NOTES:END -->
