---
id: TASK-169
title: Fix AI Forecasting integration logging and URL configurability
status: Done
assignee: []
created_date: '2026-09-13 15:03'
updated_date: '2026-09-13 15:03'
labels: []
dependencies: []
ordinal: 345000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The AI service URL was hardcoded to 127.0.0.1:8050 and errors were suppressed, making it impossible to integrate in containerized environments. Added INDUSTRY_REFORGED_AI_URL setting and proper warning logs.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 URL is configurable, exceptions log warnings, celery worker won't fail silently

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Made URL configurable via INDUSTRY_REFORGED_AI_URL and added warning logs to except blocks

<!-- SECTION:NOTES:END -->
