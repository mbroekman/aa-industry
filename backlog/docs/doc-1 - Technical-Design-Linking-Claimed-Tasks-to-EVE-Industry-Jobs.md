---
id: doc-1
title: 'Technical Design: Linking Claimed Tasks to EVE Industry Jobs'
type: guide
created_date: '2026-08-06 17:53'
updated_date: '2026-09-04 11:09'
---

# Technical Design: Linking Claimed Tasks to EVE Industry Jobs

## Background

When a user claims (accepts) a `ProductionTask`, they will install the actual industry jobs (manufacturing, reactions, etc.) in an Upwell structure in EVE Online. Currently, AA-Industry knows *that* jobs are running via ESI, but there is no direct link (foreign key) between a specific `ProductionTask` in the web app and the `CharacterIndustryJob` / `CorporationIndustryJob` in EVE Online.

The goal is to link them, considering the following challenges:

1. EVE Online does not support attaching "metadata" (such as a Task ID) to an industry job.
1. Users often claim tasks with their "Main" character in the application, but start the jobs in EVE using specialized "Alt" characters.
1. Jobs can be either personal (Character) or corporation (Corporation) jobs.

## Feasibility: Is it possible?

**Yes, it is possible via "Heuristic Matching".**
Because Alliance Auth tracks all EVE Characters belonging to a user (via `CharacterOwnership`), we can monitor jobs across all of the user's alts and link them to open tasks with a high degree of confidence.

## Implementation Strategy

### 1. Alt Character Recognition (User Scope)

In Alliance Auth, alts are linked to the `User` via the `CharacterOwnership` model.
To locate jobs matching a task, we look beyond just jobs started by the `assigned_to` character and query all characters owned by the user:

```python
user_characters = (
    task.assigned_to.character_ownerships.first()
    .user.character_ownerships.all()
    .values_list("character_id", flat=True)
)
```

### 2. Matching Logic (Heuristics)

To link an incoming ESI job to a `ProductionTask`, the following rules apply:

1. **Installer**: The job's `installer_id` (Corp or Character) exists in `user_characters`.
1. **Type Match**: `job.product_type_id == task.item_type_id`.
1. **Activity Match**: `job.activity_id == task.activity_id`.
1. **Time Match**: The job was started (`start_date`) *after* (or immediately before, within an acceptable time window) the task was claimed.
1. **Availability**: The job is not already (fully) linked to another task.

### 3. Data Model Changes

Instead of modifying the ESI-synced job models (`CharacterIndustryJob` / `CorporationIndustryJob`), introduce a dedicated linking model in `industry_reforged/models/jobs.py` (or `orders.py`):

```python
class TaskJobLink(models.Model):
    task = models.ForeignKey(
        ProductionTask, on_delete=models.CASCADE, related_name="linked_jobs"
    )
    # Since jobs reside in two separate tables (Character vs Corporation), use two nullable foreign keys:
    character_job = models.ForeignKey(
        CharacterIndustryJob, on_delete=models.CASCADE, null=True, blank=True
    )
    corporation_job = models.ForeignKey(
        CorporationIndustryJob, on_delete=models.CASCADE, null=True, blank=True
    )

    # Number of 'runs' from this job linked to this specific task (if 1 job covers multiple tasks)
    linked_runs = models.IntegerField(default=1)
```

### 4. Background Celery Task (The Matcher)

During or immediately following regular ESI job synchronizations (`update_character_jobs` and `update_corporation_jobs`), a background task runs: `link_orphaned_jobs_to_tasks`.
This task queries all unlinked active jobs and finds open `IN_PRODUCTION` tasks for the same user that match on product, activity, and time window.
When a match is found, a `TaskJobLink` is created.

### 5. Frontend & UI

- **Dashboard**: For active tasks (`ProductionTask`), display a dropdown or list of linked EVE Jobs, including remaining duration (`end_date`) or status ("Delivered").
- **Auto-completion**: Once all linked jobs reach `delivered` status and total produced quantity matches the task's `quantity`, the system can proactively prompt the player to complete the task, or optionally auto-complete it.

## Conclusion

This is functionally feasible. The implementation requires adding a linking model and a periodic matching algorithm (via Celery) to associate ESI data with internal tasks across all alts owned by the user.
