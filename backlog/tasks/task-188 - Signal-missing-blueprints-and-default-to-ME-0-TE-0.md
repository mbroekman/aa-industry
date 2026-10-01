---
id: TASK-188
title: Signal missing blueprints and default to ME 0 TE 0
status: Done
assignee:
  - '@antigravity'
created_date: '2026-10-01 10:56'
updated_date: '2026-10-01 15:01'
labels: []
dependencies: []
ordinal: 364000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
If a blueprint is missing for a part, it must be signaled in the BOM, Full production tree, and ME & BPC Overrides. Additionally, the calculations for these missing blueprints must use ME 0 and TE 0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Missing blueprints are signaled in BOM
- [x] #2 Missing blueprints are signaled in Full production tree
- [x] #3 Missing blueprints are signaled in ME & BPC Overrides
- [x] #4 Calculations use ME 0 and TE 0 for missing blueprints
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated get_blueprint_me in bom_engine.py to check if CorpBlueprint exists. If it doesn't, default ME to 0 and pass missing_bp=True flag. Added warning badge in quotes.py context and templates (bom_tree_node.html and view_quote.html) to signal missing blueprints.
<!-- SECTION:NOTES:END -->
