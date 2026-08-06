# Task 25: Fix ImportError in generate_payout_batch

## Status

DONE

## Description

In `generate_payout_batch` in `industry_reforged/views/director.py`, `EveCharacter` was imported from `..models` instead of `allianceauth.eveonline.models`, causing an `ImportError`.

## Acceptance Criteria

- [x] Fix import path for `EveCharacter` in `generate_payout_batch`.
- [x] Gecommit.
