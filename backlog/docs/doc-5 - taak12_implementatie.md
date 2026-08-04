______________________________________________________________________

## id: doc-5 title: taak12_implementatie type: guide created_date: '2026-08-04 19:51' updated_date: '2026-08-04 19:51'

# TASK-12: Koppel geclaimde taken aan EVE ESI Industry Jobs

This plan outlines the implementation for linking accepted (claimed) production tasks in AA-Industry to actual EVE Online industry jobs (Character or Corporation jobs) running in structures, via a heuristic matcher.

## User Review Required

> [!IMPORTANT]
> The heuristic matcher will use `start_date` to link jobs. If a user starts an industry job *before* they claim the task in AA-Industry, should it still match? We will allow a margin (e.g. up to 1 hour before the task was claimed, or any active/ready job that hasn't been linked yet).
> Let me know if you agree with linking *any* unlinked active job that matches the user's characters, product type, and activity type!

## Proposed Changes

______________________________________________________________________

### Models (`industry_reforged/models/jobs.py`)

We will add a new data model `TaskJobLink` to create the link between a `ProductionTask` and an ESI industry job. Because a job can be either a character job or a corp job, we use two nullable ForeignKeys.

#### [MODIFY] \[jobs.py\](file:///home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/models/jobs.py)

Add `TaskJobLink` model:

```python
class TaskJobLink(models.Model):
    task = models.ForeignKey(
        "ProductionTask", on_delete=models.CASCADE, related_name="linked_jobs"
    )
    character_job = models.ForeignKey(
        "CharacterIndustryJob", on_delete=models.CASCADE, null=True, blank=True
    )
    corporation_job = models.ForeignKey(
        "CorporationIndustryJob", on_delete=models.CASCADE, null=True, blank=True
    )

    # Amount of runs linked from this job to this task
    linked_runs = models.IntegerField(default=1)

    class Meta:
        verbose_name = _("Task Job Link")
        verbose_name_plural = _("Task Job Links")
```

______________________________________________________________________

### Celery Tasks (`industry_reforged/tasks/jobs.py`)

We will add a new background task `link_orphaned_jobs_to_tasks` that runs periodically. We can call it at the end of the existing `update_character_jobs` and `update_corporation_jobs` tasks.

#### [MODIFY] \[jobs.py\](file:///home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/tasks/jobs.py)

Add the `link_orphaned_jobs_to_tasks` function.
Logic:

1. Find all `ProductionTask`s with status `IN_PRODUCTION`.
1. For each task, get all character IDs associated with the task's `assigned_to` user (the user's alts).
1. Find unlinked `CharacterIndustryJob` and `CorporationIndustryJob` entries that belong to these characters (as character or installer), where `product_type_id == task.item_type_id` and `activity_id == task.activity_id`, and status is `active` or `ready` or `delivered`.
1. Create a `TaskJobLink` for matched jobs up to the `quantity / portion_size` limit of the task.
1. If the sum of `linked_runs * portion_size` >= `task.quantity` and all linked jobs are `delivered`, optionally auto-complete the task or just mark it as ready for completion.

Call `link_orphaned_jobs_to_tasks()` at the end of `update_character_jobs` and `update_corporation_jobs`.

______________________________________________________________________

### Views and Templates

Update the "Claimed Jobs" UI to display the linked jobs for each task.

#### [MODIFY] \[industrialist_dashboard.html\](file:///home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/templates/industry_reforged/industrialist_dashboard.html)

In the "Claimed Jobs" tab, under the actions or below the task name, we will display a small list or badge of linked ESI jobs, showing their ESI status (`active`, `ready`, or `delivered`).
We'll pass `linked_jobs` along with the tasks in `views/industrialist.py`.

#### [MODIFY] \[industrialist.py\](file:///home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/views/industrialist.py)

In `industrialist_dashboard`, use `.prefetch_related("linked_jobs__character_job", "linked_jobs__corporation_job")` when fetching `my_tasks_qs` to make querying linked jobs efficient.

## Verification Plan

### Automated Tests

- Run `python manage.py makemigrations` and `python manage.py migrate` to ensure the new model is created successfully.
- Run `python manage.py check` to check for syntax errors.

### Manual Verification

- Claim a task on the dashboard.
- Check the background sync task manually via Django shell, ensuring `TaskJobLink` objects are created accurately matching the character's active ESI jobs.
- Verify the dashboard displays the linked ESI jobs properly.
