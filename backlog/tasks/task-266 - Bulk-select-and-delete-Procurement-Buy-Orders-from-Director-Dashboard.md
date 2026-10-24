---
id: TASK-266
title: Bulk-select and delete Procurement Buy Orders from Director Dashboard
status: Done
assignee: []
created_date: '2026-10-24 13:33'
updated_date: '2026-10-24 13:34'
labels: []
dependencies: []
ordinal: 440000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add checkbox selection (header select-all + per-row) to the Buy Orders tab's DataTable, with a Delete Selected button that bulk-deletes the chosen CorpBuyOrder rows in one request.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Buy Orders table has a leading checkbox column with a select-all header checkbox
- [x] #2 Delete Selected button bulk-deletes only the checked rows via a new bulk_delete_buy_orders view, confirm-gated via the existing require-confirmation pattern
- [x] #3 corp_access permission enforced; GET and empty-selection are no-ops
- [x] #4 Tests cover selective deletion, permission denial, empty selection, and GET no-op
- [x] #5 Full suite green, ruff clean
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Shifted dt_director_buy_orders' column indices by one (checkbox now col 0) and updated order_map/columnDefs/initial-sort accordingly. Bulk form uses the existing global require-confirmation handler (base.html) via form.requestSubmit() so the same confirm-dialog convention applies as the per-row delete. Hit and fixed a real bug during test-writing: deleted_count, _ = queryset.delete() shadowed the module's gettext_lazy _ import, causing UnboundLocalError on the empty-selection path - renamed to _details.
<!-- SECTION:NOTES:END -->
