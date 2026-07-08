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
        lines_to_parse = lines[1:]
    else:
        lines_to_parse = lines

    for line in lines_to_parse:
        line = line.strip()
        if not line or line.startswith("["):
            continue

        # Check for charge: 'Module, Charge'
        if "," in line:
            parts = line.split(",")
            mod = parts[0].strip()
            charge = parts[1].strip()

            mod_qty = 1
            m_qty_match = re.search(r"\s+x(\d+)$", mod, re.IGNORECASE)
            if m_qty_match:
                mod_qty = int(m_qty_match.group(1))
                mod = mod[: m_qty_match.start()].strip()

            charge_qty = 1
            c_qty_match = re.search(r"\s+x(\d+)$", charge, re.IGNORECASE)
            if c_qty_match:
                charge_qty = int(c_qty_match.group(1))
                charge = charge[: c_qty_match.start()].strip()

            items_counts[mod] = items_counts.get(mod, 0) + mod_qty
            if charge:
                items_counts[charge] = items_counts.get(charge, 0) + (
                    charge_qty * mod_qty
                )
            continue

        # Try '<quantity> <item>' (e.g. 20 Drake, 20x Drake, 20 x Drake)
        prefix_match = re.match(r"^(\d+)\s*x?\s+(.+)$", line, re.IGNORECASE)
        # Try '<item> <quantity>' (e.g. Drake 20, Drake x20, Drake x 20, Drake\t20)
        suffix_match = re.search(r"^(.*?)\s+x?\s*(\d+)$", line, re.IGNORECASE)

        if prefix_match:
            qty = int(prefix_match.group(1))
            name = prefix_match.group(2).strip()
        elif suffix_match:
            name = suffix_match.group(1).strip()
            qty = int(suffix_match.group(2))
        else:
            name = line
            qty = 1

        items_counts[name] = items_counts.get(name, 0) + qty

    parsed_items = {}
    unrecognized = []

    names_to_resolve = list(items_counts.keys())
    if not names_to_resolve:
        return {}, []

    # Try resolving via ESI
    # Third Party
    import requests

    resolved_ids = {}  # lowercase true name -> id
    search_names = []

    for name in names_to_resolve:
        search_names.append(name)
        if name.lower().endswith("ies"):
            search_names.append(name[:-3] + "y")
        elif name.lower().endswith("s"):
            search_names.append(name[:-1])

    try:
        res = requests.post(
            "https://esi.evetech.net/latest/universe/ids/",
            json=list(set(search_names)),
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            if "inventory_types" in data:
                for item in data["inventory_types"]:
                    resolved_ids[item["name"].lower()] = item["id"]
    except Exception as e:
        logger.error(f"Failed to resolve names via ESI: {e}")

    for original_name, qty in items_counts.items():
        try:
            eve_type = None

            def try_resolve(test_name):
                et = EveType.objects.filter(name__iexact=test_name).first()
                if et:
                    return et
                test_lower = test_name.lower()
                if test_lower in resolved_ids:
                    et, _ = EveType.objects.get_or_create_esi(
                        id=resolved_ids[test_lower]
                    )
                    return et
                return None

            # 1. Try original name
            eve_type = try_resolve(original_name)

            # 2. Try singular
            if not eve_type:
                if original_name.lower().endswith("ies"):
                    eve_type = try_resolve(original_name[:-3] + "y")
                elif original_name.lower().endswith("s"):
                    eve_type = try_resolve(original_name[:-1])

            if eve_type:
                parsed_items[eve_type] = parsed_items.get(eve_type, 0) + qty
            else:
                unrecognized.append(original_name)
        except Exception as e:
            logger.warning(f"Could not parse fit item {original_name}: {e}")
            unrecognized.append(original_name)

    return parsed_items, unrecognized
