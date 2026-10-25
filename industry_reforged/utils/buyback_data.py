"""EVE reference data the buyback valuation needs, loaded per item on demand.

The SDE sections behind ore refining, T1 scrap and market-group rules (type
materials, dogma, market groups) aren't part of a default eveuniverse install.
Instead of a large up-front import, the calculator asks for exactly the pasted
items it needs and eveuniverse stores what it fetched. A failed fetch is
remembered for a day so a broken item can't slow every appraisal down.
"""

# Standard Library
import logging

# Third Party
from eveuniverse.models import EveMarketPrice, EveType, EveTypeDogmaAttribute

# Django
from django.core.cache import cache

logger = logging.getLogger(__name__)

ASTEROID_CATEGORY_ID = 25  # ore, ice and moon ore, raw and compressed
BLUEPRINT_CATEGORY_ID = 9
T1_SCRAP_CATEGORY_IDS = {6, 7, 8, 18, 32}  # ship, module, charge, drone, subsystem
META_LEVEL_ATTRIBUTE_ID = 633
MAX_T1_META_LEVEL = 4

SLEEPER_COMPONENT_TYPE_IDS = {30744, 30745, 30746, 30747}
TRIGLAVIAN_SURVEY_DATABASE_TYPE_IDS = {48121, 60459, 91773}
OVERSEERS_PERSONAL_EFFECTS_GROUP_ID = 493
SCC_ENCRYPTED_BONDS_GROUP_ID = 1248

_FAILED_FETCH_TTL = 24 * 3600


def category_id(eve_type) -> int | None:
    return eve_type.eve_group.eve_category_id if eve_type.eve_group_id else None


def is_ore(eve_type) -> bool:
    return category_id(eve_type) == ASTEROID_CATEGORY_ID


def is_blueprint(eve_type) -> bool:
    return category_id(eve_type) == BLUEPRINT_CATEGORY_ID


def is_t1_scrap_candidate(eve_type) -> bool:
    """Item kinds that can be valued as scrap; meta level is checked separately."""
    return category_id(eve_type) in T1_SCRAP_CATEGORY_IDS


def ensure_sections(eve_types, section: str) -> dict:
    """Make sure each type has `section` (an EveType.Section value) loaded.

    Returns {type_id: EveType}, re-read from the database for the types that
    were fetched, so callers see the new data.
    """
    by_id = {t.id: t for t in eve_types}
    fetched = []
    for eve_type in eve_types:
        if getattr(eve_type.enabled_sections, section):
            continue
        cache_key = f"industry_reforged_buyback_section_{section}_{eve_type.id}"
        if cache.get(cache_key):
            continue
        try:
            EveType.objects.update_or_create_esi(
                id=eve_type.id, enabled_sections=[section]
            )
            fetched.append(eve_type.id)
        except Exception as e:
            logger.warning(f"Could not load {section} for type {eve_type.id}: {e}")
            cache.set(cache_key, 1, timeout=_FAILED_FETCH_TTL)
    if fetched:
        for eve_type in EveType.objects.filter(id__in=fetched).select_related(
            "eve_group", "eve_market_group"
        ):
            by_id[eve_type.id] = eve_type
    return by_id


def meta_level(eve_type) -> int | None:
    """Meta level from dogma, or None when it isn't known."""
    value = (
        EveTypeDogmaAttribute.objects.filter(
            eve_type=eve_type, eve_dogma_attribute_id=META_LEVEL_ATTRIBUTE_ID
        )
        .values_list("value", flat=True)
        .first()
    )
    return int(value) if value is not None else None


def is_t1(eve_type) -> bool:
    """Meta level 0-4. An item whose meta level can't be determined is not
    treated as T1, so a missing dogma load never turns faction gear into scrap."""
    level = meta_level(eve_type)
    return level is not None and level <= MAX_T1_META_LEVEL


def market_group_ancestry(eve_type) -> list[int]:
    """The item's market group and every group above it, nearest first."""
    ids = []
    group = eve_type.eve_market_group
    seen = set()
    while group is not None and group.id not in seen:
        seen.add(group.id)
        ids.append(group.id)
        group = group.parent_market_group
    return ids


def npc_price_applies(program, eve_type) -> bool:
    group_id = eve_type.eve_group_id
    return (
        (program.npc_price_blue_loot and eve_type.id in SLEEPER_COMPONENT_TYPE_IDS)
        or (
            program.npc_price_red_loot
            and eve_type.id in TRIGLAVIAN_SURVEY_DATABASE_TYPE_IDS
        )
        or (program.npc_price_ope and group_id == OVERSEERS_PERSONAL_EFFECTS_GROUP_ID)
        or (program.npc_price_bonds and group_id == SCC_ENCRYPTED_BONDS_GROUP_ID)
    )


def npc_price(eve_type) -> float | None:
    """CCP's average price for the item, as the original plugin's "NPC price"."""
    value = (
        EveMarketPrice.objects.filter(eve_type=eve_type)
        .values_list("average_price", flat=True)
        .first()
    )
    return value if value else None


def compressed_variant(eve_type):
    """The "Compressed <name>" type for an ore, or None."""
    if eve_type.name.startswith("Compressed "):
        return None
    return (
        EveType.objects.filter(name=f"Compressed {eve_type.name}", published=True)
        .select_related("eve_group")
        .first()
    )
