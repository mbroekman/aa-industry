---
id: TASK-35
title: Implement Transaction Ledger
status: Done
assignee: []
created_date: '2026-08-07 11:05'
updated_date: '2026-08-07 11:08'
labels: []
dependencies: []
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Implementation of LedgerTransaction model and overview tab for tracking all internal payments.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 LedgerTransaction model created in models/wallet.py, Views modified to record transactions when MemberOrder and BuilderPayoutBatch are marked as paid, Transaction Ledger tab added to director dashboard, Existing PAID records migrated to LedgerTransaction

<!-- AC:END -->
