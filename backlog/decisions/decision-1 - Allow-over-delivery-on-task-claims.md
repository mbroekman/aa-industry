---
id: decision-1
title: Allow over-delivery on task claims
date: '2026-08-23 12:33'
status: accepted
---

## Context

When an EVE Online industry job is matched against a Production Task, the system previously capped the amount of runs linked to the task to exactly the remaining amount required (`runs_to_link = min(job.runs, required_runs - linked_total)`).
Because the query fetching available jobs (`.exclude(taskjoblink__isnull=False)`) filters out any job that has at least one link, any partially claimed jobs were completely removed from the pool of available jobs. This caused the remaining runs of those jobs to become "orphaned"—they were neither counted towards the task nor available to be claimed by other tasks.

## Decision

We decided to stop capping the linked runs (`runs_to_link = job.runs`). This allows the system to link the entire job to the task, preventing any runs from being lost. This means a task can now receive an "over-delivery" (e.g. 208 runs delivered for a 200 run requirement).

To support this change without confusing users:

1. The dashboard UI (`industrialist_dashboard.html`) was updated to explicitly split and display the normal delivery quantity and the `eve_overdelivered_qty`.
1. The "Build Steps" summary logic was updated to pre-fetch `TaskJobLink` delivered quantities so they reflect properly in the summary pane, ensuring the "Remaining" calculations account for everything that was actually delivered in-game.

## Consequences

- **Positive**: All runs from EVE jobs are fully accounted for, eliminating the bug where runs would mysteriously "disappear" from the dashboard.
- **Positive**: Industrialists can now clearly see exactly how much over-delivery they produced.
- **Negative**: Jobs cannot be cleanly "split" across multiple tasks. If you run a massive batch job to fulfill two separate tasks, the first task will claim the entire batch (resulting in massive over-delivery), and the second task will receive nothing. (This matches EVE's native logic, where you can't partially deliver a job).
