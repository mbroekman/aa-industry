"""Diagnostic command: dump everything the plugin can learn about a given
structure/station ID.

Combines the basic ESI universe/structures (or universe/stations for NPC
stations) lookup, the richer per-corp structures endpoint when a usable
token exists for the owning corp (services, fuel expiry, reinforcement
state/timers), and whatever's already cached locally in IndustryFacility /
IndustryFacilityRig. Reuses the exact ESI token/endpoint patterns already
used by tasks/facilities.py.

Usage:
    python manage.py structure_info <structure_id>
"""

# Standard Library
import logging

import requests
from django.core.management.base import BaseCommand

from ...tasks.utils import _get_security_space

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Show all known data for a given Upwell structure or NPC station ID."

    def add_arguments(self, parser):
        parser.add_argument("structure_id", type=int)

    def handle(self, *args, **options):
        structure_id = options["structure_id"]

        if structure_id < 100_000_000:
            self._show_npc_station(structure_id)
        else:
            self._show_upwell_structure(structure_id)

        self._show_cached_facility(structure_id)

    # -- NPC stations (public, no auth needed) ---------------------------

    def _show_npc_station(self, station_id):
        self.stdout.write(self.style.MIGRATE_HEADING(f"NPC Station {station_id}"))
        resp = requests.get(
            f"https://esi.evetech.net/latest/universe/stations/{station_id}/"
            "?datasource=tranquility",
            timeout=10,
        )
        if resp.status_code != 200:
            self.stdout.write(
                self.style.WARNING(
                    f"  ESI returned {resp.status_code} for station {station_id}: "
                    f"{resp.text[:200]} - falling back to whatever was cached "
                    "locally, below."
                )
            )
            return

        data = resp.json()
        system_id = data.get("system_id")
        self.stdout.write(f"  Name:          {data.get('name')}")
        self.stdout.write(
            f"  Type:          {self._resolve_type_name(data.get('type_id'))}"
        )
        self.stdout.write(f"  Solar System:  {self._resolve_system(system_id)}")
        self.stdout.write(f"  Owner:         {self._resolve_name(data.get('owner'))}")
        self.stdout.write(f"  Race:          {data.get('race_id')}")
        self.stdout.write(f"  Max Dockable:  {data.get('max_dockable_ship_volume')} m3")
        self.stdout.write(f"  Reprocessing:  {data.get('reprocessing_efficiency')}")

    # -- Upwell structures (authenticated) --------------------------------

    def _show_upwell_structure(self, structure_id):
        # Alliance Auth
        from esi.models import Token as EveToken

        from ...models import CorporationSyncConfig

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Upwell Structure {structure_id}")
        )

        configs = list(
            CorporationSyncConfig.objects.select_related(
                "sync_character", "corporation"
            ).all()
        )
        if not configs:
            self.stdout.write(
                self.style.WARNING(
                    "  No CorporationSyncConfig rows exist - nothing to "
                    "authenticate with live. Falling back to whatever was "
                    "cached locally, below."
                )
            )
            return

        basic_data = None
        for config in configs:
            token = EveToken.objects.filter(
                character_id=config.sync_character.character_id,
                scopes__name="esi-universe.read_structures.v1",
            ).first()
            if not token:
                continue
            try:
                access_token = token.valid_access_token()
            except Exception as e:  # noqa: BLE001
                self.stdout.write(
                    self.style.WARNING(
                        f"  Token refresh failed for "
                        f"{config.sync_character.character_name}: {e}"
                    )
                )
                continue

            resp = requests.get(
                f"https://esi.evetech.net/latest/universe/structures/{structure_id}/"
                "?datasource=tranquility",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                basic_data = resp.json()
                break

        if basic_data is None:
            self.stdout.write(
                self.style.WARNING(
                    f"  Not accessible live with any of the {len(configs)} "
                    "configured sync character token(s) right now (the "
                    "structure may not exist, or none of those characters "
                    "can currently see/dock at it) - falling back to "
                    "whatever was cached locally from a previous sync, below."
                )
            )
            self._show_corp_structure_detail(structure_id, configs)
            return

        system_id = basic_data.get("solar_system_id")
        self.stdout.write(f"  Name:          {basic_data.get('name')}")
        self.stdout.write(
            f"  Type:          {self._resolve_type_name(basic_data.get('type_id'))}"
        )
        self.stdout.write(f"  Solar System:  {self._resolve_system(system_id)}")
        self.stdout.write(
            f"  Owner:         {self._resolve_name(basic_data.get('owner_id'))}"
        )
        position = basic_data.get("position") or {}
        if position:
            self.stdout.write(
                "  Position:      "
                f"x={position.get('x')}, y={position.get('y')}, z={position.get('z')}"
            )

        self._show_corp_structure_detail(structure_id, configs)

    def _show_corp_structure_detail(self, structure_id, configs):
        """Richer detail from GET /corporations/{id}/structures/ (services, fuel,
        reinforcement timers) - only visible to characters with director roles in
        the owning corp."""
        # Alliance Auth
        from esi.models import Token as EveToken

        from ...tasks.utils import esi

        for config in configs:
            token = EveToken.objects.filter(
                character_id=config.sync_character.character_id,
                scopes__name="esi-corporations.read_structures.v1",
            ).first()
            if not token:
                continue
            try:
                structures = (
                    esi.client.Corporation.GetCorporationsCorporationIdStructures(
                        corporation_id=config.corporation.corporation_id,
                        token=token,
                    ).results()
                )
            except Exception as e:  # noqa: BLE001
                self.stdout.write(
                    self.style.WARNING(
                        f"  Could not list structures for "
                        f"{config.corporation.corporation_name}: {e}"
                    )
                )
                continue

            match = next(
                (
                    s
                    for s in structures
                    if getattr(s, "structure_id", None) == structure_id
                ),
                None,
            )
            if not match:
                continue

            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"  Corp detail (via {config.corporation.corporation_name})"
                )
            )
            self.stdout.write(
                f"    Solar System:    "
                f"{self._resolve_system(getattr(match, 'system_id', None))}"
            )
            self.stdout.write(
                f"    Type:            "
                f"{self._resolve_type_name(getattr(match, 'type_id', None))}"
            )
            self.stdout.write(f"    State:           {getattr(match, 'state', '-')}")
            self.stdout.write(
                f"    Fuel Expires:    {getattr(match, 'fuel_expires', '-')}"
            )
            self.stdout.write(
                f"    Reinforce Hour:  {getattr(match, 'reinforce_hour', '-')}"
            )
            self.stdout.write(
                f"    State Timer:     "
                f"{getattr(match, 'state_timer_start', '-')} -> "
                f"{getattr(match, 'state_timer_end', '-')}"
            )
            self.stdout.write(
                f"    Unanchors At:    {getattr(match, 'unanchors_at', '-')}"
            )
            services = getattr(match, "services", None) or []
            if services:
                self.stdout.write("    Services:")
                for svc in services:
                    self.stdout.write(
                        f"      - {getattr(svc, 'name', '?')}: "
                        f"{getattr(svc, 'state', '?')}"
                    )
            return  # found it, no need to check other corps

    # -- Locally cached data ----------------------------------------------

    def _show_cached_facility(self, facility_id):
        # AA Industry App
        from ...models import IndustryFacility

        facility = IndustryFacility.objects.filter(facility_id=facility_id).first()
        if not facility:
            self.stdout.write(
                self.style.WARNING(
                    "\nNo locally cached IndustryFacility row for this ID."
                )
            )
            return

        self.stdout.write(
            self.style.MIGRATE_HEADING("\nLocally Cached IndustryFacility")
        )
        self.stdout.write(f"  Name:                  {facility.name}")
        self.stdout.write(
            f"  Solar System:          {self._resolve_system(facility.solar_system_id)}"
        )
        self.stdout.write(
            f"  Type:                  {self._resolve_type_name(facility.type_id)}"
        )
        self.stdout.write(
            f"  Owner:                 {self._resolve_name(facility.owner_id)}"
        )
        self.stdout.write(f"  Security Space:        {facility.security_space}")
        self.stdout.write(f"  Production Facility:   {facility.is_production_facility}")
        self.stdout.write(f"  Default Facility:      {facility.is_default}")
        self.stdout.write(f"  Sync Inventory:        {facility.sync_inventory}")
        self.stdout.write(f"  Last Updated:          {facility.last_updated}")

        rigs = list(facility.rigs.select_related("rig").all())
        if rigs:
            self.stdout.write("  Installed Rigs:")
            for fr in rigs:
                self.stdout.write(
                    f"    - {fr.rig.name} (ME +{fr.rig.me_bonus}%, "
                    f"TE +{fr.rig.te_bonus}%)"
                )
        else:
            self.stdout.write("  Installed Rigs:        none recorded")

    # -- Name resolution helpers --------------------------------------------

    def _resolve_type_name(self, type_id):
        if not type_id:
            return "-"
        try:
            # Third Party
            from eveuniverse.models import EveType

            eve_type, _ = EveType.objects.get_or_create_esi(id=type_id)
            return f"{eve_type.name} ({type_id})"
        except Exception:  # noqa: BLE001
            return f"Unknown ({type_id})"

    def _resolve_system(self, system_id):
        if not system_id:
            return "-"
        security_space = _get_security_space(system_id)
        try:
            # Alliance Auth
            from allianceauth.eveonline.models import EveSolarSystem

            system = EveSolarSystem.objects.get(eve_id=system_id)
            return f"{system.name} ({system_id}, {security_space})"
        except Exception:  # noqa: BLE001
            logger.debug(
                "No local EveSolarSystem for %s, falling back to ESI", system_id
            )
        name = self._resolve_bare_name(entity_id=system_id)
        return f"{name} ({system_id}, {security_space})"

    def _resolve_name(self, entity_id):
        if not entity_id:
            return "-"
        return f"{self._resolve_bare_name(entity_id)} ({entity_id})"

    def _resolve_bare_name(self, entity_id):
        """Just the name, no '(id)' suffix - callers that already build their own
        '(id, ...)' tail use this to avoid duplicating the ID."""
        if not entity_id:
            return "Unknown"
        try:
            resp = requests.post(
                "https://esi.evetech.net/latest/universe/names/?datasource=tranquility",
                json=[entity_id],
                timeout=10,
            )
            if resp.status_code == 200 and resp.json():
                return resp.json()[0].get("name") or "Unknown"
        except Exception:  # noqa: BLE001
            logger.debug("Failed to resolve name for %s via ESI", entity_id)
        return "Unknown"
