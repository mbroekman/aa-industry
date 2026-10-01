---
id: TASK-200
title: Fix django.po compile errors in v0.14.0
status: Done
assignee: []
created_date: '2026-10-01 17:05'
updated_date: '2026-10-01 17:07'
labels: []
dependencies: []
ordinal: 376000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix invalid control sequence at line 659 and duplicate message definitions in industry_reforged/locale/nl/LC_MESSAGES/django.po which causes compilation to fail on GitHub Actions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 django-admin compilemessages succeeds without errors
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fixed invalid control sequence on line 659 and removed duplicate definitions for 'Missing Blueprints', 'Item', and 'Status'. Released as v0.14.1.
<!-- SECTION:NOTES:END -->
