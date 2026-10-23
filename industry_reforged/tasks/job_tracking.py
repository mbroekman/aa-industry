"""App Tasks - claimed-job ETA tracking and overdue alerting."""

# Standard Library
import logging

# Third Party
from celery import shared_task

# Django
from django.utils import timezone

from ..models import CorporationWebhookConfig, ProductionTask
from ..utils import eta_service
from ..utils.discord import send_discord_webhook
from .utils import log_task_execution, send_pi_notification

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.check_overdue_production_tasks")
@log_task_execution("Check Overdue Production Tasks")
def check_overdue_production_tasks():
    """Flags claimed jobs that have run past their estimated completion time (plus the
    corp's configurable grace buffer), notifies the claimant (AA in-app + Discord DM),
    and re-notifies on the same buffer interval as long as the job stays overdue. Also
    sends one batched director-webhook embed per corp per run for anything (re-)flagged
    this cycle."""
    now = timezone.now()
    tasks = ProductionTask.objects.filter(
        status="IN_PRODUCTION", assigned_to__isnull=False
    ).select_related("item_type", "assigned_to")

    newly_flagged_by_corp: dict[int, list[ProductionTask]] = {}
    buffer_hours_by_corp: dict[int, int] = {}

    for task in tasks:
        try:
            corp = task.assigned_to.corporation
        except Exception:  # noqa: BLE001
            corp = None
        corp_id = corp.corporation_id if corp else None

        if corp_id not in buffer_hours_by_corp:
            buffer_hours_by_corp[corp_id] = eta_service.get_corp_buffer_hours(corp)
        buffer_hours = buffer_hours_by_corp[corp_id]

        if not eta_service.is_overdue(task, buffer_hours):
            continue

        due_for_reminder = (
            task.last_overdue_notified_at is None
            or (now - task.last_overdue_notified_at).total_seconds()
            >= buffer_hours * 3600
        )
        if not due_for_reminder:
            continue

        eta = eta_service.get_task_eta(task)
        overdue_since = now - eta if eta else None
        hours_overdue = (
            int(overdue_since.total_seconds() // 3600) if overdue_since else 0
        )
        message = (
            f"Your claimed job {task.quantity}x {task.item_type.name} is "
            f"~{hours_overdue}h past its estimated completion time."
        )
        send_pi_notification(
            task.assigned_to, title="Claimed Job Overdue", message=message
        )

        task.last_overdue_notified_at = now
        task.save(update_fields=["last_overdue_notified_at"])

        if corp_id is not None:
            newly_flagged_by_corp.setdefault(corp_id, []).append(task)

    for corp_id, flagged_tasks in newly_flagged_by_corp.items():
        webhook_config = CorporationWebhookConfig.objects.filter(
            corporation__corporation_id=corp_id
        ).first()
        if not webhook_config or not webhook_config.directors_webhook:
            continue

        lines = "\n".join(
            f"- **{t.assigned_to.character_name}**: {t.quantity}x {t.item_type.name}"
            for t in flagged_tasks
        )
        embed = {
            "title": "Overdue Claimed Jobs",
            "description": (
                f"{len(flagged_tasks)} claimed job(s) are past their estimated "
                f"completion time:\n{lines}"
            ),
            "color": 15158332,  # Red
        }
        send_discord_webhook(webhook_config.directors_webhook, embed)
