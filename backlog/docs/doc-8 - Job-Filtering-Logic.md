---
id: doc-8
title: Job Filtering Logic (v0.4.1)
type: guide
status: published
created: 2026-08-19
updated: 2026-08-25
---

# Job Filtering Logic

This document describes the logic behind selecting and displaying EVE jobs (industry jobs from the game) based on locally claimed tasks (`ProductionTask`) in the Industrialist Dashboard, as implemented in recent versions (v0.3.12+).

## Concept & Data Model

Within the application, we deal with three main components:

1. **ProductionTask**: This is a claimed task within Alliance Auth. It specifies what needs to be built and who is going to build it. A task can have statuses such as `IN_PRODUCTION` (active) or `COMPLETED` (finished).
1. **IndustryJob** (`CorporationIndustryJob` / `CharacterIndustryJob`): These are the actual jobs as they are running in EVE Online, fetched via the API.
1. **TaskJobLink**: This table acts as the bridge between a `ProductionTask` and one or more `IndustryJob`s.

## How the Selection Works

Previously, the **"Corporate Jobs Overview"** and **"My Corporate Jobs"** tabs displayed *all* active EVE jobs, regardless of whether the user started them privately in-game or claimed them via the app. This led to a cluttered dashboard with unrelated personal jobs.

Since v0.3.12 and subsequent updates, the logic works as follows:

- **Strict Relation Check for Corp Jobs Overview**: The Corporate Dashboard tab filters jobs using `taskjoblink__isnull=False`. This means an EVE job is **only** retrieved if it is successfully linked to a `ProductionTask` via a `TaskJobLink`.
- **Time Window for My Corporate Jobs**: The Industrialist Dashboard uses a more flexible time window approach to support unlinked jobs like Reactions. It calculates the `oldest_claim_date` based on the user's currently active claims (`IN_PRODUCTION` status).
- **Visibility of Unlinked Jobs**: Jobs started by the user in EVE without a corresponding claimed task (e.g., Reactions) are shown under two conditions:
  - **Always Visible if Active**: If the unlinked job is currently running (`active`) or finished and waiting to be delivered (`ready`), it is always shown, bypassing any date filters.
  - **Time-Based Visibility for Delivered Jobs**: If the unlinked job has already been delivered, it is only shown if its `start_date` falls on or after the `oldest_claim_date`. If the user has no active claims, old unlinked delivered jobs are hidden.
- **Preservation of History**: Jobs with a valid link (`taskjoblink__isnull=False`) are always shown regardless of the time window or their current state. This ensures that users can still view their historical claimed tasks by setting the UI filter to "Delivered" or "All".

## Diagram: Data Flow and Visibility

The diagram below outlines how a job originating from EVE is processed and whether it ends up visible on the dashboard.

```mermaid
graph TD
    API["EVE Online API"] -->|Sync| DB_JOB["CorporationIndustryJob"]

    DB_JOB -->|"Is this job linked to a task?"| CHECK{"Has TaskJobLink?"}

    CHECK -->|No| UNLINKED["Unlinked Job (e.g., Reactions or Private)"]
    UNLINKED --> STATUS_CHECK{"Is status Active or Ready?"}
    STATUS_CHECK -->|Yes| VISIBLE_ACTIVE(("Visible in My Corporate Jobs"))
    STATUS_CHECK -->|No| TIME_CHECK{"Started on/after oldest claim?"}
    TIME_CHECK -->|No| HIDDEN(("Hidden from Dashboard"))
    TIME_CHECK -->|Yes| VISIBLE_DELIVERED(("Visible via UI Filter"))

    CHECK -->|Yes| LINKED["Linked Job"]
    LINKED --> TASK_STATE{"Status of the Linked Task?"}

    TASK_STATE -->|IN_PRODUCTION| ACTIVE_JOB["Active or Ready Job"]
    ACTIVE_JOB -->|"Displayed by default"| VISIBLE_ACTIVE

    TASK_STATE -->|COMPLETED| COMPLETED_JOB["Delivered Job"]
    COMPLETED_JOB -->|"Available via filter"| VISIBLE_DELIVERED(("Visible with Delivered filter"))
```

## Conclusion

By employing a hybrid filtering approach, we ensure the dashboard displays exactly what the user expects:

1. Jobs explicitly linked to tasks (`taskjoblink__isnull=False`) are always retained for history.
1. Unlinked jobs that are currently running (`active`) or waiting to be delivered (`ready`) are always visible so you can monitor your active work, regardless of linked tasks.
1. Delivered unlinked jobs (such as completed EVE Reactions) are visible dynamically, but only if they were started during an active work session (measured from the oldest active claim date).
   This prevents old private jobs from cluttering the interface while fully supporting complex production chains that include unlinked steps.
