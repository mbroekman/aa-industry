"""App Configuration"""

# Django
from django.apps import AppConfig


class IndustryConfig(AppConfig):
    """App Config"""

    name = "industry_reforged"
    label = "industry_reforged"
    verbose_name = "Industry Reforged"

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(_queue_initial_tasks, sender=self)


def _queue_initial_tasks(sender, **kwargs):
    """Queue all main tasks once after a fresh install (no prior runs recorded)."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        from .models import TaskExecutionLog

        if TaskExecutionLog.objects.exists():
            # Tasks have run before — skip initial queue.
            return

        from .tasks.blueprints import task_sync_corp_blueprints
        from .tasks.facilities import update_industry_facilities
        from .tasks.inventory import task_sync_corp_inventory
        from .tasks.jobs import update_character_jobs, update_corporation_jobs
        from .tasks.wallets import task_sync_corp_wallets

        tasks = [
            update_character_jobs,
            update_corporation_jobs,
            task_sync_corp_blueprints,
            task_sync_corp_inventory,
            task_sync_corp_wallets,
            update_industry_facilities,
        ]
        for task in tasks:
            task.delay()

        logger.info(
            "Industry Reforged: fresh install detected — queued %d initial tasks.",
            len(tasks),
        )
    except Exception:
        # Never let a signal failure break migrate.
        pass
