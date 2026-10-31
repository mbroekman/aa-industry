"""Where corp stock lies, per structure, and what to haul to the build facility.

Materials tables show one "Corp Stock" total over every location. A builder needs
to know how much already sits in the structure they build in, and where the rest
is, so they know what to pick up before a job can start.

Inventory rows are stored per root location (the structure; see TASK-283), so the
location_id here is the structure ID that IndustryFacility.facility_id also uses.
"""

# Standard Library
from collections import defaultdict

BLUEPRINT_CATEGORY_ID = 9
MAX_LISTED_LOCATIONS = 4


def location_names(location_ids) -> dict:
    """Readable names: configured facility first, then known asset location."""
    # AA Industry App
    from industry_reforged.models import IndustryFacility, KnownLocation

    ids = set(location_ids)
    names = dict(
        IndustryFacility.objects.filter(facility_id__in=ids).values_list(
            "facility_id", "name"
        )
    )
    missing = ids - set(names)
    if missing:
        names.update(
            KnownLocation.objects.filter(location_id__in=missing).values_list(
                "location_id", "name"
            )
        )
    return {i: names.get(i) or f"Location {i}" for i in ids}


def stock_by_location(corp_info, type_ids) -> dict:
    """{type_id: [{"location_id", "name", "quantity"}, ...]} largest first."""
    # AA Industry App
    from industry_reforged.models import CorpInventory

    if not corp_info or not type_ids:
        return {}
    rows = CorpInventory.objects.filter(
        corporation=corp_info, item_type_id__in=type_ids, quantity__gt=0
    ).values_list("item_type_id", "location_id", "quantity")

    per_type = defaultdict(lambda: defaultdict(int))
    for type_id, location_id, qty in rows:
        per_type[type_id][location_id] += qty
    names = location_names({loc for locs in per_type.values() for loc in locs})

    result = {}
    for type_id, locs in per_type.items():
        result[type_id] = sorted(
            (
                {"location_id": loc, "name": names[loc], "quantity": qty}
                for loc, qty in locs.items()
            ),
            key=lambda e: -e["quantity"],
        )
    return result


def _blueprint_type_ids(type_ids) -> set:
    # Third Party
    from eveuniverse.models import EveType

    return set(
        EveType.objects.filter(
            id__in=type_ids, eve_group__eve_category_id=BLUEPRINT_CATEGORY_ID
        ).values_list("id", flat=True)
    )


def annotate_stock_locations(materials, corp_info, facility_id=None) -> None:
    """Add per-structure stock to each material dict (needs "type_id" and "quantity").

    Sets on every material:
    - stock_locations: [{"location_id", "name", "quantity", "is_facility"}]
    - stock_at_facility: quantity in the build structure (None when no facility)
    - stock_elsewhere: quantity in all other structures
    - to_haul: how much of the requirement must be brought to the build structure
    Blueprints are skipped: their stock is counted in BPC runs, not items.
    """
    materials = list(materials)
    for mat in materials:
        mat["stock_locations"] = []
        mat["stock_at_facility"] = 0 if facility_id else None
        mat["stock_elsewhere"] = 0
        mat["to_haul"] = 0
    type_ids = {m["type_id"] for m in materials if m.get("type_id")}
    if not type_ids or not corp_info:
        return
    type_ids -= _blueprint_type_ids(type_ids)
    stock = stock_by_location(corp_info, type_ids)

    for mat in materials:
        locs = stock.get(mat.get("type_id"), [])
        at_facility = 0
        listed = []
        for loc in locs:
            is_facility = facility_id is not None and loc["location_id"] == facility_id
            if is_facility:
                at_facility = loc["quantity"]
            listed.append({**loc, "is_facility": is_facility})
        # Build structure first, then the largest piles.
        listed.sort(key=lambda e: (not e["is_facility"], -e["quantity"]))
        elsewhere = sum(e["quantity"] for e in listed if not e["is_facility"])
        mat["stock_locations"] = listed
        mat["stock_locations_shown"] = listed[:MAX_LISTED_LOCATIONS]
        mat["stock_locations_hidden"] = listed[MAX_LISTED_LOCATIONS:]
        mat["stock_elsewhere"] = elsewhere
        if facility_id is not None:
            mat["stock_at_facility"] = at_facility
            need = max(0, int(mat.get("quantity", 0) or 0) - at_facility)
            mat["to_haul"] = min(need, elsewhere)


def build_haul_list(materials) -> list:
    """Group what to bring to the build structure by source structure.

    Takes from the largest piles first, so a pick-up needs as few stops as possible.
    Returns [{"location_id", "name", "items": [{"type_id", "name", "quantity"}],
    "item_count"}] with the busiest stop first. Expects annotate_stock_locations().
    """
    stops = {}
    for mat in materials:
        remaining = mat.get("to_haul") or 0
        if remaining <= 0:
            continue
        for loc in mat.get("stock_locations", []):
            if loc["is_facility"] or remaining <= 0:
                continue
            take = min(remaining, loc["quantity"])
            remaining -= take
            stop = stops.setdefault(
                loc["location_id"],
                {"location_id": loc["location_id"], "name": loc["name"], "items": []},
            )
            stop["items"].append(
                {"type_id": mat["type_id"], "name": mat.get("name"), "quantity": take}
            )
    result = list(stops.values())
    for stop in result:
        stop["items"].sort(key=lambda i: i["name"] or "")
        stop["item_count"] = len(stop["items"])
    result.sort(key=lambda s: (-s["item_count"], s["name"]))
    return result


def single_facility(orders) -> object:
    """The one target facility all given orders share, else None."""
    facilities = {o.target_facility_id for o in orders if o is not None}
    if len(facilities) == 1:
        facility_id = facilities.pop()
        if facility_id:
            # AA Industry App
            from industry_reforged.models import IndustryFacility

            return IndustryFacility.objects.filter(facility_id=facility_id).first()
    return None
