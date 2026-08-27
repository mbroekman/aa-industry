"""App Tasks for Blueprints"""

# Standard Library
import logging

# Third Party
from celery import shared_task

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

from .utils import ensure_eve_type, esi, log_task_execution

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.task_sync_corp_blueprints")
@log_task_execution("Task Sync Corp Blueprints")
def task_sync_corp_blueprints():
    from ..models import CorporationSyncConfig

    sync_configs = CorporationSyncConfig.objects.all()
    for config in sync_configs:
        try:
            _sync_corp_blueprints(config)
        except Exception as e:
            logger.error(
                f"Failed to sync blueprints for {config.corporation.corporation_name}: {e}"
            )


def _sync_corp_blueprints(config):
    from ..models import CorpBlueprint

    corp_id = config.corporation.corporation_id
    token = Token.get_token(
        config.sync_character.character_id, ["esi-corporations.read_blueprints.v1"]
    )
    if not token:
        logger.warning(
            f"No token with read_blueprints scope for {config.sync_character.character_name}"
        )
        return

    db_is_empty = not CorpBlueprint.objects.filter(
        corporation=config.corporation
    ).exists()

    try:
        req = esi.client.Corporation.GetCorporationsCorporationIdBlueprints(
            corporation_id=corp_id, page=1, token=token
        )
        if db_is_empty:
            req._clear_etag()
            req._clear_cache()

        blueprints_data = req.results()
    except HTTPNotModified:
        return
    except Exception as e:
        logger.error(f"Failed to fetch blueprints for corp {corp_id}: {e}")
        return

    seen_item_ids = set()

    for bp in blueprints_data:
        item_id = getattr(bp, "item_id", None)
        type_id = getattr(bp, "type_id", None)
        location_id = getattr(bp, "location_id", None)
        location_flag = getattr(bp, "location_flag", None)
        quantity = getattr(bp, "quantity", -1)
        time_efficiency = getattr(bp, "time_efficiency", 0)
        material_efficiency = getattr(bp, "material_efficiency", 0)
        runs = getattr(bp, "runs", -1)

        if not item_id or not type_id:
            continue

        seen_item_ids.add(item_id)

        ensure_eve_type(type_id)

        CorpBlueprint.objects.update_or_create(
            item_id=item_id,
            defaults={
                "corporation": config.corporation,
                "eve_type_id": type_id,
                "location_id": location_id,
                "location_flag": location_flag,
                "quantity": quantity,
                "time_efficiency": time_efficiency,
                "material_efficiency": material_efficiency,
                "runs": runs,
            },
        )

    # Delete blueprints that no longer exist for this corp
    CorpBlueprint.objects.filter(corporation=config.corporation).exclude(
        item_id__in=seen_item_ids
    ).delete()
