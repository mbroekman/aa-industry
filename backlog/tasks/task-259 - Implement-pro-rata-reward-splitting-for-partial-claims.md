---
id: TASK-259
title: Implement pro-rata reward splitting for partial claims
status: Done
assignee: []
created_date: '2026-10-21 19:53'
labels:
  - logic
  - rewards
  - pricing
dependencies: []
ordinal: 433000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement pro-rata reward distribution when claiming partial quantities from production tasks on the Job Market.
Currently, `calculate_task_builder_reward` recalculates rewards for both claimed and remaining portions as independent tasks, causing each partial batch to consume the full corporate maximum reward cap (e.g. 75M ISK).
Instead, the task's existing `builder_reward` must be split pro-rata (`ratio = claim_qty / task.quantity`) so that:
- Claimed batch receives `ratio * task.builder_reward`
- Remaining task on Job Market retains `task.builder_reward - claimed_reward`
- Total reward paid across all partial claims never exceeds the original task's total reward or corporate cap.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Update `claim_task_preview` endpoint in `views/industrialist.py` to calculate `reward_claimed` and `reward_rem` pro-rata from `task.builder_reward`
- [x] #2 Update `claim_task` endpoint in `views/industrialist.py` to split `task.builder_reward` pro-rata between claimed task and remaining task
- [x] #3 Fall back gracefully to `calculate_task_builder_reward` only if `task.builder_reward` is 0 or unassigned
- [x] #4 Add unit regression tests in `test_partial_claiming.py` verifying pro-rata distribution and conservation of total reward across partial claims
- [x] #5 Verify all tests pass, deploy to devauth, and test live calculation
<!-- AC:END -->

## Implementation Notes
- Updated `claim_task_preview` and `claim_task` in `industry_reforged/views/industrialist.py`:
  - When claiming a partial quantity (`claim_qty < task.quantity`), the batch reward is calculated pro-rata: `ratio = Decimal(str(claim_qty)) / Decimal(str(task.quantity))`, `reward_claimed = (task.builder_reward * ratio).quantize(Decimal("0.01"))`.
  - The remaining task on the Job Market retains `task.builder_reward - reward_claimed`.
  - Handled fallback gracefully: if `task.builder_reward` was 0 or uncomputed, the full task reward is first computed via `calculate_task_builder_reward(task.quantity)` and then split pro-rata.
  - In `claim_task`, updated full claims with `allocated_slots > 1` to adjust `estimated_duration_seconds` to reflect the industrialist's actual wall-clock duration.
- Added comprehensive unit tests in `test_partial_claiming.py`:
  - Verified pro-rata math: 20/50 items (40%) splits 30M into 12M claimed and 18M remaining.
  - Verified user scenario: 50 Capital Corporate Hangar Bays claimed from a 432-item task with 75M cap allocates exact pro-rata 8,680,555.56 ISK to the claimed batch and 66,319,444.44 ISK to the remaining market task, conserving the exact 75M corporate cap.
- Verified live on devauth: calling preview on task #11910 returns `8,680,555.56 ISK` claimed, `66,319,444.44 ISK` remaining, and `16h 40m` wall-clock duration with 10 slots.

