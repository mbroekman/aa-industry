"""App Tasks"""

# Standard Library
import logging
import time
import traceback
from functools import wraps

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
