"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task

from .utils import _get_security_space, esi, log_task_execution

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.update_industry_facilities")
@log_task_execution("Update Industry Facilities")
def update_industry_facilities():
    """Fetch facility names from ESI to populate IndustryFacility cache."""
    # Third Party
    import requests

    # Alliance Auth
    from allianceauth.services.hooks import get_extension_logger
    from esi.models import Token as EveToken

    from ..models import (
        CharacterIndustryJob,
        CorporationIndustryJob,
        CorporationSyncConfig,
        IndustryFacility,
    )

    logger = get_extension_logger(__name__)

    # Collect all unique location/facility IDs
    facility_ids = set()
    for model in [CharacterIndustryJob, CorporationIndustryJob]:
        facility_ids.update(
            model.objects.exclude(facility_id__isnull=True).values_list(
                "facility_id", flat=True
            )
        )
        facility_ids.update(
            model.objects.exclude(location_id__isnull=True).values_list(
                "location_id", flat=True
            )
        )

    # Also collect location_ids from Corporate Assets

    configs = CorporationSyncConfig.objects.select_related("sync_character").all()
    for config in configs:
        token = EveToken.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-assets.read_corporation_assets.v1",
        ).first()
        if token:
            try:
                assets = esi.client.Assets.GetCorporationsCorporationIdAssets(
                    corporation_id=config.corporation.corporation_id, token=token
                ).results()
                for asset in assets:
                    if getattr(asset, "location_type", "") in [
                        "station",
                        "other",
                    ] and getattr(asset, "location_id", None):
                        facility_ids.add(asset.location_id)
            except Exception as e:
                logger.error(f"Failed to fetch assets for facility resolution: {e}")

        # Fetch Corporate Structures
        token_str = EveToken.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-corporations.read_structures.v1",
        ).first()
        if token_str:
            try:
                structures = (
                    esi.client.Corporation.GetCorporationsCorporationIdStructures(
                        corporation_id=config.corporation.corporation_id,
                        token=token_str,
                    ).results()
                )
                for s in structures:
                    if getattr(s, "structure_id", None):
                        facility_ids.add(s.structure_id)
            except Exception as e:
                logger.error(f"Failed to fetch structures for facility resolution: {e}")

    if not facility_ids:
        return

    # Identify missing ones
    existing = set(IndustryFacility.objects.values_list("facility_id", flat=True))
    missing = facility_ids - existing

    if not missing:
        return

    logger.info(f"Attempting to resolve {len(missing)} unknown facilities...")

    valid_tokens = []
    configs = CorporationSyncConfig.objects.select_related("sync_character").all()
    for config in configs:
        token = EveToken.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-universe.read_structures.v1",
        ).first()
        if token:
            valid_tokens.append(token)

    for loc_id in missing:
        try:
            if loc_id < 100000000:
                # NPC Station
                st_resp = requests.get(
                    f"https://esi.evetech.net/latest/universe/stations/{loc_id}/?datasource=tranquility"
                )
                if st_resp.status_code == 200:
                    data = st_resp.json()
                    sys_id = data.get("system_id", None)
                    IndustryFacility.objects.create(
                        facility_id=loc_id,
                        name=data.get("name", f"Station {loc_id}"),
                        owner_id=data.get("owner", None),
                        solar_system_id=sys_id,
                        type_id=data.get("type_id", None),
                        security_space=_get_security_space(sys_id),
                        is_production_facility=False,
                    )
            else:
                # Upwell Structure

                for token in valid_tokens:
                    access_token = token.valid_access_token()
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    }
                    str_resp = requests.get(
                        f"https://esi.evetech.net/latest/universe/structures/{loc_id}/?datasource=tranquility",
                        headers=headers,
                    )
                    if str_resp.status_code == 200:
                        data = str_resp.json()
                        sys_id = data.get("solar_system_id", None)
                        IndustryFacility.objects.create(
                            facility_id=loc_id,
                            name=data.get("name", f"Structure {loc_id}"),
                            owner_id=data.get("owner_id", None),
                            solar_system_id=sys_id,
                            type_id=data.get("type_id", None),
                            security_space=_get_security_space(sys_id),
                            is_production_facility=False,
                        )

                        break
        except Exception as e:
            logger.error(f"Error resolving facility {loc_id}: {e}")


@shared_task(name="industry_reforged.tasks.sync_facility_rigs")
@log_task_execution("Sync Facility Rigs")
def sync_facility_rigs():
    """Fetch corporate assets and automatically determine installed rigs for facilities."""
    # Alliance Auth
    from allianceauth.services.hooks import get_extension_logger
    from esi.models import Token

    from ..models import (
        CorporationSyncConfig,
        IndustryFacility,
        IndustryFacilityRig,
        IndustryRig,
    )

    logger = get_extension_logger(__name__)

    # Find all corporations that have facilities
    facility_corps = set(
        IndustryFacility.objects.exclude(owner_id__isnull=True).values_list(
            "owner_id", flat=True
        )
    )
    if not facility_corps:
        return

    facilities_by_corp = {}
    for f in IndustryFacility.objects.all():
        if f.owner_id:
            facilities_by_corp.setdefault(f.owner_id, []).append(f)

    for corp_id in facility_corps:
        if not corp_id:
            continue

        sync_config = CorporationSyncConfig.objects.filter(
            corporation_id=corp_id
        ).first()
        if not sync_config:
            continue

        token = Token.objects.filter(
            character_id=sync_config.sync_character.character_id,
            scopes__name="esi-assets.read_corporation_assets.v1",
        ).first()

        if not token:
            continue

        try:
            logger.info(f"Fetching assets for corp {corp_id} to sync facility rigs...")
            assets = esi.client.Assets.GetCorporationsCorporationIdAssets(
                corporation_id=corp_id, token=token
            ).results()

            facilities = facilities_by_corp.get(corp_id, [])
            facility_ids = {f.facility_id: f for f in facilities}

            # Keep track of found rigs to remove old ones
            found_rigs = {f.id: [] for f in facilities}

            for asset in assets:
                location_id = getattr(asset, "location_id")
                flag_id = getattr(asset, "location_flag")

                # If asset is in one of our known facilities and flag implies a rig slot
                if (
                    location_id in facility_ids
                    and flag_id
                    and flag_id.startswith("RigSlot")
                ):
                    type_id = getattr(asset, "type_id")

                    # Try to map to an IndustryRig
                    rig = IndustryRig.objects.filter(type_id=type_id).first()
                    if rig:
                        facility = facility_ids[location_id]
                        # Create or get the linkage
                        fr, created = IndustryFacilityRig.objects.get_or_create(
                            facility=facility, rig=rig
                        )
                        found_rigs[facility.id].append(rig.type_id)
                        if created:
                            logger.info(
                                f"Auto-linked rig {rig.name} to facility {facility.name}"
                            )

            # Optional: Remove rigs that are no longer installed
            for f in facilities:
                current_rigs = found_rigs[f.id]
                removed = IndustryFacilityRig.objects.filter(facility=f).exclude(
                    rig__type_id__in=current_rigs
                )
                if removed.exists():
                    logger.info(
                        f"Removing {removed.count()} old rigs from facility {f.name}"
                    )
                    removed.delete()

        except Exception as e:
            logger.error(f"Failed to sync rigs for corp {corp_id}: {e}")
