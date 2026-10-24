---
id: TASK-268
title: >-
  Separate Missing Materials overview from the full BOM table on the order CP
  page
status: Done
assignee: []
created_date: '2026-10-24 14:56'
updated_date: '2026-10-24 14:56'
labels: []
dependencies: []
ordinal: 442000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Director feedback: buy-order selection shouldn't be mixed into the full Required Raw Materials cost breakdown - add a dedicated, pre-filtered Missing Materials card (shortfall>0 only) above it with the checkbox+Create Buy Order UI, and revert the full table back to a pure cost overview.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 New dedicated Missing Materials card on the order BOM tab, shown only when there is an actual shortage
- [x] #2 Checkboxes/select-all/Create Buy Order button live only on the new card, not on the full Required Raw Materials table
- [x] #3 Full Required Raw Materials table reverted to its original pure-overview markup (no checkboxes)
- [x] #4 create_buy_orders_from_order view unchanged/still correct regardless of which UI posts to it
- [x] #5 Full test suite green, ruff clean
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Director feedback (via AskUserQuestion) confirmed: wanted overview-first-then-buy-order as a SEPARATE section, not checkboxes mixed into the existing full cost-breakdown table. Added _filter_missing_materials(bom_materials_list) helper in views/orders/quotes.py, reused in both view_quote and the htmx_update_quote_facility partial-refresh path so the definition of 'missing' never drifts between full-page and facility-change-triggered renders. New card uses its own table id/checkbox classes (order-missing-materials-table / order-missing-material-checkbox) with its own simple DataTable, separate from the full table's custom grouping DataTable - reverted that table's checkbox column, dynamic colspan/column-index JS, and buy-order form back to their pre-TASK-265 state. create_buy_orders_from_order itself needed zero changes - it already recomputes shortfall fresh server-side regardless of which UI submits to it.
<!-- SECTION:NOTES:END -->
