---
id: TASK-281
title: Discord messages in a fixed language
status: Done
assignee: []
created_date: '2026-10-27 10:26'
updated_date: '2026-10-27 10:41'
labels: []
dependencies: []
ordinal: 455000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Webhook and channel messages are built in the language of whoever triggered them, so Discord gets a mix of English and Dutch. Build every Discord message inside a fixed language: per-webhook-config choice (frontend) falling back to DISCORD_MESSAGE_LANGUAGE / LANGUAGE_CODE; DMs in the recipient's AA profile language.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
discord_i18n.py helper; CorporationWebhookConfig.discord_language (migration 0092) editable under Global Pricing; every webhook/DM/Auth-notification text built inside discord_language(); DMs and Auth notifications in recipient's profile language; 147 Dutch strings added via polib (no gettext tools available).
<!-- SECTION:NOTES:END -->
