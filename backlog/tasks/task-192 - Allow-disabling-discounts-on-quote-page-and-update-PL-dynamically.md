---
id: TASK-192
title: Allow disabling discounts on quote page and update P&L dynamically
status: Done
assignee: []
created_date: '2026-10-01 11:50'
updated_date: '2026-10-01 15:01'
labels: []
dependencies: []
ordinal: 368000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add an option to toggle corp discounts on the provide quote page for an order. Also, ensure the Profit & Loss section updates dynamically when the total sale price is manually adjusted.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Can toggle discounts on/off per order, P&L updates dynamically on price change
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added ignore_discounts to MemberOrder. Updated pricing_engine to skip applying discounts when ignore_discounts is True. Added checkbox to Provide Quote form that recalculates and updates the quote totals. Added javascript to dynamically recalculate Profit & Loss when suggested price is edited.
<!-- SECTION:NOTES:END -->
