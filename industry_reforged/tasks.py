"""App Tasks"""

# Standard Library
import datetime
import logging
import time
import traceback
from functools import wraps

# Third Party
from celery import shared_task
from eveuniverse.models import EveType

# Django
from django.utils import timezone

# Alliance Auth
from allianceauth import __title_useragent__, __url__, __version__
from allianceauth.eveonline import __esi_compatibility_date__
from esi.exceptions import HTTPNotModified
from esi.models import Token
from esi.openapi_clients import ESIClientProvider

from .models import (
    CharacterIndustryJob,
    CharacterPlanet,
    CorporationIndustryJob,
    CorporationSyncConfig,
    PlanetPin,
    TaskExecutionLog,
)

logger = logging.getLogger(__name__)


def log_task_execution(task_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log_entry, _ = TaskExecutionLog.objects.update_or_create(
                task_name=task_name,
                defaults={
                    "status": "RUNNING",
                    "message": "",
                    "last_run": timezone.now(),
                },
            )
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                log_entry.status = "SUCCESS"
                log_entry.message = "Task completed successfully."
                return result
            except Exception as e:
                log_entry.status = "FAILED"
                log_entry.message = f"Error: {str(e)}\n\n{traceback.format_exc()}"
                raise
            finally:
                log_entry.duration_seconds = time.time() - start_time
                log_entry.last_run = timezone.now()
                log_entry.save()

        return wrapper

    return decorator


class IndustryESIProvider(ESIClientProvider):
    def __init__(self) -> None:
        super().__init__(
            __esi_compatibility_date__,
            __title_useragent__,
            __version__,
            __url__,
            operations=[
                "GetCharactersCharacterIdIndustryJobs",
                "GetCorporationsCorporationIdIndustryJobs",
                "GetCharactersCharacterIdPlanets",
                "GetCharactersCharacterIdPlanetsPlanetId",
                "GetUniverseSchematicsSchematicId",
                "GetCorporationsCorporationIdAssets",
                "PostUniverseNames",
                "PostUniverseIds",
                "GetUniverseStructuresStructureId",
                "GetUniverseStationsStationId",
                "GetCorporationsCorporationIdWallets",
                "GetCorporationsCorporationIdWalletsDivisionJournal",
            ],
        )


esi = IndustryESIProvider()


def notify_discord_user(character, message):
    try:
        # Alliance Auth
        from allianceauth.services.modules.discord.models import DiscordUser

        user = character.character_ownership.user
        discord_user = DiscordUser.objects.get(user=user)

        # We need the discord client to send DM
        # Alliance Auth
        from allianceauth.services.modules.discord.discord_client import DiscordClient

        client = DiscordClient()

        # create_dm creates a dm channel
        dm_channel = client.create_dm(discord_user.uid)
        if dm_channel and "id" in dm_channel:
            client.create_message(channel_id=dm_channel["id"], content=message)
    except Exception as e:
        logger.error(f"Failed to send discord DM to {character.character_name}: {e}")


def ensure_eve_type(type_id):
    if type_id:
        try:
            # Third Party
            from eveuniverse.models import EveType

            EveType.objects.get_or_create_esi(id=type_id)
        except Exception as e:
            logger.warning(f"Could not fetch EveType {type_id}: {e}")


@shared_task
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

            jobs = []
            page = 1
            while True:
                response = esi.client.Industry.GetCharactersCharacterIdIndustryJobs(
                    character_id=token.character_id,
                    token=token,
                    include_completed=True,
                    page=page,
                ).response()

                if response.swagger_result:
                    jobs.extend(response.swagger_result)

                # Check for X-Pages header
                pages = response.header.get("X-Pages", 1)
                if page >= int(pages):
                    break
                page += 1

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


@shared_task
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
            jobs = []
            page = 1
            while True:
                response = esi.client.Industry.GetCorporationsCorporationIdIndustryJobs(
                    corporation_id=config.corporation.corporation_id,
                    token=token,
                    include_completed=True,
                    page=page,
                ).response()

                if response.swagger_result:
                    jobs.extend(response.swagger_result)

                pages = response.header.get("X-Pages", 1)
                if page >= int(pages):
                    break
                page += 1

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
                        from .models import CorporationWebhookConfig

                        webhook_config = CorporationWebhookConfig.objects.filter(
                            corporation=config.corporation
                        ).first()
                        if webhook_config and webhook_config.jobs_webhook:
                            from .utils.discord import send_discord_webhook

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


@shared_task
@log_task_execution("Update Character Pi")
def update_character_pi(character_id=None):
    """Fetch PI planets and pins from ESI for all users or a specific user."""
    tokens_query = Token.objects.filter(scopes__name="esi-planets.manage_planets.v1")
    if character_id:
        tokens_query = tokens_query.filter(character_id=character_id)

    for token in tokens_query:
        try:
            # Alliance Auth
            from allianceauth.eveonline.models import EveCharacter

            character = EveCharacter.objects.filter(
                character_id=token.character_id
            ).first()
            if not character:
                continue

            try:
                planets = (
                    esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanets(
                        character_id=token.character_id, token=token
                    ).result()
                )

                if planets is not None:
                    logger.info(
                        f"Fetched {len(planets)} PI planets from ESI for character {token.character_id}"
                    )

                    for p in planets:
                        planet_id = getattr(p, "planet_id")
                        planet_type_str = getattr(p, "planet_type")

                        PLANET_TYPE_MAP = {
                            "temperate": 11,
                            "ice": 12,
                            "gas": 13,
                            "oceanic": 2014,
                            "lava": 2015,
                            "barren": 2016,
                            "storm": 2017,
                            "plasma": 2063,
                        }
                        planet_type_id = PLANET_TYPE_MAP.get(planet_type_str, 2016)

                        system_id = getattr(p, "solar_system_id")
                        upgrade_level = getattr(p, "upgrade_level")
                        num_pins = getattr(p, "num_pins")

                        ensure_eve_type(planet_type_id)

                        CharacterPlanet.objects.update_or_create(
                            character=character,
                            planet_id=planet_id,
                            defaults={
                                "system_id": system_id,
                                "planet_type_id": planet_type_id,
                                "upgrade_level": upgrade_level,
                                "num_pins": num_pins,
                            },
                        )
            except HTTPNotModified:
                # Planet list hasn't changed, but we still must check pins
                pass

            # Now fetch pins for all known planets for this character
            char_planets = CharacterPlanet.objects.filter(character=character)
            for char_planet in char_planets:
                try:
                    planet_details = esi.client.Planetary_Interaction.GetCharactersCharacterIdPlanetsPlanetId(
                        character_id=token.character_id,
                        planet_id=char_planet.planet_id,
                        token=token,
                    ).result()

                    pins = getattr(planet_details, "pins", [])

                    # Keep track of active pin ids to delete removed pins
                    active_pin_ids = []

                    # ESI Bug: Planetary Interaction pins always return the "Barren" variant's type_id.
                    # We must map it back to the correct variant for the given planet type.
                    PI_PIN_MAP = {
                        2473: {
                            "Temperate": 2481,
                            "Ice": 2493,
                            "Gas": 2492,
                            "Oceanic": 2490,
                            "Lava": 2469,
                            "Barren": 2473,
                            "Storm": 2483,
                            "Plasma": 2471,
                        },
                        2474: {
                            "Temperate": 2480,
                            "Ice": 2491,
                            "Gas": 2494,
                            "Oceanic": 2485,
                            "Lava": 2470,
                            "Barren": 2474,
                            "Storm": 2484,
                            "Plasma": 2472,
                        },
                        2475: {"Temperate": 2482, "Barren": 2475},
                        2524: {
                            "Temperate": 2254,
                            "Ice": 2533,
                            "Gas": 2534,
                            "Oceanic": 2525,
                            "Lava": 2549,
                            "Barren": 2524,
                            "Storm": 2550,
                            "Plasma": 2551,
                        },
                        2541: {
                            "Temperate": 2562,
                            "Ice": 2257,
                            "Gas": 2536,
                            "Oceanic": 2535,
                            "Lava": 2558,
                            "Barren": 2541,
                            "Storm": 2561,
                            "Plasma": 2560,
                        },
                        2544: {
                            "Temperate": 2256,
                            "Ice": 2552,
                            "Gas": 2543,
                            "Oceanic": 2542,
                            "Lava": 2555,
                            "Barren": 2544,
                            "Storm": 2557,
                            "Plasma": 2556,
                        },
                        2848: {
                            "Temperate": 3068,
                            "Ice": 3061,
                            "Gas": 3060,
                            "Oceanic": 3063,
                            "Lava": 3062,
                            "Barren": 2848,
                            "Storm": 3067,
                            "Plasma": 3064,
                        },
                    }
                    PLANET_ID_TO_NAME = {
                        11: "Temperate",
                        12: "Ice",
                        13: "Gas",
                        2014: "Oceanic",
                        2015: "Lava",
                        2016: "Barren",
                        2017: "Storm",
                        2063: "Plasma",
                    }

                    # Django
                    from django.utils import timezone

                    now = timezone.now()

                    for pin in pins:
                        pin_id = getattr(pin, "pin_id")
                        active_pin_ids.append(pin_id)

                        type_id = getattr(pin, "type_id")

                        # Apply mapping to fix ESI bug (ESI sometimes returns generic variants like Barren or Storm for all planets)
                        planet_category = PLANET_ID_TO_NAME.get(
                            char_planet.planet_type_id, "Barren"
                        )
                        for mapping in PI_PIN_MAP.values():
                            if type_id in mapping.values():
                                type_id = mapping.get(planet_category, type_id)
                                break

                        schematic_id = getattr(pin, "schematic_id", None)
                        extractor_details = getattr(pin, "extractor_details", None)

                        ensure_eve_type(type_id)

                        install_time = getattr(pin, "install_time", None)
                        expiry_time = getattr(pin, "expiry_time", None)
                        last_cycle_start = getattr(pin, "last_cycle_start", None)

                        product_type_id = None
                        cycle_time = None
                        extraction_yield = None

                        if schematic_id:
                            # Try to find another pin that already resolved this schematic
                            existing = (
                                PlanetPin.objects.filter(schematic_id=schematic_id)
                                .exclude(product_type_id__isnull=True)
                                .first()
                            )
                            if existing:
                                product_type_id = existing.product_type_id
                            else:
                                try:
                                    # Third Party
                                    import requests

                                    # Use raw requests to bypass django-esi caching which throws HTTPNotModified
                                    url = f"https://esi.evetech.net/latest/universe/schematics/{schematic_id}/"
                                    r = requests.get(url, timeout=10)
                                    if r.status_code == 200:
                                        data = r.json()
                                        schematic_name = data.get("schematic_name")

                                        t = EveType.objects.filter(
                                            name=schematic_name
                                        ).first()

                                        # Fix plural mismatch between schematic names and item names for certain PI products
                                        if not t and not schematic_name.endswith("s"):
                                            t = EveType.objects.filter(
                                                name=schematic_name + "s"
                                            ).first()

                                        if not t:
                                            # Fallback: resolve ID from ESI if not loaded locally
                                            try:
                                                resolve_name = (
                                                    schematic_name + "s"
                                                    if schematic_name
                                                    in [
                                                        "High-Tech Transmitter",
                                                        "Ukomi Superconductor",
                                                        "Transcranial Microcontroller",
                                                    ]
                                                    else schematic_name
                                                )
                                                id_url = "https://esi.evetech.net/latest/universe/ids/"
                                                id_res = requests.post(
                                                    id_url,
                                                    json=[resolve_name],
                                                    timeout=10,
                                                )
                                                if id_res.status_code == 200:
                                                    id_data = id_res.json()
                                                    inv_types = id_data.get(
                                                        "inventory_types", []
                                                    )
                                                    if inv_types:
                                                        first_inv = inv_types[0]
                                                        resolved_id = first_inv.get(
                                                            "id"
                                                        )

                                                    if resolved_id:
                                                        ensure_eve_type(resolved_id)
                                                        t = EveType.objects.filter(
                                                            id=resolved_id
                                                        ).first()
                                            except Exception as inner_e:
                                                logger.warning(
                                                    f"Could not resolve universe ID for {schematic_name}: {inner_e}"
                                                )

                                        if t:
                                            product_type_id = t.id
                                except Exception as e:
                                    logger.warning(
                                        f"Could not resolve schematic {schematic_id}: {e}"
                                    )

                        if extractor_details:
                            product_type_id = getattr(
                                extractor_details, "product_type_id", None
                            )
                            cycle_time = getattr(extractor_details, "cycle_time", None)
                            qty_per_cycle = getattr(
                                extractor_details, "qty_per_cycle", None
                            )
                            extraction_yield = qty_per_cycle
                            ensure_eve_type(product_type_id)

                        contents_raw = getattr(pin, "contents", [])
                        contents_volume = 0.0
                        contents_json = {}

                        if contents_raw:
                            for item in contents_raw:
                                item_type_id = getattr(item, "type_id")
                                amount = getattr(item, "amount")
                                ensure_eve_type(item_type_id)
                                item_type = EveType.objects.filter(
                                    id=item_type_id
                                ).first()
                                if item_type:
                                    vol = float(item_type.volume or 0.0) * float(amount)
                                    contents_volume += vol
                                    if item_type.name in contents_json:
                                        contents_json[item_type.name][
                                            "amount"
                                        ] += amount
                                        contents_json[item_type.name]["volume"] += vol
                                    else:
                                        contents_json[item_type.name] = {
                                            "type_id": item_type_id,
                                            "amount": amount,
                                            "volume": vol,
                                        }

                        capacity = 0.0
                        pin_type = EveType.objects.filter(id=type_id).first()
                        if pin_type:
                            capacity = float(getattr(pin_type, "capacity", 0.0) or 0.0)

                        pin_obj, created = PlanetPin.objects.update_or_create(
                            planet=char_planet,
                            pin_id=pin_id,
                            defaults={
                                "type_id": type_id,
                                "install_time": install_time,
                                "expiry_time": expiry_time,
                                "cycle_time": cycle_time,
                                "extraction_yield": extraction_yield,
                                "product_type_id": product_type_id,
                                "schematic_id": schematic_id,
                                "last_cycle_start": last_cycle_start,
                                "contents_volume": contents_volume,
                                "capacity": capacity,
                                "contents": contents_json,
                            },
                        )

                        # Notification Logic for Extractor Expiry
                        if pin_obj.is_extractor and pin_obj.expiry_time:
                            if now >= pin_obj.expiry_time:
                                if not pin_obj.notification_sent:
                                    planet_name = (
                                        char_planet.planet_type.name
                                        if char_planet.planet_type
                                        else f"Planeet {char_planet.planet_id}"
                                    )
                                    message = f"Je extractor op je **{planet_name}** is zojuist gestopt. Tijd om deze opnieuw aan te zetten!"
                                    notify_discord_user(character, message)
                                    pin_obj.notification_sent = True
                                    pin_obj.save()
                            else:
                                # Extractor has future expiry, meaning it was restarted
                                if pin_obj.notification_sent:
                                    pin_obj.notification_sent = False
                                    pin_obj.save()

                    # Remove pins that are no longer on the planet
                    char_planet.pins.exclude(pin_id__in=active_pin_ids).delete()

                except HTTPNotModified:
                    continue
                except Exception as e:
                    logger.error(
                        f"Failed to fetch PI pins for planet {char_planet.planet_id}: {e}"
                    )

        except HTTPNotModified:
            # 304 Not Modified is expected, nothing changed.
            pass
        except Exception as e:
            logger.error(f"Failed to fetch PI for {token.character_id}: {e}")


@shared_task
@log_task_execution("Task Sync Corp Inventory")
def task_sync_corp_inventory():
    """Fetch corporate assets from ESI for all configured Industry Facilities."""

    from .models import CorpInventory, CorporationSyncConfig, IndustryFacility

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

            from .models import CorpItemConfig, CorporationWebhookConfig

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
                            from .utils.discord import send_discord_webhook

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


@shared_task
@log_task_execution("Task Pull Market Data")
def task_pull_market_data():
    """Fetch Jita prices for PI, Moon, Gas, and Minerals via Fuzzwork."""
    logger.info("Market Data Pull initiated.")
    # Implementation requires querying the fuzzwork market API for the specific types
    # This is a placeholder for the actual API call logic
    pass


@shared_task
@log_task_execution("Task Bom Explosion")
def task_bom_explosion(order_id):
    """Calculate BOM and create ProductionTasks based on Build vs Buy configuration."""
    from .models import CorpItemConfig, MemberOrder

    order = MemberOrder.objects.filter(id=order_id).first()
    if not order:
        return

    for item in order.items.all():
        config = CorpItemConfig.objects.filter(item_type=item.item_type).first()

        # Determine build or buy
        if config and config.build_or_buy == "BUY":
            # Create a BUY task
            pass
        else:
            # SDE or Fuzzwork explosion
            pass


@shared_task
@log_task_execution("Task Sync Corp Wallets")
def task_sync_corp_wallets():
    """Fetch corporate wallets and journals from ESI."""
    from .models import CorporationSyncConfig, CorpWalletDivision, CorpWalletJournal

    configs = CorporationSyncConfig.objects.select_related(
        "sync_character", "corporation"
    )

    for config in configs:
        token = Token.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-wallet.read_corporation_wallets.v1",
        ).first()

        if not token:
            logger.warning(
                f"No corporate wallet token found for {config.sync_character.character_name}"
            )
            continue

        try:
            # 1. Fetch division balances
            wallets = esi.client.Wallet.GetCorporationsCorporationIdWallets(
                corporation_id=config.corporation.corporation_id, token=token
            ).result()

            divisions_map = {}
            if wallets:
                for w in wallets:
                    division_id = getattr(w, "division")
                    balance = getattr(w, "balance")
                    div, created = CorpWalletDivision.objects.update_or_create(
                        corporation=config.corporation,
                        division=division_id,
                        defaults={"balance": balance},
                    )
                    # We might not know the name initially, default to Division X
                    if not div.name:
                        div.name = f"Division {division_id}"
                        div.save()
                    divisions_map[division_id] = div

                    from .models import CorporationWebhookConfig

                    now = timezone.now()

                    webhook_config = CorporationWebhookConfig.objects.filter(
                        corporation=config.corporation
                    ).first()
                    threshold = (
                        webhook_config.wallet_warning_threshold
                        if webhook_config
                        else 500000000
                    )

                    if balance < threshold:
                        if not div.last_warning or (
                            now - div.last_warning
                        ) > datetime.timedelta(days=1):
                            if webhook_config and webhook_config.wallets_webhook:
                                from .utils.discord import send_discord_webhook

                                embed = {
                                    "title": f"Low Wallet Balance: {div.name}",
                                    "description": f"Balance is **{balance:,.2f} ISK**, which is below the threshold of **{threshold:,.2f} ISK**.",
                                    "color": 15158332,  # Red
                                }
                                send_discord_webhook(
                                    webhook_config.wallets_webhook, embed
                                )
                            div.last_warning = now
                            div.save()

            # 2. Fetch journal entries for each division
            for division_id, div_obj in divisions_map.items():
                try:
                    journal_entries = esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal(
                        corporation_id=config.corporation.corporation_id,
                        division=division_id,
                        token=token,
                    ).result()

                    if journal_entries:
                        journal_objects = []
                        seen_j_ids = set()
                        for entry in journal_entries:
                            j_id = getattr(entry, "id")
                            if j_id in seen_j_ids:
                                continue
                            seen_j_ids.add(j_id)

                            # Check if exists to avoid bulk_create collisions (if we weren't ignoring conflicts)
                            if not CorpWalletJournal.objects.filter(
                                division=div_obj, journal_id=j_id
                            ).exists():
                                journal_objects.append(
                                    CorpWalletJournal(
                                        division=div_obj,
                                        journal_id=j_id,
                                        date=getattr(entry, "date"),
                                        ref_type=getattr(entry, "ref_type"),
                                        amount=getattr(entry, "amount", None),
                                        balance=getattr(entry, "balance", None),
                                        reason=str(getattr(entry, "reason", ""))[:250],
                                        description=str(
                                            getattr(entry, "description", "")
                                        )[:250],
                                        first_party_id=getattr(
                                            entry, "first_party_id", None
                                        ),
                                        second_party_id=getattr(
                                            entry, "second_party_id", None
                                        ),
                                        tax=getattr(entry, "tax", None),
                                        tax_receiver_id=getattr(
                                            entry, "tax_receiver_id", None
                                        ),
                                    )
                                )
                        if journal_objects:
                            CorpWalletJournal.objects.bulk_create(
                                journal_objects, ignore_conflicts=True
                            )

                except HTTPNotModified:
                    continue
                except Exception as e:
                    logger.error(
                        f"Failed to fetch journal for div {division_id} (corp {config.corporation.corporation_id}): {e}"
                    )

        except HTTPNotModified:
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch wallets for corp {config.corporation.corporation_id}: {e}"
            )

    # After syncing wallets, check for any payments that match pending payouts or orders
    task_process_wallet_payments.delay()


@shared_task
@log_task_execution("Task Notify Expired Extractors")
def task_notify_expired_extractors():
    """Check for expired PI extractors and send notifications via Alliance Auth notify."""
    # Django
    from django.utils import timezone

    # Alliance Auth
    from allianceauth.notifications.models import Notification

    from .models import PlanetPin

    now = timezone.now()

    expired_pins = PlanetPin.objects.filter(
        expiry_time__lte=now, notification_sent=False
    ).select_related("planet__character__character_ownership__user")

    for pin in expired_pins:
        if pin.is_extractor:
            user = None
            try:
                user = pin.planet.character.character_ownership.user
            except Exception:
                pass

            if user:
                planet_name = pin.planet.name
                char_name = pin.planet.character.character_name
                message = f"Your PI Extractor on planet **{planet_name}** ({char_name}) has expired and stopped extracting. It's time to restart your extraction program!"
                Notification.objects.notify_user(
                    user=user,
                    title="PI Extractor Expired",
                    message=message,
                    level="warning",
                )

            # Mark as notified even if user doesn't exist, so we don't keep trying
            pin.notification_sent = True
            pin.save(update_fields=["notification_sent"])


@shared_task
@log_task_execution("Task Process Wallet Payments")
def task_process_wallet_payments():
    """Process new wallet journal entries and match them to Orders and Payouts."""
    from .models import (
        BuilderPayoutBatch,
        CorpWalletJournal,
        EveCorporationInfo,
        MemberOrder,
        WalletJournalSyncState,
    )

    # Ensure all corps have a sync state
    for corp in EveCorporationInfo.objects.all():
        WalletJournalSyncState.objects.get_or_create(corporation=corp)

    states = WalletJournalSyncState.objects.all()

    # Pre-fetch pending payments
    unpaid_orders = {
        order.payment_reference: order
        for order in MemberOrder.objects.filter(is_paid=False)
        .exclude(payment_reference__isnull=True)
        .exclude(payment_reference="")
    }
    pending_batches = {
        batch.payment_reference: batch
        for batch in BuilderPayoutBatch.objects.filter(status="PENDING")
    }

    if not unpaid_orders and not pending_batches:
        return  # Nothing to look for

    for state in states:
        entries = CorpWalletJournal.objects.filter(
            division__corporation=state.corporation,
            journal_id__gt=state.last_journal_id,
        ).order_by("journal_id")

        if not entries.exists():
            continue

        highest_id = state.last_journal_id

        for entry in entries:
            highest_id = max(highest_id, entry.journal_id)
            reason = entry.reason or ""

            # Incoming payment (Client -> Corp)
            if entry.amount is not None and entry.amount > 0:
                # Iterate over a list of items so we can safely modify/pop the dict if needed
                for ref, order in list(unpaid_orders.items()):
                    if ref in reason:
                        order.amount_paid += entry.amount
                        note = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Auto Sync: Received payment of {entry.amount:,.2f} ISK."
                        if order.notes:
                            order.notes += f"\n{note}"
                        else:
                            order.notes = note

                        if order.amount_paid >= order.total_price:
                            order.is_paid = True
                            unpaid_orders.pop(ref, None)

                        order.save()
                        break

            # Outgoing payment (Corp -> Builder)
            elif entry.amount is not None and entry.amount < 0:
                for ref, batch in pending_batches.items():
                    if ref in reason and abs(entry.amount) >= batch.total_amount:
                        batch.status = "PAID"
                        batch.paid_at = timezone.now()
                        batch.save()
                        pending_batches.pop(ref, None)
                        break

        # Save highest processed ID
        state.last_journal_id = highest_id
        state.save()


def _get_security_space(system_id):
    if not system_id:
        return "HIGHSEC"
    try:
        # Alliance Auth
        from allianceauth.eveonline.models import EveSolarSystem

        system = EveSolarSystem.objects.get(eve_id=system_id)
        sec = system.security_status
    except Exception:
        # Third Party
        import requests

        try:
            resp = requests.get(
                f"https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility",
                timeout=5,
            )
            if resp.status_code == 200:
                sec = resp.json().get("security_status", 1.0)
            else:
                return "HIGHSEC"
        except Exception:
            return "HIGHSEC"

    if sec >= 0.45:
        return "HIGHSEC"
    elif sec > 0.0:
        return "LOWSEC"
    else:
        return "NULLSEC_WH"


@shared_task
@log_task_execution("Update Industry Facilities")
def update_industry_facilities():
    """Fetch facility names from ESI to populate IndustryFacility cache."""
    # Third Party
    import requests

    # Alliance Auth
    from allianceauth.services.hooks import get_extension_logger
    from esi.models import Token as EveToken

    from .models import (
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


@shared_task
@log_task_execution("Sync Facility Rigs")
def sync_facility_rigs():
    """Fetch corporate assets and automatically determine installed rigs for facilities."""
    # Alliance Auth
    from allianceauth.services.hooks import get_extension_logger
    from esi.models import Token

    from .models import (
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
