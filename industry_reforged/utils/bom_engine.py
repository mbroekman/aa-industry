# Standard Library
import logging
import math

# Third Party
# Eve Universe
from eveuniverse.models import EveIndustryActivityMaterial, EveIndustryActivityProduct

# Django
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_sde_bom(type_id):
    """
    Fetch the manufacturing or reaction materials for a specific product/type from local SDE.
    Returns a tuple: (list of dicts, product_quantity)
    """
    cache_key = f"industry_reforged_bom_sde_{type_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        # Find the product entry. Activity 1 = Manufacturing, 11 = Reactions.
        product_entry = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=type_id, activity_id__in=[1, 11]
        ).first()

        if not product_entry:
            return ([], 1)

        blueprint_id = product_entry.eve_type_id
        activity_id = product_entry.activity_id
        product_quantity = product_entry.quantity

        materials = EveIndustryActivityMaterial.objects.filter(
            eve_type_id=blueprint_id, activity_id=activity_id
        ).select_related("material_eve_type")

        manufacturing_materials = []
        for mat in materials:
            manufacturing_materials.append(
                {
                    "typeid": mat.material_eve_type_id,
                    "name": mat.material_eve_type.name,
                    "quantity": mat.quantity,
                    "maketype": activity_id,
                }
            )

        result = (manufacturing_materials, product_quantity)
        cache.set(cache_key, result, 604800)
        return result
    except Exception as e:
        logger.error(f"Failed to fetch SDE BOM for type_id {type_id}: {e}")
        return ([], 1)


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

        materials, yield_qty = get_sde_bom(type_id)
        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity

        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)

            # Simple BOM math
            required_qty = max(1, math.ceil(base_qty * runs * (1 - (me_level / 100.0))))

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

        materials, yield_qty = get_sde_bom(type_id)
        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity

        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)

            required_qty = max(1, math.ceil(base_qty * runs * (1 - (me_level / 100.0))))

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

    materials, yield_qty = get_sde_bom(type_id)
    runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity
    sub_materials = []

    for mat in materials:
        mat_type_id = mat.get("typeid")
        mat_name = mat.get("name")
        base_qty = mat.get("quantity", 0)

        # Apply ME discount if configured
        me_level = me_dict.get(mat_type_id, 0)
        required_qty = max(1, math.ceil(base_qty * runs * (1 - (me_level / 100.0))))

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


def calculate_recursive_tasks_bom(tasks, corp_info=None):
    """
    Calculates the hierarchical Bill of Materials for a list of ProductionTasks.
    Returns a list of trees (one for each task).
    """
    # AA Industry App
    from industry_reforged.models import CorpItemConfig

    me_dict = {}
    if corp_info:
        try:
            for config in CorpItemConfig.objects.filter(corporation=corp_info):
                me_dict[config.item_type_id] = config.manual_me
        except Exception:
            pass

    tree = []
    for task in tasks:
        type_id = task.item_type_id
        quantity = task.quantity
        name = task.item_type.name

        node = get_recursive_bom_tree(type_id, name, quantity, me_dict)
        tree.append(node)

    return tree
