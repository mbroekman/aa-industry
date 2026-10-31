---
id: TASK-284
title: 'Orders tab: real In Production status, default filter and attention badges'
status: Done
assignee: []
created_date: '2026-10-31 07:59'
updated_date: '2026-10-31 08:09'
labels:
  - orders
  - ui
dependencies: []
ordinal: 458000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Member orders never get status IN_PRODUCTION (no code sets it), so the In Production filter on the director dashboard is always empty. Sync the order status from its tasks, rename the 'Active Member Orders' tab to 'Orders', default the list to In Production, and show clickable badges on the tab for new, quoted (not accepted) and unpaid orders that refresh the table in place.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Order moves ACCEPTED -> IN_PRODUCTION when a task of the order family is claimed/completed or a buy item is bought, and back to ACCEPTED when all claims are released
- [x] #2 Data migration fixes existing ACCEPTED orders that already have work started
- [x] #3 Tab renamed to Orders; list defaults to In Production with an explicit All option
- [x] #4 Tab shows badges for new, quoted and unpaid orders; clicking one filters the table without a page reload
- [x] #5 Tests cover status sync and the default filter
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added utils/order_status.py (sync_order_production_status) called from claim, unclaim, bulk claim/unclaim, complete and toggle bought. Migration 0093 moved existing orders (devauth: #279, #281 -> IN_PRODUCTION). Orders tab renamed, defaults to IN_PRODUCTION (explicit ALL option), badges for REQUESTED/QUOTED/UNPAID filter the DataTable in place via ajax.url().load(). UNPAID now means is_paid=False from ACCEPTED onwards. Tests: test_order_production_status.py; full suite 542 passed.
<!-- SECTION:FINAL_SUMMARY:END -->
