---
id: TASK-25
title: Fix ImportError in generate_payout_batch
status: Done
assignee: []
created_date: '2026-08-06 17:51'
updated_date: '2026-08-06 17:51'
labels: []
dependencies: []
ordinal: 26000
---

# Task 25: Fix ImportError in generate_payout_batch

## Status

DONE

## Description

In `generate_payout_batch` in `industry_reforged/views/director.py`, `EveCharacter` was imported from `..models` instead of `allianceauth.eveonline.models`, causing an `ImportError`.

## Acceptance Criteria

- [x] Fix import path for `EveCharacter` in `generate_payout_batch`.
- [x] Gecommit.
