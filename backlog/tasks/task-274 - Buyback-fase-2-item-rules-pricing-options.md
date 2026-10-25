---
id: TASK-274
title: 'Buyback fase 2: item rules & pricing options'
status: Done
assignee: []
created_date: '2026-10-25 12:42'
updated_date: '2026-10-25 13:40'
labels:
  - buyback
dependencies: []
priority: medium
ordinal: 448000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Plan: C:/Users/mbroe/.claude/plans/write-a-detailed-plan-crispy-candle.md (buyback parity with allianceauth-buyback-program). Item/market-group tax/discount/disallow rules; static prices; watchlist by group; allow_all_items; raw/compressed/refined ore toggles; T1 scrap value; NPC price toggles; hauling cost; compression density modifier; unpacked items; reject blueprints; reject whole appraisal option; per-item explanation.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Market-group rules as in the original (user choice), data per item on demand (user choice). New models BuybackItemRule (item or market group, modifier added to program's, disallow) and BuybackStaticPrice; watchlist by item group; program options allow_all_items, raw/compressed/refined ore toggles, T1 scrap (meta<=4 via dogma, own yield), 4 NPC price toggles (bonds bug of the original avoided), hauling ISK/m3 (+compressed volume option), allow_unpacked_items, reject_appraisal_on_disallowed. utils/buyback_data.py loads type_materials/dogmas/market_groups per pasted item via eveuniverse and remembers failures for a day; buyback_load_market_groups task behind a director button; EveMarketPrice refreshed in task_pull_market_data. Fixed reprocessing yield per portion (ore ~100x). Migration 0085. 449 tests green.
<!-- SECTION:NOTES:END -->
