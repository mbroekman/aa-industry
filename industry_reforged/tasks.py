"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task

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
)

logger = logging.getLogger(__name__)


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
                character_id=token.character_id, token=token, include_completed=True
            ).result()

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
                CharacterIndustryJob.objects.filter(character=character).exclude(
                    job_id__in=fetched_job_ids
                ).update(status="delivered")

        except HTTPNotModified:
            # 304 Not Modified, ignore
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch character jobs for {token.character_id}: {e}"
            )


@shared_task
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
            ).result()

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

                # Any jobs in our DB for this corp that are NOT in the fetched list
                # have aged out of ESI (meaning they are completed/delivered/cancelled > 90 days ago).
                fetched_job_ids = [getattr(j, "job_id") for j in jobs]
                CorporationIndustryJob.objects.filter(
                    corporation=config.corporation
                ).exclude(job_id__in=fetched_job_ids).update(status="delivered")
        except HTTPNotModified:
            # 304 Not Modified, ignore
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch jobs for corp {config.corporation.corporation_id}: {e}"
            )


@shared_task
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
                            "oceanic": 14,
                            "lava": 2014,
                            "barren": 2015,
                            "storm": 2016,
                            "plasma": 2017,
                        }
                        planet_type_id = PLANET_TYPE_MAP.get(planet_type_str, 2015)

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

                    # Clear old pins
                    char_planet.pins.all().delete()

                    pin_objects = []
                    for pin in pins:
                        pin_id = getattr(pin, "pin_id")
                        type_id = getattr(pin, "type_id")
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
                            try:
                                res = esi.client.Planetary_Interaction.GetUniverseSchematicsSchematicId(
                                    schematic_id=schematic_id
                                ).result()
                                # Third Party
                                from eveuniverse.models import EveType

                                t = EveType.objects.filter(
                                    name=res.schematic_name
                                ).first()
                                if t:
                                    product_type_id = t.id
                                    ensure_eve_type(product_type_id)
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

                        pin_objects.append(
                            PlanetPin(
                                planet=char_planet,
                                pin_id=pin_id,
                                type_id=type_id,
                                install_time=install_time,
                                expiry_time=expiry_time,
                                cycle_time=cycle_time,
                                extraction_yield=extraction_yield,
                                product_type_id=product_type_id,
                                schematic_id=schematic_id,
                                last_cycle_start=last_cycle_start,
                            )
                        )

                    PlanetPin.objects.bulk_create(pin_objects)

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
def task_sync_corp_inventory():
    """Fetch corporate assets from ESI for configured Hangars."""

    from .models import CorpHangarConfig, CorpInventory

    hangar_configs = CorpHangarConfig.objects.all()
    corps = {hc.corporation_id for hc in hangar_configs}

    for corp_id in corps:
        configs_for_corp = [hc for hc in hangar_configs if hc.corporation_id == corp_id]

        # We need a director token for this corp
        # Assuming CorporationSyncConfig is used for general sync character
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
            assets = esi.client.Assets.GetCorporationsCorporationIdAssets(
                corporation_id=sync_config.corporation.corporation_id, token=token
            ).result()

            # Filter assets matching location_id and flag_id
            filtered_assets = []
            for asset in assets:
                location_id = getattr(asset, "location_id")
                flag_id = getattr(asset, "location_flag")

                # Check if this asset is in a configured hangar
                if any(
                    hc.location_id == location_id and hc.flag_id == flag_id
                    for hc in configs_for_corp
                ):
                    type_id = getattr(asset, "type_id")
                    quantity = getattr(
                        asset, "quantity", 1
                    )  # single items don't always have quantity field
                    ensure_eve_type(type_id)
                    filtered_assets.append(
                        {
                            "type_id": type_id,
                            "quantity": quantity,
                            "location_id": location_id,
                            "flag_id": flag_id,
                        }
                    )

            # Update CorpInventory (only for items not manually overridden)
            if filtered_assets:
                # Group by type, location, flag
                # Standard Library
                from collections import defaultdict

                grouped = defaultdict(int)
                for fa in filtered_assets:
                    grouped[(fa["type_id"], fa["location_id"], fa["flag_id"])] += fa[
                        "quantity"
                    ]

                for (type_id, loc_id, flg_id), qty in grouped.items():
                    inv, created = CorpInventory.objects.get_or_create(
                        corporation_id=corp_id,
                        item_type_id=type_id,
                        location_id=loc_id,
                        flag_id=flg_id,
                        defaults={"quantity": qty},
                    )
                    if not inv.manual_override:
                        inv.quantity = qty
                        inv.save()

        except HTTPNotModified:
            # 304 Not Modified is expected, nothing changed.
            pass
        except Exception as e:
            logger.error(f"Failed to fetch assets for corp {corp_id}: {e}")


@shared_task
def task_pull_market_data():
    """Fetch Jita prices for PI, Moon, Gas, and Minerals via Fuzzwork."""
    logger.info("Market Data Pull initiated.")
    # Implementation requires querying the fuzzwork market API for the specific types
    # This is a placeholder for the actual API call logic
    pass


@shared_task
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


@shared_task
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
