"""App Tasks"""

# Standard Library
import logging
import time
import traceback
from functools import wraps

# Third Party
from celery import shared_task

# Django
from django.utils import timezone

# Alliance Auth
from allianceauth import __title_useragent__, __url__, __version__
from allianceauth.eveonline import __esi_compatibility_date__
from esi.openapi_clients import ESIClientProvider

from ..models import (
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
                "GetCorporationsCorporationIdStructures",
                "GetCorporationsCorporationIdDivisions",
                "GetCorporationsCorporationIdBlueprints",
            ],
        )


esi = IndustryESIProvider()


def notify_discord_user(character, message):
    try:
        user = character.character_ownership.user
        try:
            # Third Party
            from aadiscordbot.tasks import send_direct_message_by_user_id

            send_direct_message_by_user_id.delay(user.id, message)
            return
        except ImportError:
            pass  # Fallback to standard AA discord module

        # Alliance Auth standard fallback
        # Alliance Auth
        from allianceauth.services.modules.discord.discord_client import DiscordClient
        from allianceauth.services.modules.discord.models import DiscordUser

        discord_user = DiscordUser.objects.get(user=user)
        client = DiscordClient()
        dm_channel = client.create_dm(discord_user.uid)
        if dm_channel and "id" in dm_channel:
            client.create_message(channel_id=dm_channel["id"], content=message)
    except Exception as e:
        logger.error(f"Failed to send discord DM to {character.character_name}: {e}")


def send_pi_notification(character, title, message):
    try:
        user = character.character_ownership.user

        # 1. Send Alliance Auth Notification
        # Alliance Auth
        from allianceauth.notifications.models import Notification

        Notification.objects.notify_user(
            user=user, title=title, message=message, level="warning"
        )

        # 2. Send Discord DM
        notify_discord_user(character, message)

    except Exception as e:
        logger.error(
            f"Failed to send PI notification to {character.character_name}: {e}"
        )


def ensure_eve_type(type_id):
    if type_id:
        try:
            # Third Party
            from eveuniverse.models import EveType

            EveType.objects.get_or_create_esi(id=type_id)
        except Exception as e:
            logger.warning(f"Could not fetch EveType {type_id}: {e}")


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


# Third Party


@shared_task(name="industry_reforged.tasks.resolve_unknown_locations")
def resolve_unknown_locations(location_ids=None):
    """Resolve names for unknown locations via ESI."""
    # Django
    from django.db.models import Q

    # Third Party
    import requests

    # Alliance Auth
    from esi.models import Token

    from ..models.facilities import KnownLocation

    if location_ids is None:
        location_ids = list(
            KnownLocation.objects.filter(
                Q(name="") | Q(name__startswith="Unknown")
            ).values_list("location_id", flat=True)[:1000]
        )

    if not location_ids:
        return

    token = Token.objects.filter(scopes__name="esi-universe.read_structures.v1").first()

    # Filter to only IDs that actually need resolution
    needs_resolution = []
    loc_objects = {}

    for loc_id in location_ids:
        loc, created = KnownLocation.objects.get_or_create(location_id=loc_id)
        if created or loc.name == "" or loc.name.startswith("Unknown"):
            needs_resolution.append(loc_id)
            loc_objects[loc_id] = loc

    if not needs_resolution:
        return

    # Step 1: Bulk resolve using /universe/names/ (handles solar systems, stations, etc)
    unresolved_ids = set(needs_resolution)

    # ESI /universe/names/ endpoint only accepts int32. Large structure IDs will cause a 400 error for the whole chunk.
    int32_max = 2147483647
    public_ids = [i for i in needs_resolution if i <= int32_max]

    try:
        if public_ids:
            # Split into chunks of 1000 (ESI limit)
            for i in range(0, len(public_ids), 1000):
                chunk = public_ids[i : i + 1000]
                resp = requests.post(
                    "https://esi.evetech.net/latest/universe/names/?datasource=tranquility",
                    json=chunk,
                    timeout=10,
                )
                if resp.status_code == 200:
                    results = resp.json()
                    for res in results:
                        loc_id = res.get("id")
                        if loc_id in loc_objects:
                            loc = loc_objects[loc_id]
                            loc.name = res.get("name")
                            loc.save()
                            unresolved_ids.discard(loc_id)
                else:
                    logger.error(
                        f"ESI names endpoint failed with {resp.status_code}: {resp.text}"
                    )
    except Exception as e:
        logger.error(f"Error bulk resolving names: {e}")

    # Step 2: Fallback to /universe/structures/ for player structures
    if token and unresolved_ids:
        headers = {"Authorization": f"Bearer {token.valid_access_token()}"}
        for loc_id in list(unresolved_ids):
            # Check if it even falls in the structure ID range to save useless API calls
            if loc_id > 1000000000000:
                try:
                    resp = requests.get(
                        f"https://esi.evetech.net/latest/universe/structures/{loc_id}/?datasource=tranquility",
                        headers=headers,
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        loc = loc_objects[loc_id]
                        loc.name = resp.json().get("name")
                        loc.save()
                        unresolved_ids.discard(loc_id)
                except Exception as e:
                    logger.error(f"Failed to fetch structure name for {loc_id}: {e}")

    # Step 3: Set fallback names for anything that couldn't be resolved
    for loc_id in unresolved_ids:
        loc = loc_objects[loc_id]
        if loc.name == "" or loc.name.startswith("Unknown"):
            loc.name = f"Unknown Location ({loc_id})"
            loc.save()
