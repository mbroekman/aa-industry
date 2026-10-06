---
id: TASK-209
title: Investigate high cost of Capital Core Temperature Regulator Blueprint
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-04 15:27'
updated_date: '2026-10-04 15:28'
labels: []
dependencies: []
ordinal: 385000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User is reporting extremely high costs for BPCs such as Capital Core Temperature Regulator Blueprint. Need to investigate how pricing_engine handles BPCs vs BPOs and why the cost calculation yields a high value.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root cause identified and reported to user
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Investigation complete. BPCs and BPOs share the same type ID, so the pricing engine pulls the BPO market price (1.5B+ ISK) from ESI. The minimum margin logic forces the final quote to >1.5B based on this 'True Cost'. Provided user with instructions to use Manual Price Overrides in the Director Config to explicitly price these BPCs.
<!-- SECTION:NOTES:END -->
