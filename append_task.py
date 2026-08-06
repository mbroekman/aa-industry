# Standard Library
code = """
@shared_task(name="industry_reforged.tasks.link_orphaned_jobs_to_tasks")
@log_task_execution("Link orphaned jobs to tasks")
def link_orphaned_jobs_to_tasks():
    from django.db.models import Sum
    from ..models import ProductionTask, TaskJobLink, CharacterIndustryJob, CorporationIndustryJob

    active_tasks = ProductionTask.objects.filter(status="IN_PRODUCTION")

    for task in active_tasks:
        if not task.assigned_to:
            continue

        first_ownership = task.assigned_to.character_ownerships.first()
        if not first_ownership:
            continue

        user = first_ownership.user
        user_character_ids = list(
            user.character_ownerships.all().values_list("character_id", flat=True)
        )

        char_jobs = CharacterIndustryJob.objects.filter(
            character_id__in=user_character_ids,
            product_type_id=task.item_type_id,
            activity_id=task.activity_id,
            status__in=["active", "ready", "delivered"]
        ).exclude(taskjoblink__isnull=False).order_by('start_date')

        corp_jobs = CorporationIndustryJob.objects.filter(
            installer_id__in=user_character_ids,
            product_type_id=task.item_type_id,
            activity_id=task.activity_id,
            status__in=["active", "ready", "delivered"]
        ).exclude(taskjoblink__isnull=False).order_by('start_date')

        linked_total = task.linked_jobs.aggregate(total=Sum('linked_runs'))['total'] or 0

        # Assume portion_size is 1 if not available, but EveType has portion_size?
        # Actually in production tasks, we usually calculate quantity.
        # Let's get the blueprint portion size from SDE? Or just use task.quantity if it means runs?
        # A task's 'quantity' is the final amount. 'runs' is the quantity / portion_size.
        portion_size = 1
        if task.item_type and hasattr(task.item_type, 'portion_size') and task.item_type.portion_size > 0:
            portion_size = task.item_type.portion_size

        required_runs = int(task.quantity / portion_size)
        if required_runs == 0:
            required_runs = 1

        for job in list(char_jobs) + list(corp_jobs):
            if linked_total >= required_runs:
                break

            runs_to_link = min(job.runs, required_runs - linked_total)
            if runs_to_link > 0:
                is_char = isinstance(job, CharacterIndustryJob)
                TaskJobLink.objects.create(
                    task=task,
                    character_job=job if is_char else None,
                    corporation_job=job if not is_char else None,
                    linked_runs=runs_to_link
                )
                linked_total += runs_to_link
"""

with open("industry_reforged/tasks/jobs.py", "a", encoding="utf-8") as f:
    f.write("\n" + code + "\n")
