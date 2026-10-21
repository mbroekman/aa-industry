---
id: TASK-258
title: Fix ClaimTaskModal hidden behind modal backdrop
status: Done
assignee: []
created_date: '2026-10-21 19:24'
labels:
  - bugfix
  - ui
dependencies: []
ordinal: 432000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix `#claimTaskModal` being hidden behind the modal backdrop when clicking "Claim" on the Job Market. The backdrop is created (screen darkens), but the modal dialog is invisible or trapped within a nested DOM stacking context.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Inspect placement and z-index / stacking context of `#claimTaskModal` in `industrialist_dashboard.html`
- [x] #2 Ensure modal is placed directly under `{% block content %}` or body root, outside nested card/table containers
- [x] #3 Ensure proper Bootstrap 5 classes, dark theme contrast, and correct z-index
- [x] #4 Verify modal opens visibly on devauth without being obscured by backdrop
- [x] #5 Run full unit tests and deploy to devauth
<!-- AC:END -->

## Implementation Notes
- Diagnosed DOM structure in `industry_reforged/templates/industry_reforged/industrialist_dashboard.html`:
  - The preceding `#shoppingListLoadingModal` element was missing its closing `</div></div></div>` tags (closing `modal-content`, `modal-dialog`, and `shoppingListLoadingModal`).
  - As a result, `#claimTaskModal` was mistakenly nested inside `#shoppingListLoadingModal` (`display: none`), so when Bootstrap displayed `#claimTaskModal`, it inserted a backdrop on the `body` while `#claimTaskModal` remained hidden inside its parent container.
- Added the missing `</div>` tags to properly isolate `#shoppingListLoadingModal`.
- Verified all 302 unit tests pass.
- Deployed changes to devauth and restarted Gunicorn services.

