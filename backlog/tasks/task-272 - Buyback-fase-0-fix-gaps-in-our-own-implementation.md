---
id: TASK-272
title: 'Buyback fase 0: fix gaps in our own implementation'
status: Done
assignee: []
created_date: '2026-10-25 12:42'
updated_date: '2026-10-25 12:49'
labels:
  - buyback
dependencies: []
priority: high
ordinal: 446000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Plan: C:/Users/mbroe/.claude/plans/write-a-detailed-plan-crispy-candle.md (buyback parity with allianceauth-buyback-program). Corp-scope director views + POST-only deletes; enforce accepted_categories; watchlist flag marks contract; follow ESI contract status (finished->PAID+ledger, rejected/deleted/expired); webhook only on status change; DM on payout; reprocessed materials priced per price_type; drop unused ACCEPTED status; set is_esi_verified.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Corp-scoped director views (+POST-only deletes, protected delete of programs with contracts); poller matches once then follows ESI status (finished->mark_paid, rejected, withdrawn->PENDING, in-game expiry); BuybackContract.mark_paid() shared with Pay button; webhook only on transition; watchlist flag mode sets flag_watchlist/FLAGGED; accepted_categories enforced with blocked_reason; reprocessing priced per price_type; ACCEPTED status removed; is_esi_verified set. Migration 0082. 397 tests green.
<!-- SECTION:NOTES:END -->
