---
id: TASK-185
title: Profit & Loss view for quotes
status: Done
assignee: []
created_date: '2026-09-28 15:07'
updated_date: '2026-09-28 15:11'
labels: []
dependencies: []
ordinal: 361000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Order details view for the quote process should look more like a Profit & Loss view showing a suggested price based on Jita, Material Cost, Estimated Build Cost, and Profit Margin. This needs to be a new view only shown for quotes, but it should be the default view.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 1. Create a Profit & Loss view for MemberOrder quotes. 2. Show Jita Price, Material Cost, Estimated Build Cost, Profit Margin, and Suggested Price. 3. Make this the default view for orders in 'quote' status.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added a new 'Profit & Loss' tab to the order quote view, showing original Jita Value, Material Cost, Estimated Build Cost, and Profit Margin. This tab is set as the default view for orders in the REQUESTED or QUOTED states. Extracted the sidebar to a partial template (_order_details_sidebar.html) to keep it visible across both views. Updated user_manual_en.md and CHANGELOG.md accordingly.
<!-- SECTION:NOTES:END -->
