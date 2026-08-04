---
id: TASK-4
title: Translation Review
status: Done
assignee: []
created_date: '2026-07-29 16:32'
labels: []
dependencies: []
type: chore
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Ensure multilingual support is consistently applied across the codebase using Django gettext.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Review templates for hardcoded English strings and use trans/blocktrans
- [ ] #2 Review Python files for hardcoded user-facing strings and use gettext_lazy
- [ ] #3 Run makemessages for en and nl
- [ ] #4 Run compilemessages
- [ ] #5 All user-facing text is translatable

<!-- AC:END -->
