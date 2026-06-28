# Standard Library
import logging
import math

# Third Party
import requests

# Django
from django.core.cache import cache

logger = logging.getLogger(__name__)

FUZZWORK_BOM_API = "https://fuzzwork.co.uk/blueprint/api/blueprint.php?typeid="


def get_fuzzwork_bom(type_id):
    """
    Fetch the manufacturing materials for a specific blueprint/type from Fuzzwork.
    Returns a list of dicts: [{"typeid": int, "name": str, "quantity": int}, ...]
    """
    cache_key = f"industry_reforged_bom_{type_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        url = f"{FUZZWORK_BOM_API}{type_id}"
        resp = requests.get(url, verify=False, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # "1" is the activity ID for Manufacturing
            manufacturing_materials = data.get("activityMaterials", {}).get("1", [])
            # Cache for 1 week (60 * 60 * 24 * 7)
            cache.set(cache_key, manufacturing_materials, 604800)
            return manufacturing_materials
    except Exception as e:
        logger.error(f"Failed to fetch Fuzzwork BOM for type_id {type_id}: {e}")

    return []


def calculate_order_bom(order):
    """
    Calculates the aggregated Bill of Materials for a MemberOrder.
    Returns a dictionary mapping material type_id to a dict of details:
    {
        material_type_id: {
            "type_id": int,
            "name": str,
            "quantity": int
        }
    }
    """
    bom = {}
    # AA Industry App
    from industry_reforged.models import CorpItemConfig

    for item in order.items.all():
        type_id = item.item_type.id
        quantity = item.quantity

        # Determine Material Efficiency
        me_level = 0
        # Alliance Auth
        from allianceauth.eveonline.models import EveCorporationInfo

        try:
            corp_info = EveCorporationInfo.objects.get(
                corporation_id=order.character.corporation_id
            )
            config = CorpItemConfig.objects.filter(
                item_type_id=type_id, corporation=corp_info
            ).first()
            if config:
                me_level = config.manual_me
        except Exception:
            pass

        materials = get_fuzzwork_bom(type_id)
        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)

            # Simple BOM math: (base_qty * quantity) * (1 - me_level/100)
            # In EVE, fractional materials are usually rounded up per job run, but for an estimation
            # across an entire order, this provides a highly accurate Shopping List.
            required_qty = max(
                1, math.ceil(base_qty * quantity * (1 - (me_level / 100.0)))
            )

            if mat_type_id in bom:
                bom[mat_type_id]["quantity"] += required_qty
            else:
                bom[mat_type_id] = {
                    "type_id": mat_type_id,
                    "name": mat.get("name"),
                    "quantity": required_qty,
                }

    return bom


def calculate_tasks_bom(tasks, corp_info=None):
    """
    Calculates the aggregated Bill of Materials for a list of ProductionTask objects.
    Optionally pass corp_info (EveCorporationInfo) to apply corporate ME discounts.
    """
    bom = {}
    # AA Industry App
    from industry_reforged.models import CorpItemConfig

    for task in tasks:
        type_id = task.item_type.id
        quantity = task.quantity

        me_level = 0
        if corp_info:
            try:
                config = CorpItemConfig.objects.filter(
                    item_type_id=type_id, corporation=corp_info
                ).first()
                if config:
                    me_level = config.manual_me
            except Exception:
                pass

        materials = get_fuzzwork_bom(type_id)
        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)

            required_qty = max(
                1, math.ceil(base_qty * quantity * (1 - (me_level / 100.0)))
            )

            if mat_type_id in bom:
                bom[mat_type_id]["quantity"] += required_qty
            else:
                bom[mat_type_id] = {
                    "type_id": mat_type_id,
                    "name": mat.get("name"),
                    "quantity": required_qty,
                }

    return bom


def get_recursive_bom_tree(type_id, name, quantity, me_dict, depth=0):
    """
    Recursively fetch manufacturing materials to build a hierarchical BOM.
    """
    if depth > 15:  # Safety limit for recursion
        return {
            "type_id": type_id,
            "name": name,
            "quantity": quantity,
            "sub_materials": [],
        }

    materials = get_fuzzwork_bom(type_id)
    sub_materials = []

    for mat in materials:
        mat_type_id = mat.get("typeid")
        mat_name = mat.get("name")
        base_qty = mat.get("quantity", 0)

        # Apply ME discount if configured
        me_level = me_dict.get(mat_type_id, 0)
        required_qty = max(1, math.ceil(base_qty * quantity * (1 - (me_level / 100.0))))

        child_node = get_recursive_bom_tree(
            mat_type_id, mat_name, required_qty, me_dict, depth + 1
        )
        sub_materials.append(child_node)

    return {
        "type_id": type_id,
        "name": name,
        "quantity": quantity,
        "sub_materials": sub_materials,
    }


def calculate_recursive_order_bom(order):
    """
    Calculates the hierarchical Bill of Materials for a MemberOrder.
    Returns a list of trees (one for each requested item).
    """
    # Alliance Auth
    from allianceauth.eveonline.models import EveCorporationInfo

    # AA Industry App
    from industry_reforged.models import CorpItemConfig

    me_dict = {}
    try:
        corp_info = EveCorporationInfo.objects.get(
            corporation_id=order.character.corporation_id
        )
        for config in CorpItemConfig.objects.filter(corporation=corp_info):
            me_dict[config.item_type_id] = config.manual_me
    except Exception:
        pass

    tree = []
    for item in order.items.all():
        type_id = item.item_type.id
        quantity = item.quantity
        name = item.item_type.name

        node = get_recursive_bom_tree(type_id, name, quantity, me_dict)
        tree.append(node)

    return tree
