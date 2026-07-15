"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

from .utils import ensure_eve_type, esi, log_task_execution

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.task_sync_corp_inventory")
@log_task_execution("Task Sync Corp Inventory")
def task_sync_corp_inventory():
    """Fetch corporate assets from ESI for all configured Industry Facilities."""

    from ..models import CorpInventory, CorporationSyncConfig, IndustryFacility

    # Get all configured industry facilities
    facility_ids = set(
        IndustryFacility.objects.filter(sync_inventory=True).values_list(
            "facility_id", flat=True
        )
    )
    if not facility_ids:
        return

    # Fetch inventory for all corps that have a sync config
    sync_configs = CorporationSyncConfig.objects.all()

    for sync_config in sync_configs:
        corp = sync_config.corporation
        corp_id = corp.corporation_id

        token = Token.objects.filter(
            character_id=sync_config.sync_character.character_id,
            scopes__name="esi-assets.read_corporation_assets.v1",
        ).first()

        if not token:
            continue

        try:
            assets = esi.client.Assets.GetCorporationsCorporationIdAssets(
                corporation_id=corp_id, token=token
            ).results()

            # Build a map of item_id -> location_id to resolve nested containers
            item_locations = {}
            for asset in assets:
                # Note: some assets might not have item_id (e.g. blueprints in some endpoints), but corp assets endpoint usually does.
                item_id = getattr(asset, "item_id", getattr(asset, "id", None))
                if item_id:
                    item_locations[item_id] = getattr(asset, "location_id")

            def get_root_location(loc_id):
                visited = set()
                while loc_id not in facility_ids and loc_id in item_locations:
                    if loc_id in visited:
                        break  # Prevent infinite loop in case of circular references
                    visited.add(loc_id)
                    loc_id = item_locations[loc_id]
                return loc_id

            # Filter assets matching location_id (including nested)
            filtered_assets = []
            for asset in assets:
                loc_id = getattr(asset, "location_id")
                root_loc_id = get_root_location(loc_id)

                # Check if this asset is in a configured facility
                if root_loc_id in facility_ids:
                    type_id = getattr(asset, "type_id")
                    quantity = getattr(
                        asset, "quantity", 1
                    )  # single items don't always have quantity field
                    ensure_eve_type(type_id)
                    filtered_assets.append(
                        {
                            "type_id": type_id,
                            "quantity": quantity,
                            "location_id": root_loc_id,
                        }
                    )

            # Update CorpInventory (only for items not manually overridden)
            # Reset all non-manual overridden quantities for this corp to 0
            # so that items that are no longer there are properly zeroed out.
            CorpInventory.objects.filter(
                corporation=corp, manual_override=False
            ).update(quantity=0)

            if filtered_assets:

                # Group by type and location
                # Standard Library
                from collections import defaultdict

                grouped = defaultdict(int)
                for fa in filtered_assets:
                    grouped[(fa["type_id"], fa["location_id"])] += fa["quantity"]

                for (type_id, loc_id), qty in grouped.items():
                    inv, created = CorpInventory.objects.get_or_create(
                        corporation=corp,
                        item_type_id=type_id,
                        location_id=loc_id,
                        defaults={"quantity": qty},
                    )
                    if not inv.manual_override:
                        inv.quantity = qty
                        inv.save()

            # Check low stock thresholds
            # Standard Library
            import datetime

            # Django
            from django.db.models import Sum
            from django.utils import timezone

            from ..models import CorpItemConfig, CorporationWebhookConfig

            now = timezone.now()
            configs = CorpItemConfig.objects.filter(
                corporation_id=corp_id, target_threshold__gt=0
            )
            webhook_config = CorporationWebhookConfig.objects.filter(
                corporation_id=corp_id
            ).first()

            for config in configs:
                total_qty = (
                    CorpInventory.objects.filter(
                        corporation_id=corp_id, item_type=config.item_type
                    ).aggregate(total=Sum("quantity"))["total"]
                    or 0
                )

                if total_qty < config.target_threshold:
                    if not config.last_low_stock_warning or (
                        now - config.last_low_stock_warning
                    ) > datetime.timedelta(days=1):
                        if webhook_config and webhook_config.inventory_webhook:
                            from ..utils.discord import send_discord_webhook

                            embed = {
                                "title": f"Low Stock Warning: {config.item_type.name}",
                                "description": f"Total stock is **{total_qty}**, which is below the threshold of **{config.target_threshold}**.",
                                "color": 15158332,  # Red
                            }
                            send_discord_webhook(
                                webhook_config.inventory_webhook, embed
                            )
                        config.last_low_stock_warning = now
                        config.save()

        except HTTPNotModified:
            # 304 Not Modified is expected, nothing changed.
            pass
        except Exception as e:
            logger.error(f"Failed to fetch assets for corp {corp_id}: {e}")
