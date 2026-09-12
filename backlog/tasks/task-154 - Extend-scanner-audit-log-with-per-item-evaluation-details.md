---
id: TASK-154
title: Extend scanner audit log with per-item evaluation details
status: Done
assignee: []
created_date: '2026-09-12 07:39'
updated_date: '2026-09-12 07:44'
labels: []
dependencies: []
ordinal: 151000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a JSONField to OpportunityScannerLog to store per-item evaluation breakdown (item name, velocity, ADV threshold, margin, sell price, build cost, decision). Update scan_market_opportunities task to collect this data. Update scanner_logs template to display the evaluation details in an expandable table per log entry.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 OpportunityScannerLog has evaluation_details JSONField
- [ ] #2 scan_market_opportunities collects per-item data including velocity, margin, sell_price, build_cost, thresholds, and decision
- [ ] #3 scanner_logs.html displays evaluation details in expandable rows
- [ ] #4 Migration created
- [ ] #5 All tests pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added evaluation_details JSONField to OpportunityScannerLog. The scan_market_opportunities task now collects per-item data (item name, type_id, velocity, min_velocity, margin, min_margin, sell_price, build_cost, decision, reason) for every candidate. Skipped items include specific rejection reasons. Template updated with expandable detail rows per log entry. Migration 0062 created and applied. 149/149 tests pass.
<!-- SECTION:NOTES:END -->
