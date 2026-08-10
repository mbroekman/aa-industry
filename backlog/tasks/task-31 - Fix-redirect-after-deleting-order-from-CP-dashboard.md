---
id: TASK-31
title: Fix redirect after deleting order from CP dashboard
status: Done
assignee: []
created_date: '2026-08-07 07:37'
updated_date: '2026-08-07 07:38'
labels: []
dependencies: []
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Ensure deleting an order returns the user to the correct dashboard they originated from (Corporate Dashboard or Member Dashboard) rather than defaulting to the Member Dashboard.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Deleting from CP dashboard returns to CP dashboard

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated delete_order view to redirect to HTTP_REFERER if available and not the quote page of the deleted order. Added fallback to director_dashboard for users with corp_access.

<!-- SECTION:NOTES:END -->
