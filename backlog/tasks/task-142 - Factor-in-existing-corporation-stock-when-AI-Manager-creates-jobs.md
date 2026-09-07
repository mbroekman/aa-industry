---
id: TASK-142
title: Factor in existing corporation stock when AI Manager creates jobs
status: To Do
assignee: []
created_date: '2026-09-07 19:50'
labels: []
dependencies: []
ordinal: 139000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Modify the AI Market Manager (Baskets and Opportunity Scanners) to check the existing inventory stock of the corporation before automatically creating a production job. The required production quantity should be offset by the stock the corporation already has available. The AI Market Logs and Scanner Logs must clearly state the current stock level and that it was taken into account when calculating the order size.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 1. Basket evaluation checks current corp stock for the item before generating an order; 2. Opportunity Scanner checks current corp stock before generating an order; 3. The requested production amount is reduced by the available stock; 4. The AI Market Log and Scanner Log mentions the current stock and that it was factored into the calculation.

<!-- AC:END -->
