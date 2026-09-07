---
id: TASK-134
title: Basket market stock trigger
status: To Do
assignee: []
created_date: '2026-09-07 12:57'
labels: []
dependencies: []
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Add logic to evaluate market stock levels (C‑N) for basket items and trigger orders when market stock is below basket target. Include logging for Loki and Maelstrom examples.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 When market stock < target, AI creates ProductionTask; logs show correct stock values.

<!-- AC:END -->
