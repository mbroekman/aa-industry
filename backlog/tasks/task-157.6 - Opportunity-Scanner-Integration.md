---
id: TASK-157.6
title: Opportunity Scanner Integration
status: Done
assignee: []
created_date: '2026-09-12 11:49'
updated_date: '2026-09-12 12:11'
labels: []
dependencies: []
parent_task_id: TASK-157
ordinal: 160000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update the Opportunity Scanner to query the FastAPI /forecast endpoint for demand predictions instead of using naive velocity, and add a confidence score to the UI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Scanner UI shows AI-backed velocity/confidence and correctly sorts opportunities based on the AI predictions
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated MarketOpportunity model, updated scanner logic in tasks/ai_manager.py to use /forecast, and added AI columns to opportunities.html.
<!-- SECTION:NOTES:END -->
