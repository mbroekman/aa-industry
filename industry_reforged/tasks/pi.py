"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task
from eveuniverse.models import EveType

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

from ..models import (
    CharacterPlanet,
    PlanetPin,
)
from .utils import ensure_eve_type, esi, log_task_execution, send_pi_notification

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.update_character_pi")
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

                        # Third Party
                        from eveuniverse.models import EvePlanet, EveSolarSystem

                        eve_system, _ = EveSolarSystem.objects.get_or_create_esi(
                            id=system_id
                        )
                        eve_planet, _ = EvePlanet.objects.get_or_create_esi(
                            id=planet_id
                        )

                        CharacterPlanet.objects.update_or_create(
                            character=character,
                            planet_id=planet_id,
                            defaults={
                                "system_id": system_id,
                                "planet_type_id": planet_type_id,
                                "upgrade_level": upgrade_level,
                                "num_pins": num_pins,
                                "eve_system": eve_system,
                                "eve_planet": eve_planet,
                            },
                        )
            except HTTPNotModified:
                # Planet list hasn't changed, but we still must check pins
                pass

            # Now fetch pins for all known planets for this character
            char_planets = CharacterPlanet.objects.filter(character=character)
            for char_planet in char_planets:
                if not char_planet.eve_planet_id or not char_planet.eve_system_id:
                    # Third Party
                    from eveuniverse.models import EvePlanet, EveSolarSystem

                    eve_planet, _ = EvePlanet.objects.get_or_create_esi(
                        id=char_planet.planet_id
                    )
                    eve_system, _ = EveSolarSystem.objects.get_or_create_esi(
                        id=char_planet.system_id
                    )
                    char_planet.eve_planet = eve_planet
                    char_planet.eve_system = eve_system
                    char_planet.save(update_fields=["eve_planet", "eve_system"])
                elif char_planet.eve_planet and not char_planet.eve_planet.name:
                    # Third Party
                    from eveuniverse.models import EvePlanet

                    EvePlanet.objects.update_or_create_esi(id=char_planet.planet_id)

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

                        planet_label = (
                            f"{char_planet.eve_system.name} » {char_planet.eve_planet.name}"
                            if char_planet.eve_planet and char_planet.eve_system
                            else (
                                char_planet.planet_type.name
                                if char_planet.planet_type
                                else f"Planeet {char_planet.planet_id}"
                            )
                        )

                        # Notification Logic for Extractor Expiry
                        if pin_obj.is_extractor and pin_obj.expiry_time:
                            if now >= pin_obj.expiry_time:
                                if not pin_obj.notification_sent:
                                    message = f"Je extractor op je **{planet_label}** is zojuist gestopt. Tijd om deze opnieuw aan te zetten!"
                                    send_pi_notification(
                                        character, "PI Extractor Expired", message
                                    )
                                    pin_obj.notification_sent = True
                                    pin_obj.save()
                            else:
                                # Extractor has future expiry, meaning it was restarted
                                if pin_obj.notification_sent:
                                    pin_obj.notification_sent = False
                                    pin_obj.save()

                        # Notification Logic for Full Storage
                        elif pin_obj.is_storage:
                            threshold = 75
                            try:
                                if hasattr(
                                    character.character_ownership.user,
                                    "industry_pi_config",
                                ):
                                    threshold = (
                                        character.character_ownership.user.industry_pi_config.storage_warning_threshold
                                    )
                            except Exception:
                                pass

                            if pin_obj.utilization_pct >= threshold:
                                if not pin_obj.notification_sent:
                                    message = f"De opslag (of launchpad) op je **{planet_label}** is (bijna) vol! Tijd om spullen op te halen."
                                    send_pi_notification(
                                        character, "PI Storage Full", message
                                    )
                                    pin_obj.notification_sent = True
                                    pin_obj.save()
                            else:
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


@shared_task(name="industry_reforged.tasks.task_notify_expired_extractors")
@log_task_execution("Task Notify Expired Extractors")
def task_notify_expired_extractors():
    """Check for expired PI extractors and send notifications via Alliance Auth notify."""
    # Deprecated: Notification logic has been moved into the main update_pi_planets task
    # to guarantee atomicity and combine Auth and Discord notifications reliably.
    pass


@shared_task(name="industry_reforged.tasks.update_pi_schematics_from_sde")
@log_task_execution("Update PI Schematics from SDE")
def update_pi_schematics_from_sde():
    """Fetch PI schematics from SDE mirrors and update local database."""
    # Third Party
    import requests

    from ..models.pi import PISchematic, PISchematicInput, PISchematicOutput

    try:
        r1 = requests.get("https://sde.zzeve.com/planetSchematics.json", timeout=15)
        r1.raise_for_status()
        schematics = r1.json()

        r2 = requests.get(
            "https://sde.zzeve.com/planetSchematicsTypeMap.json", timeout=15
        )
        r2.raise_for_status()
        typemap = r2.json()

        for sch in schematics:
            PISchematic.objects.update_or_create(
                schematic_id=sch["schematicID"],
                defaults={
                    "name": sch["schematicName"],
                    "cycle_time": sch["cycleTime"],
                },
            )

        for tm in typemap:
            sid = tm["schematicID"]
            tid = tm["typeID"]
            qty = tm["quantity"]
            is_in = tm["isInput"]

            ensure_eve_type(tid)
            # Third Party
            from eveuniverse.models import EveType

            eve_type = EveType.objects.filter(id=tid).first()
            if not eve_type:
                continue

            sch = PISchematic.objects.filter(schematic_id=sid).first()
            if not sch:
                continue

            if is_in == 1 or is_in == True:
                PISchematicInput.objects.update_or_create(
                    schematic=sch, type=eve_type, defaults={"quantity": qty}
                )
            else:
                PISchematicOutput.objects.update_or_create(
                    schematic=sch, type=eve_type, defaults={"quantity": qty}
                )

        logger.info("Successfully updated PI schematics from SDE.")
    except Exception as e:
        logger.error(f"Failed to update PI schematics from SDE: {e}")
