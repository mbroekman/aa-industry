---
id: TASK-82
title: Show EVE Delivered quantities in build steps
status: Done
assignee: []
created_date: '2026-08-23 12:23'
updated_date: '2026-08-23 12:25'
labels: []
dependencies: []
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User requested to see how many items of a production task have already been built (EVE Delivered) inside the 'build steps' view. For example, if 20 Oneiros need to be built and 9 are already done, it should reflect 9/20.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Identify where the 'build steps' are rendered. Pass eve_delivered_qty to the context for these steps. Update the template to display the delivered quantity.

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Updated the Build Steps (summary pane) to show EVE Delivered quantities. This was achieved by fetching TaskJobLink objects for IN_PRODUCTION tasks and calculating the delivered quantity per item_type and activity, then passing it to the summary view logic. The 'Remaining' column was also corrected to deduct the delivered quantity, and the template was updated to display the delivered runs alongside active/ready jobs.

<!-- SECTION:NOTES:END -->
