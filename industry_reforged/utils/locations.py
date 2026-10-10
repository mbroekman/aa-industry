"""Location resolution helper utilities for Industry Reforged."""

# Standard Library
from typing import Dict, Iterable, Optional, Tuple


def format_location_flag(
    flag: str,
    division_names: Optional[Dict[str, str]] = None,
) -> str:
    """Format an EVE location_flag into human-readable text, using division name if available."""
    if not flag:
        return ""
    if division_names and flag in division_names:
        return division_names[flag]
    if flag.startswith("CorpSAG"):
        div_num = flag.replace("CorpSAG", "")
        return f"Hangar Division {div_num}"
    if flag == "CorpDeliveries":
        return "Corp Deliveries"
    if flag == "AutoFit":
        return "Deliveries"
    return flag


def get_corp_division_names() -> Dict[Optional[int], Dict[str, str]]:
    """
    Get mapping of corporation_id -> { 'CorpSAG1': 'Input-Output', ... }.
    Extracted from corptools EveLocation entries with negative IDs (managed hangars).
    Key `None` contains fallback division names across all corporations.
    """
    divisions_by_corp: Dict[Optional[int], Dict[str, str]] = {None: {}}
    try:
        from corptools.models import EveLocation

        for loc_id, loc_name, corp_id in (
            EveLocation.objects.filter(location_id__lt=0)
            .values_list(
                "location_id",
                "location_name",
                "managed_corp__corporation__corporation_id",
            )
        ):
            div_num = abs(loc_id) % 10
            flag = f"CorpSAG{div_num}"
            if " > " in loc_name:
                div_name = loc_name.split(" > ")[-1].strip()
                if div_name and not div_name.startswith("CorpSAG"):
                    if corp_id:
                        divisions_by_corp.setdefault(corp_id, {})[flag] = div_name
                    divisions_by_corp[None][flag] = div_name
    except (ImportError, Exception):
        pass

    return divisions_by_corp


def get_office_hangar_locations(
    structure_ids: Iterable[int],
) -> Dict[Tuple[int, str], str]:
    """
    Map (structure_id, flag) -> 'Structure > Hangar Division Name'.
    Uses corptools CorpAsset (OfficeFolder) and EveLocation.
    """
    hangar_map: Dict[Tuple[int, str], str] = {}
    ids = list(structure_ids)
    if not ids:
        return hangar_map

    try:
        from corptools.models import CorpAsset, EveLocation

        offices = list(
            CorpAsset.objects.filter(
                location_id__in=ids, location_flag="OfficeFolder"
            ).values_list("location_id", "item_id")
        )
        if not offices:
            return hangar_map

        hangar_id_to_key: Dict[int, Tuple[int, str]] = {}
        for struct_id, office_item_id in offices:
            for d in range(1, 8):
                h_id = -int(f"{office_item_id}{d}")
                hangar_id_to_key[h_id] = (struct_id, f"CorpSAG{d}")

        for loc_id, loc_name in EveLocation.objects.filter(
            location_id__in=hangar_id_to_key.keys()
        ).values_list("location_id", "location_name"):
            if loc_id in hangar_id_to_key:
                hangar_map[hangar_id_to_key[loc_id]] = loc_name
    except (ImportError, Exception):
        pass

    return hangar_map


def resolve_location_names(location_ids: Iterable[int]) -> Dict[int, str]:
    """
    Resolve a collection of location IDs into human-readable names.
    Combines IndustryFacility, KnownLocation, corptools (EveLocation, CorpAsset),
    EveStation, and EveSolarSystem.
    """
    ids = set(location_ids)
    names: Dict[int, str] = {}
    if not ids:
        return names

    # 1. IndustryFacility
    from ..models.facilities import IndustryFacility

    for fac_id, name in IndustryFacility.objects.filter(facility_id__in=ids).values_list(
        "facility_id", "name"
    ):
        if name:
            names[fac_id] = name

    # 2. KnownLocation
    from ..models.facilities import KnownLocation

    for loc_id, name in KnownLocation.objects.filter(location_id__in=ids).values_list(
        "location_id", "name"
    ):
        if name and not name.startswith("Unknown"):
            names[loc_id] = name

    # 3. CorpAsset (for container/office item_ids)
    try:
        from corptools.models import CorpAsset

        for itm_id, loc_name in (
            CorpAsset.objects.filter(item_id__in=ids)
            .select_related("location_name")
            .values_list("item_id", "location_name__location_name")
        ):
            if loc_name:
                names[itm_id] = loc_name
    except (ImportError, Exception):
        pass

    # 4. EveStation
    try:
        from eveuniverse.models import EveStation

        for st_id, name in EveStation.objects.filter(id__in=ids).values_list("id", "name"):
            if name:
                names[st_id] = name
    except (ImportError, Exception):
        pass

    # 5. EveSolarSystem
    try:
        from eveuniverse.models import EveSolarSystem

        for sys_id, name in EveSolarSystem.objects.filter(id__in=ids).values_list(
            "id", "name"
        ):
            if name:
                names[sys_id] = name
    except (ImportError, Exception):
        pass

    # 6. EveLocation (corptools) - HIGHEST PRECEDENCE
    # Provides the exact full hierarchy: "Structure > Hangar > Container"
    try:
        from corptools.models import EveLocation

        for loc_id, name in EveLocation.objects.filter(location_id__in=ids).values_list(
            "location_id", "location_name"
        ):
            if name:
                names[loc_id] = name
    except (ImportError, Exception):
        pass

    return names



def get_blueprint_asset_locations(item_ids: Iterable[int]) -> Dict[int, str]:
    """
    Map blueprint item_id -> full location path from corptools CorpAsset.
    Provides exact container hierarchy (e.g. Structure > Division > Container).
    """
    asset_locs: Dict[int, str] = {}
    ids = list(item_ids)
    if not ids:
        return asset_locs

    try:
        from corptools.models import CorpAsset

        for itm_id, loc_name in (
            CorpAsset.objects.filter(item_id__in=ids)
            .select_related("location_name")
            .values_list("item_id", "location_name__location_name")
        ):
            if loc_name:
                asset_locs[itm_id] = loc_name
    except (ImportError, Exception):
        pass

    return asset_locs


def get_blueprint_full_location(
    bp,
    location_names: Dict[int, str],
    office_hangars: Optional[Dict[Tuple[int, str], str]] = None,
    corp_divisions: Optional[Dict[Optional[int], Dict[str, str]]] = None,
    asset_locations: Optional[Dict[int, str]] = None,
) -> str:
    """Return the complete location path for a blueprint in 'Structure > Hangar > Container' format."""
    # 0. Check direct asset location (e.g. exact container from corptools CorpAsset)
    if asset_locations and bp.item_id in asset_locations:
        return asset_locations[bp.item_id]

    loc_name = location_names.get(bp.location_id, "")

    # 1. If loc_name already contains the full path hierarchy (e.g. from container EveLocation), return directly
    if loc_name and " > " in loc_name:
        return loc_name

    # 2. Check if (location_id, location_flag) maps directly to an office hangar EveLocation
    if office_hangars and (bp.location_id, bp.location_flag) in office_hangars:
        return office_hangars[(bp.location_id, bp.location_flag)]

    # 3. Determine division name
    corp_id = getattr(bp, "corporation_id", None)
    if corp_id is None and hasattr(bp, "corporation"):
        corp_id = getattr(bp.corporation, "corporation_id", None)

    div_names = {}
    if corp_divisions:
        div_names = corp_divisions.get(corp_id) or corp_divisions.get(None, {})

    flag_display = format_location_flag(bp.location_flag, division_names=div_names)

    # 4. Combine structure name + flag_display
    if loc_name:
        if not flag_display:
            return loc_name
        return f"{loc_name} > {flag_display}"

    if flag_display:
        return f"Structure ({bp.location_id}) > {flag_display}"
    return f"Structure ({bp.location_id})"


