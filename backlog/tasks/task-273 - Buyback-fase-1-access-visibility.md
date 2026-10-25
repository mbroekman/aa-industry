---
id: TASK-273
title: 'Buyback fase 1: access & visibility'
status: Done
assignee: []
created_date: '2026-10-25 12:42'
updated_date: '2026-10-25 13:04'
labels:
  - buyback
dependencies: []
priority: high
ordinal: 447000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Plan: C:/Users/mbroe/.claude/plans/write-a-detailed-plan-crispy-candle.md (buyback parity with allianceauth-buyback-program). Group/state restrictions enforced everywhere; optional public calculator per program; multiple drop-off locations; recipient corp or character (+ character contracts scope); per-program tracking prefix.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Program fields: facilities/known_locations M2M (data-migrated from the old FKs, 0083/0084), recipient_type/recipient_character, tracking_prefix, restricted_to_groups/states, is_public; BuybackContract.is_public_submission. BuybackProgram.objects.visible_to(user) used by dashboard, calculator (POST too), stats; contract detail only for owner or director of the program's corp. Public calculator/contract views in views/buyback/public.py, excluded in UrlHook and kept last in urls.py because AA's decorate_url_patterns returns at the first excluded view. Poller reads character contracts for character recipients. 422 tests green.
<!-- SECTION:NOTES:END -->
