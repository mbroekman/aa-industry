---
id: TASK-279
title: 'Buyback: sell or reprocess advice per contract'
status: Done
assignee: []
created_date: '2026-10-25 18:27'
updated_date: '2026-10-27 10:26'
labels: []
dependencies: []
ordinal: 453000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per buyback-contract een advies (directors) of items beter verkocht of gereprocest kunnen worden: corp-instelbaar rendement/belasting, twee verkooproutes (direct/sell-order) met kosten, voorraadtekorten als eigen gebruik, materialenlijst. Plan: write-a-detailed-plan-crispy-candle.md
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
CorpReprocessingConfig (migration 0090) + form on Buyback tab; utils/reprocess_advice.py (sell instant/listed vs reprocess, whole portions, taxes/fees, stock shortages once per contract, slow-sale warning); utils/stock_needs.py extracted from inventory view; card on contract page (program directors) and Advice column in review queue. Result not cached separately: prices/velocity/materials are already cached.
<!-- SECTION:NOTES:END -->
