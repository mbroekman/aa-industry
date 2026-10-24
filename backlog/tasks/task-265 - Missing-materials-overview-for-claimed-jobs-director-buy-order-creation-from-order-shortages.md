---
id: TASK-265
title: >-
  Missing materials overview for claimed jobs + director buy-order creation from
  order shortages
status: Done
assignee: []
created_date: '2026-10-24 12:34'
updated_date: '2026-10-24 12:49'
labels: []
dependencies: []
ordinal: 439000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Industrialist side: show an always-visible 'Missing Materials' overview of the materials still needed to finish the member's own claimed (IN_PRODUCTION) jobs, using the existing calculate_tasks_bom BOM engine. Director/CP side: on the order detail page's existing Required Raw Materials table, add checkboxes to select one or more short materials and a 'Create Buy Order' action that spawns/merges CorpBuyOrder rows for just the shortfall quantity (required - corp stock).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Industrialist dashboard shows a Missing Materials tab/panel computed from the member's own claimed tasks, with shortage rows highlighted the same way the existing order BOM table does
- [x] #2 Order detail page's Required Raw Materials table has a director-only checkbox column + Create Buy Order button
- [x] #3 Creating a buy order from selected materials computes shortfall server-side (never trusts client quantities) and merges into an existing OPEN/IN_PROGRESS CorpBuyOrder for that item if one exists, else creates a new one
- [x] #4 New buy orders appear correctly on the existing Director Dashboard Buy Orders tab
- [x] #5 Full test suite green, ruff clean
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented: industrialist_dashboard.html gets a new 'Missing Materials' tab (badge shows shortage count) backed by views/industrialist.py calling the existing calculate_tasks_bom(my_tasks, corp_info=corporation) and attaching a server-computed shortfall=max(0, quantity-corp_stock) per material. On the order page, quote_bom_panes.html's Required Raw Materials table gets a director-only (corp_access) checkbox column (only on shortage rows) + select-all + 'Create Buy Order' button, posting selected type_ids to the new create_buy_orders_from_order view (views/orders/quotes.py, urls.py route orders/<id>/create-buy-orders/). That view recomputes calculate_order_bom(order) fresh server-side (never trusts client quantities), computes the shortfall per selected material, and merges it into an existing OPEN/IN_PROGRESS CorpBuyOrder for that item (quantity += shortfall) or creates a new one - new/updated rows show up automatically on the existing Director Dashboard Buy Orders tab, no changes needed there. DataTables grouping JS in quote_bom_panes.html made column-index/colspan dynamic (bomGroupColIndex/bomGroupColspan) to account for the new leading checkbox column only appearing for corp_access viewers. No new models/migrations needed - CorpBuyOrder already had every field required. New test file test_missing_materials_buy_orders.py (7 tests): shortage highlighting/count on the industrialist dashboard, shortfall-only buy-order creation, merge-into-existing-open-order behaviour, corp_access permission enforcement, empty-selection and GET-request no-ops. Full suite 345/345 green, ruff clean on all changed files (quotes.py's pre-existing unrelated ruff findings elsewhere in that file predate this change, confirmed via diff against HEAD). Not yet deployed/verified live on devauth.
<!-- SECTION:NOTES:END -->
