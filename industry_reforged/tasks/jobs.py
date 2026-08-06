"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

from ..models import (
    CharacterIndustryJob,
    CorporationIndustryJob,
    CorporationSyncConfig,
)
from .utils import ensure_eve_type, esi, log_task_execution, notify_discord_user

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.update_character_jobs")
@log_task_execution("Update Character Jobs")
def update_character_jobs():
    """Fetch personal industry jobs from ESI for all users who have given the token."""
    tokens = Token.objects.filter(scopes__name="esi-industry.read_character_jobs.v1")

    for token in tokens:
        try:
            # Alliance Auth
            from allianceauth.eveonline.models import EveCharacter

            character = EveCharacter.objects.filter(
                character_id=token.character_id
            ).first()
            if not character:
                continue

            jobs = esi.client.Industry.GetCharactersCharacterIdIndustryJobs(
                character_id=token.character_id,
                token=token,
                include_completed=True,
            ).results()

            if jobs is not None:
                logger.info(
                    f"Fetched {len(jobs)} character jobs from ESI for character {token.character_id}"
                )
                for job in jobs:
                    job_id = getattr(job, "job_id")
                    blueprint_type_id = getattr(job, "blueprint_type_id", None)
                    product_type_id = getattr(job, "product_type_id", None)
                    ensure_eve_type(blueprint_type_id)
                    ensure_eve_type(product_type_id)

                    existing = CharacterIndustryJob.objects.filter(
                        job_id=job_id
                    ).first()
                    was_active = existing and existing.status not in [
                        "completed",
                        "delivered",
                        "cancelled",
                    ]

                    obj, created = CharacterIndustryJob.objects.update_or_create(
                        job_id=job_id,
                        defaults={
                            "character": character,
                            "activity_id": getattr(job, "activity_id", None),
                            "blueprint_type_id": blueprint_type_id,
                            "product_type_id": product_type_id,
                            "status": getattr(job, "status", None),
                            "start_date": getattr(job, "start_date", None),
                            "end_date": getattr(job, "end_date", None),
                            "runs": getattr(job, "runs", None),
                            "probability": getattr(job, "probability", None),
                            "successful_runs": getattr(job, "successful_runs", None),
                            "cost": getattr(job, "cost", None),
                            "facility_id": getattr(job, "facility_id", None),
                            "station_id": getattr(job, "station_id", None),
                            "location_id": getattr(job, "location_id", None),
                        },
                    )

                    if was_active and obj.status in ["completed", "delivered"]:
                        notify_discord_user(
                            obj.character,
                            f"Your industry job {obj.job_id} has finished.",
                        )

                # Any jobs in our DB for this character that are NOT in the fetched list
                # have aged out of ESI (meaning they are completed/delivered/cancelled > 90 days ago).
                fetched_job_ids = [getattr(j, "job_id") for j in jobs]
                CharacterIndustryJob.objects.filter(
                    character=character, status__in=["active", "paused", "ready"]
                ).exclude(job_id__in=fetched_job_ids).update(status="delivered")

        except HTTPNotModified:
            # 304 Not Modified, ignore
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch character jobs for {token.character_id}: {e}"
            )

    # Link tasks
    link_orphaned_jobs_to_tasks.delay()


@shared_task(name="industry_reforged.tasks.update_corporation_jobs")
@log_task_execution("Update Corporation Jobs")
def update_corporation_jobs():
    """Fetch corporate industry jobs from ESI for configured corps."""
    configs = CorporationSyncConfig.objects.select_related(
        "sync_character", "corporation"
    )

    for config in configs:
        token = Token.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-industry.read_corporation_jobs.v1",
        ).first()

        if not token:
            logger.warning(
                f"No corporate industry token found for {config.sync_character.character_name}"
            )
            continue

        try:
            jobs = esi.client.Industry.GetCorporationsCorporationIdIndustryJobs(
                corporation_id=config.corporation.corporation_id,
                token=token,
                include_completed=True,
            ).results()

            if jobs is not None:
                logger.info(
                    f"Fetched {len(jobs)} corporation jobs from ESI for corporation {config.corporation.corporation_name}"
                )
                for job in jobs:
                    job_id = getattr(job, "job_id")
                    blueprint_type_id = getattr(job, "blueprint_type_id", None)
                    product_type_id = getattr(job, "product_type_id", None)
                    ensure_eve_type(blueprint_type_id)
                    ensure_eve_type(product_type_id)

                    installer_eve_id = getattr(job, "installer_id", None)
                    installer = None
                    if installer_eve_id:
                        # Alliance Auth
                        from allianceauth.eveonline.models import EveCharacter

                        installer = EveCharacter.objects.filter(
                            character_id=installer_eve_id
                        ).first()

                    existing = CorporationIndustryJob.objects.filter(
                        job_id=job_id
                    ).first()
                    was_active = existing and existing.status == "active"

                    # Add job logic similar to character jobs
                    obj, created = CorporationIndustryJob.objects.update_or_create(
                        job_id=job_id,
                        defaults={
                            "corporation": config.corporation,
                            "installer": installer,
                            "activity_id": getattr(job, "activity_id", None),
                            "blueprint_type_id": blueprint_type_id,
                            "product_type_id": product_type_id,
                            "status": getattr(job, "status", None),
                            "start_date": getattr(job, "start_date", None),
                            "end_date": getattr(job, "end_date", None),
                            "runs": getattr(job, "runs", None),
                            "probability": getattr(job, "probability", None),
                            "successful_runs": getattr(job, "successful_runs", None),
                            "cost": getattr(job, "cost", None),
                            "facility_id": getattr(job, "facility_id", None),
                            "station_id": getattr(job, "station_id", None),
                            "location_id": getattr(job, "location_id", None),
                            "wallet_division": getattr(job, "wallet_division", None),
                        },
                    )

                    if was_active and obj.status == "ready":
                        from ..models import CorporationWebhookConfig

                        webhook_config = CorporationWebhookConfig.objects.filter(
                            corporation=config.corporation
                        ).first()
                        if webhook_config and webhook_config.jobs_webhook:
                            from ..utils.discord import send_discord_webhook

                            p_name = (
                                obj.product_type.name if obj.product_type else "Unknown"
                            )
                            i_name = (
                                obj.installer.character_name
                                if obj.installer
                                else "Unknown"
                            )
                            embed = {
                                "title": f"Corporate Job Ready: {p_name}",
                                "description": f"Job **{obj.job_id}** is now ready to be delivered by **{i_name}**.",
                                "color": 15844367,  # Gold
                            }
                            send_discord_webhook(webhook_config.jobs_webhook, embed)

                # Any jobs in our DB for this corp that are NOT in the fetched list
                # have aged out of ESI (meaning they are completed/delivered/cancelled > 90 days ago).
                fetched_job_ids = [getattr(j, "job_id") for j in jobs]
                CorporationIndustryJob.objects.filter(
                    corporation=config.corporation,
                    status__in=["active", "paused", "ready"],
                ).exclude(job_id__in=fetched_job_ids).update(status="delivered")
        except HTTPNotModified:
            # 304 Not Modified, ignore
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch jobs for corp {config.corporation.corporation_id}: {e}"
            )

    # Link tasks
    link_orphaned_jobs_to_tasks.delay()


@shared_task(name="industry_reforged.tasks.link_orphaned_jobs_to_tasks")
@log_task_execution("Link orphaned jobs to tasks")
def link_orphaned_jobs_to_tasks():
    # Django
    from django.db.models import Sum

    from ..models import (
        CharacterIndustryJob,
        CorporationIndustryJob,
        ProductionTask,
        TaskJobLink,
    )

    active_tasks = ProductionTask.objects.filter(status="IN_PRODUCTION")

    for task in active_tasks:
        if not task.assigned_to:
            continue

        try:
            user = task.assigned_to.character_ownership.user
        except Exception:
            continue

        user_character_ids = list(
            user.character_ownerships.all().values_list("character_id", flat=True)
        )

        char_jobs = (
            CharacterIndustryJob.objects.filter(
                character_id__in=user_character_ids,
                product_type_id=task.item_type_id,
                activity_id=task.activity_id,
                status__in=["active", "ready", "delivered"],
            )
            .exclude(taskjoblink__isnull=False)
            .order_by("start_date")
        )

        corp_jobs = (
            CorporationIndustryJob.objects.filter(
                installer_id__in=user_character_ids,
                product_type_id=task.item_type_id,
                activity_id=task.activity_id,
                status__in=["active", "ready", "delivered"],
            )
            .exclude(taskjoblink__isnull=False)
            .order_by("start_date")
        )

        linked_total = (
            task.linked_jobs.aggregate(total=Sum("linked_runs"))["total"] or 0
        )

        # Assume portion_size is 1 if not available, but EveType has portion_size?
        # Actually in production tasks, we usually calculate quantity.
        # Let's get the blueprint portion size from SDE? Or just use task.quantity if it means runs?
        # A task's 'quantity' is the final amount. 'runs' is the quantity / portion_size.
        portion_size = 1
        if (
            task.item_type
            and hasattr(task.item_type, "portion_size")
            and task.item_type.portion_size > 0
        ):
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
                    linked_runs=runs_to_link,
                )
                linked_total += runs_to_link
