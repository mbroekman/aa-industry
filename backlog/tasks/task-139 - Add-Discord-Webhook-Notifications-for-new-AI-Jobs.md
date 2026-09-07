---
id: TASK-139
title: Add Discord Webhook Notifications for new AI Jobs
status: Done
assignee: []
created_date: '2026-09-07 17:00'
updated_date: '2026-09-07 17:02'
labels: []
dependencies: []
ordinal: 136000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

User requested to add a discord webhook notification so that when the AI Manager generates new jobs, it broadcasts a message on discord indicating that new jobs are available.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Discord notifications are sent when AI generates jobs

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Added ai_jobs_webhook to CorporationWebhookConfig in models/config.py. Updated ai_manager.py's evaluate_baskets to gather created jobs and send a grouped Discord embed using send_discord_webhook. Admins can now configure a discord webhook per corp for new AI jobs.

<!-- SECTION:NOTES:END -->
