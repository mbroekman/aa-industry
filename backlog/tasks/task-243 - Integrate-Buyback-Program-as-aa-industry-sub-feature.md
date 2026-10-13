---
id: TASK-243
title: Integrate Buyback Program as aa-industry sub-feature
status: To Do
assignee: []
created_date: '2026-10-13 08:27'
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
- [ ] #1 Read backlog/docs/doc-18 in full before starting any implementation
- [ ] #2 New BuybackMenuItem registered in auth_hooks.py following the existing MenuItemHook pattern, gated on industry_reforged.basic_access (member-visible, no new permission needed)
- [ ] #3 Manager/config views gated on the existing industry_reforged.corp_access permission (not the broken/undeclared director_access codename)
- [ ] #4 New models/buyback.py, views/buyback.py, tasks/buyback.py added following the existing per-feature-module convention; no separate app/UrlHook
- [ ] #5 Reuses IndustryFacility/KnownLocation for locations and LedgerTransaction for payout tracking instead of porting the source project's own Location/payment models
- [ ] #6 Pricing reuses or extends utils/pricing_engine.py rather than porting a second, parallel pricing engine
- [ ] #7 Contract-matching/abuse-detection logic ported with tests (the source project's best-tested part); inventory-paste parser rewritten with proper unit tests (untested in source)
- [ ] #8 Frontend-configurable (director_config-style form), not Django admin, per ADR-006
- [ ] #9 Do not import or run the source project's committed alliance_auth.sqlite3 file
<!-- AC:END -->
