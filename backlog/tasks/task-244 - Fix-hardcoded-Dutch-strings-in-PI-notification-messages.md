---
id: TASK-244
title: Fix hardcoded Dutch strings in PI notification messages
status: Done
assignee: []
created_date: '2026-10-13 13:28'
updated_date: '2026-10-13 13:41'
labels: []
dependencies: []
ordinal: 420000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tasks/pi.py had hardcoded Dutch text in PI notification messages (extractor expired, storage full, and the planet-name fallback label), inconsistent with the Alliance Auth ecosystem English-only standard already enforced elsewhere (e.g. aa-kanban TASK-70). Translate to English.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Extractor-expired notification message is in English
- [ ] #2 Storage-full notification message is in English
- [ ] #3 Planet label fallback string ('Planeet {id}') is in English
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Translated 3 hardcoded Dutch strings in tasks/pi.py: the extractor-expired notification message, the storage-full notification message, and the 'Planeet {id}' planet-name fallback label. No existing tests asserted on the exact message text, so no test updates needed. Verified via industry_reforged/tests/test_pi_tasks.py and related (7 passed).
<!-- SECTION:NOTES:END -->
