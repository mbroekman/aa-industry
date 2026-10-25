---
id: TASK-276
title: 'Buyback fase 4: member pages'
status: Done
assignee: []
created_date: '2026-10-25 12:42'
updated_date: '2026-10-25 14:06'
labels:
  - buyback
dependencies: []
priority: low
ordinal: 450000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Plan: C:/Users/mbroe/.claude/plans/write-a-detailed-plan-crispy-candle.md (buyback parity with allianceauth-buyback-program). Read-only rules & prices page; FAQ with frontend CRUD; manual contract refresh button.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
buyback_program_rules (read-only, visibility via visible_to, watchlist only for the program's corp directors); BuybackFaq per corporation with director CRUD on the Buyback tab + member FAQ page (built-in how-it-works + FAQs of visible programs' corps); director_buyback_refresh_contracts queues buyback_poll_contracts. Migration 0087. 473 tests green.
<!-- SECTION:NOTES:END -->
