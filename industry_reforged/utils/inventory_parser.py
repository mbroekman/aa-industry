# Standard Library
import logging
import re

# Third Party
from eveuniverse.models import EveType

logger = logging.getLogger(__name__)

_THOUSANDS_SEP_RE = re.compile(r"^[\d.,]+$")


def _parse_quantity(raw: str) -> int | None:
    """Parse a quantity column that may use ',' or '.' as a thousands separator
    (e.g. "1,234" or "1.234"), or be a plain integer. Returns None if not numeric."""
    raw = raw.strip()
    if not raw or not _THOUSANDS_SEP_RE.match(raw):
        return None
    # A single separator followed by exactly 3 digits at the end is a thousands
    # separator, not a decimal point - EVE inventory quantities are always whole
    # numbers, so just strip every '.'/',' and parse as int.
    digits = raw.replace(",", "").replace(".", "")
    if not digits.isdigit():
        return None
    return int(digits)


def parse_inventory_paste(text: str, with_unpacked: bool = False):
    """
    Parses an EVE client "Copy as List" inventory export and returns a
    dict of {EveType: quantity} plus a list of unrecognized item names.

    The paste is tab-delimited with a variable column count depending on the
    client window (commonly Name/Quantity/Group/Category/Size/Volume, or a
    plain Name/Quantity from some windows). Only column 0 (name) and column 1
    (quantity, if present and numeric) are used; the rest are ignored.

    The client leaves the quantity empty for assembled (unpacked) items. With
    `with_unpacked=True` a third value is returned: the ids of the types that
    appeared on such a line.
    """
    items_counts: dict[str, int] = {}
    unpacked_names: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip().rstrip("\r")
        if not line:
            continue

        columns = line.split("\t")
        name = columns[0].strip()
        if name.endswith("*"):
            name = name[:-1].strip()
        if not name:
            continue

        qty = None
        if len(columns) > 1:
            qty = _parse_quantity(columns[1])
        if qty is None:
            qty = 1
            unpacked_names.add(name)

        items_counts[name] = items_counts.get(name, 0) + qty

    parsed_items: dict[EveType, int] = {}
    unrecognized: list[str] = []
    unpacked_type_ids: set[int] = set()

    for name, qty in items_counts.items():
        eve_type = (
            EveType.objects.filter(name__iexact=name)
            .select_related("eve_group")
            .first()
        )
        if eve_type:
            parsed_items[eve_type] = parsed_items.get(eve_type, 0) + qty
            if name in unpacked_names:
                unpacked_type_ids.add(eve_type.id)
        else:
            unrecognized.append(name)

    if with_unpacked:
        return parsed_items, unrecognized, unpacked_type_ids
    return parsed_items, unrecognized
