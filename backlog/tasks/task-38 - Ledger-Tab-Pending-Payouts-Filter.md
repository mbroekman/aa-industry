---
id: TASK-38
title: Ledger Tab Pending Payouts Filter
status: Done
assignee: []
created_date: '2026-08-07 14:27'
updated_date: '2026-08-07 14:27'
labels: []
dependencies: []
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Add pending builder payouts and a filter dropdown to the Ledger Transactions tab on the Director Dashboard (CP).

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Ledger transactions tab shows PENDING payouts, Filter allows selecting between All, Payouts, Received, Pending

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Implemented the Ledger Transactions filter in director_dashboard.html and dt_director_transactions view. Pending payouts are dynamically retrieved and returned to the datatable.

<!-- SECTION:NOTES:END -->
