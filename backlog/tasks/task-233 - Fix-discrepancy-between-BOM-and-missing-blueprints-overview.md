---
id: TASK-233
title: Fix discrepancy between BOM and missing blueprints overview
status: Done
assignee: []
created_date: '2026-10-06 11:13'
updated_date: '2026-10-06 12:36'
labels: []
dependencies: []
ordinal: 409000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
There is a discrepancy between the blueprints shown in the BOM and the separate overview of missing blueprints. The BOM overview is correct, but the missing blueprints overview is incorrect (showing 7 missing when there should be more, and showing some as missing when they are actually present). Investigate and fix the logic for calculating missing blueprints to match the BOM logic.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Missing blueprints overview matches the BOM blueprints correctly, Blueprints that are present are not shown as missing, All missing blueprints are correctly identified
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed an issue where the stock evaluation for blueprints mistakenly summed up the amount of BPC items instead of their contained runs. The stock calculation engine now overrides blueprint stock with the total aggregated runs fetched from the CorpBlueprint records where the item is a BPC. This resolves the false positive shortage reporting on large quantity BPCs.
<!-- SECTION:NOTES:END -->
