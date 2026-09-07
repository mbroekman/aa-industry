---
id: TASK-129
title: Persistent Opportunity Scanners
status: Done
assignee: []
created_date: '2026-09-06 16:49'
updated_date: '2026-09-06 16:54'
labels: []
dependencies: []
ordinal: 126000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Refactor Opportunity Scanners to be saved as persistent configurations (like Baskets) so users can view, edit, and re-run them from the dashboard.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 OpportunityScanner model exists, OpportunityScanForm is a ModelForm, Scanners are listed on the AI Manager dashboard, Scanners can be created, edited, deleted, and re-run, The celery task uses the saved configuration

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Opportunity Scanner refactored into a persistent model (OpportunityScanner) and integrated into the AI Manager Dashboard with CRUD and Run functionality.

<!-- SECTION:NOTES:END -->
