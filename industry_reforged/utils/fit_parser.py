# Standard Library
import logging
import re

# Third Party
from eveuniverse.models import EveType

logger = logging.getLogger(__name__)


def parse_fit_text(text):
    """
    Parses an EFT/Pyfa fit string and returns a dictionary of {EveType: quantity}.
    Also returns a list of unrecognized item names.
    """
    items_counts = {}  # name -> quantity

    lines = text.strip().split("\n")
    if not lines:
        return {}, []

    # Check for [Hull, Fit Name]
    hull_match = re.match(r"\[([^,]+),\s*([^\]]+)\]", lines[0])
    if hull_match:
        hull = hull_match.group(1).strip()
        items_counts[hull] = items_counts.get(hull, 0) + 1

    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("["):
            continue

        # Check for 'x<quantity>' at the end
        qty_match = re.search(r"\s+x(\d+)$", line)
        qty = 1
        if qty_match:
            qty = int(qty_match.group(1))
            line = line[: qty_match.start()]

        # Check for charge: 'Module, Charge'
        if "," in line:
            parts = line.split(",")
            mod = parts[0].strip()
            charge = parts[1].strip()

            charge_qty_match = re.search(r"\s+x(\d+)$", charge)
            charge_qty = 1
            if charge_qty_match:
                charge_qty = int(charge_qty_match.group(1))
                charge = charge[: charge_qty_match.start()]

            items_counts[mod] = items_counts.get(mod, 0) + qty
            if charge:
                items_counts[charge] = items_counts.get(charge, 0) + (charge_qty * qty)
        else:
            items_counts[line] = items_counts.get(line, 0) + qty

    parsed_items = {}
    unrecognized = []

    names_to_resolve = list(items_counts.keys())
    if not names_to_resolve:
        return {}, []

    # Try resolving via ESI
    # Third Party
    import requests

    resolved_ids = {}
    try:
        res = requests.post(
            "https://esi.evetech.net/latest/universe/ids/",
            json=names_to_resolve,
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            if "inventory_types" in data:
                for item in data["inventory_types"]:
                    resolved_ids[item["name"]] = item["id"]
    except Exception as e:
        logger.error(f"Failed to resolve names via ESI: {e}")

    for name, qty in items_counts.items():
        try:
            # 1. Check if we already have it in DB
            eve_type = EveType.objects.filter(name=name).first()

            # 2. If not, and we got the ID from ESI, use get_or_create_esi with ID
            if not eve_type and name in resolved_ids:
                eve_type, _ = EveType.objects.get_or_create_esi(id=resolved_ids[name])

            if eve_type:
                parsed_items[eve_type] = parsed_items.get(eve_type, 0) + qty
            else:
                unrecognized.append(name)
        except Exception as e:
            logger.warning(f"Could not parse fit item {name}: {e}")
            unrecognized.append(name)

    return parsed_items, unrecognized
