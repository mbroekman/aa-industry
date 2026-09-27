---
id: TASK-178
title: Show most expensive line item in order list
status: Done
assignee: []
created_date: '2026-09-26 19:06'
updated_date: '2026-09-26 19:08'
labels: []
dependencies: []
ordinal: 354000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Currently orders only show ISK value, making them hard to identify. Display the most expensive line item for each order in the list view so it's easier to see what an order is for without opening it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 - Order list shows the most expensive line item for each order, - It doesn't break the layout
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added most_expensive_item property to MemberOrder model. Updated orders_dashboard.html and director_dashboard.html (with dt_director_orders view) to display the primary item column.
<!-- SECTION:NOTES:END -->
