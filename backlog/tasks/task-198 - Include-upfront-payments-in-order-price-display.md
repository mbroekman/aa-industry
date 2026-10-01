---
id: TASK-198
title: Include upfront payments in order price display
status: Done
assignee: []
created_date: '2026-10-01 16:28'
updated_date: '2026-10-01 16:32'
labels: []
dependencies: []
ordinal: 374000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user reports that upfront payments (ISK or PLEX) are not taken into account when displaying the prices/remaining balance on the order. Need to update the template and view logic to correctly reflect payments.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Order view correctly subtracts upfront ISK payments from the remaining balance.
- [x] #2 Order view correctly subtracts upfront PLEX payments from the remaining balance.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added plex_isk_value deduction to remaining_balance property in MemberOrder. Added a new explicit row for 'Remaining Balance on Delivery' in view_quote.html so users can easily see their remaining payment.
<!-- SECTION:NOTES:END -->
