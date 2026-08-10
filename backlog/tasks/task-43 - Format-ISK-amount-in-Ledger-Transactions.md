---
id: TASK-43
title: Format ISK amount in Ledger Transactions
status: Done
assignee: []
created_date: '2026-08-09 06:25'
updated_date: '2026-08-09 06:26'
labels: []
dependencies: []
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Fix the ISK amount formatting in the Ledger Transactions datatable (Director Dashboard) to use the standard EVE ISK format, making it easier to read.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 ISK amounts in Ledger Transactions are formatted correctly (e.g. 1,000,000.00)
- [ ] #2 1

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Applied the standard eve_isk template tag function to format both regular ledger transactions and pending payouts in dt_director_transactions (datatables.py).

<!-- SECTION:NOTES:END -->
