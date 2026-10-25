---
id: TASK-275
title: 'Buyback fase 3: contract handling & notifications'
status: Done
assignee: []
created_date: '2026-10-25 12:42'
updated_date: '2026-10-25 13:55'
labels:
  - buyback
dependencies: []
priority: medium
ordinal: 449000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Plan: C:/Users/mbroe/.claude/plans/write-a-detailed-plan-crispy-candle.md (buyback parity with allianceauth-buyback-program). Seller note; price too high vs too low; untracked/suspicious contracts; per-program notification toggles + manager DM + AA notifications; member notification opt-out; ESI items vs appraisal side-by-side.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
seller_note (calculator, detail, review queue, webhook); price high = flag, low = note only (ContractMatchResult.price_low); BuybackUntrackedContract recorded once per ESI contract (prefix match, unknown tracking, outstanding, assigned to program recipient) + webhook/manager DM + review-queue list with dismiss; program toggles notify_new_contracts / notify_show_item_list / notify_manager_character; utils/buyback_notify.py central (DM + AA notify, BuybackUserSettings opt-out, dashboard bell); esi_items stored on match and compared on the contract page; watchlist_flag_notes now covers item groups (gap from phase 2). Migration 0086. 465 tests green.
<!-- SECTION:NOTES:END -->
