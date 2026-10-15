---
id: TASK-243
title: Integrate Buyback Program as aa-industry sub-feature
status: Done
assignee: []
created_date: '2026-10-13 08:27'
updated_date: '2026-10-15 20:02'
labels: []
dependencies: []
ordinal: 419000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port the concept (not the code) of the third-party allianceauth-buyback-program plugin into industry_reforged as a new sub-feature, available to all members via a menu item gated on the existing basic_access permission. Full analysis, code-quality findings, and integration plan documented in backlog/docs/doc-18 (Feature Proposal: Buyback Program Integration) -- read that doc in full before starting. Source project analyzed: a downloaded snapshot at C:\Users\mbroe\Downloads\allianceauth-buyback-program-master (no git history included).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Read backlog/docs/doc-18 in full before starting any implementation
- [x] #2 New BuybackMenuItem registered in auth_hooks.py following the existing MenuItemHook pattern, gated on industry_reforged.basic_access (member-visible, no new permission needed)
- [x] #3 Manager/config views gated on the existing industry_reforged.corp_access permission (not the broken/undeclared director_access codename)
- [x] #4 New models/buyback.py, views/buyback.py, tasks/buyback.py added following the existing per-feature-module convention; no separate app/UrlHook
- [x] #5 Reuses IndustryFacility/KnownLocation for locations and LedgerTransaction for payout tracking instead of porting the source project's own Location/payment models
- [x] #6 Pricing reuses or extends utils/pricing_engine.py rather than porting a second, parallel pricing engine
- [x] #7 Contract-matching/abuse-detection logic ported with tests (the source project's best-tested part); inventory-paste parser rewritten with proper unit tests (untested in source)
- [x] #8 Frontend-configurable (director_config-style form), not Django admin, per ADR-006
- [x] #9 Do not import or run the source project's committed alliance_auth.sqlite3 file
<!-- AC:END -->

## Implementation Notes

Delivered the **normal buyback flow only** (paste inventory -> appraisal -> tracking number -> in-game contract -> ESI polling/matching -> director payout), per an explicit scoping decision made during planning: reverse buyback (corp selling hangar stock to members), public/anonymous per-program access, and the stats/leaderboard dashboard were deferred to a follow-up task, since they are the largest and most separable pieces of the source project's scope and the contract-matching engine (the part that moves real ISK) deserved a production review cycle on its own first.

New/changed files: `models/buyback.py` (BuybackProgram, BuybackWatchlistItem, BuybackContract, BuybackContractItem), `utils/inventory_parser.py`, `utils/buyback_matching.py` (pure, independently-tested contract-matching logic), `utils/pricing_engine.py` (appraisal functions appended), `tasks/buyback.py` (`buyback_poll_contracts` every 15 min, `buyback_purge_stale_contracts` daily), `views/buyback/` package (`member.py`, `director.py`), new "Buyback" tab on Director Configurations + a separate review queue page, migration `0072`. 69 new tests across `test_inventory_parser.py`, `test_buyback_pricing.py`, `test_buyback_matching.py`, `test_buyback_tasks.py`, `test_buyback_views.py`, `test_buyback_director_views.py` - full suite (233 tests) green.
