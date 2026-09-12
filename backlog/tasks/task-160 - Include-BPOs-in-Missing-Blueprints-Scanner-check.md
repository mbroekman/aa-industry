---
id: TASK-160
title: Include BPOs in Missing Blueprints Scanner check
status: In Progress
assignee: []
created_date: '2026-09-12 17:10'
updated_date: '2026-09-12 17:10'
labels: []
dependencies: []
ordinal: 336000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The missing blueprints list for Opportunity Scanners currently only checks for available BPCs. It should also check for BPOs, as items are often built directly from BPOs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Scanner checks both BPO and BPC availability for a blueprint, Missing Blueprint list excludes items where either a BPO or BPC is available
<!-- AC:END -->
