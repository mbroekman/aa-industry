---
id: TASK-132
title: Missing Blueprint Report
status: Done
assignee: []
created_date: '2026-09-06 17:40'
updated_date: '2026-09-06 17:45'
labels: []
dependencies: []
ordinal: 198000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Scanner identifies profitable opportunities for items the corporation does NOT own the blueprint for.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Add scan_missing_blueprints boolean to Scanner, evaluate products in selected categories that we lack blueprints for, log them in MissingBlueprintOpportunity model, show report in Scanner details/dashboard

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Created MissingBlueprintOpportunity model, updated scanner logic, added UI toggle and dashboard report view.

<!-- SECTION:NOTES:END -->
