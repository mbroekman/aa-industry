---
id: TASK-34
title: Fix tab redirect after batch payment
status: Done
assignee: []
created_date: '2026-08-07 10:41'
updated_date: '2026-08-07 10:47'
labels: []
dependencies: []
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

After executing a batch payment, the page refreshes and doesn't return to the active tab (e.g. #active-pane). Update the redirect URL in the batch payment view to include the correct anchor.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Batch payment redirects to the same tab

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated Javascript in director_dashboard.html to properly handle hash changes and tab selection using triggerEl.click() and updating window.location.hash on tab change.
*Fix update:* The previous JS-only fix failed because redirects from POST requests drop the hash in some cases or trigger a full reload. Updated `director.py` to append `?tab=payouts` (and similar query parameters) instead of `#payouts-pane` in redirect URLs. Updated `director_dashboard.html` JS to prioritize parsing the `tab` query parameter and restoring the hash dynamically.

<!-- SECTION:NOTES:END -->
