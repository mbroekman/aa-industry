# Standard Library
import logging
import math

# Third Party
from eveuniverse.models import EveIndustryActivityMaterial, EveIndustryActivityProduct

logger = logging.getLogger(__name__)


def get_sde_bom(type_id):
    """
    Returns (materials, yield_qty) for the given type_id.
    First tries to use Industry Activities (accurate for T2/T3).
    Falls back to EveType.materials (legacy) if no industry activity found.
    """
    # Third Party
    from eveuniverse.models import (
        EveIndustryActivityMaterial,
        EveIndustryActivityProduct,
        EveType,
    )

    try:
        # Try finding the blueprint that manufactures this item (Activity 1 or 11)
        bp_prod = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=type_id, activity_id__in=[1, 11]
        ).first()

        if bp_prod:
            blueprint_id = bp_prod.eve_type_id
            activity = bp_prod.activity_id
            yield_qty = bp_prod.quantity

            mats = EveIndustryActivityMaterial.objects.filter(
                eve_type_id=blueprint_id, activity_id=activity
            )

            if mats.exists():
                materials = []
                for mat in mats:
                    materials.append(
                        {
                            "typeid": mat.material_eve_type_id,
                            "name": mat.material_eve_type.name,
                            "quantity": mat.quantity,
                        }
                    )
                return materials, yield_qty

        # Fallback to legacy EveType.materials
        eve_type = EveType.objects.get(id=type_id)
        if not eve_type.materials:
            return [], 1

        materials = []
        for mat in eve_type.materials.all():
            materials.append(
                {
                    "typeid": mat.material_eve_type_id,
                    "name": mat.material_eve_type.name,
                    "quantity": mat.quantity,
                }
            )
        return materials, 1
    except Exception:
        return [], 1


def calculate_facility_me_multiplier(facility, product_type, return_breakdown=False):
    """
    Calculates the combined (1 - HullBonus) * (1 - RigBonus * SecMultiplier)
    for a given IndustryFacility and the product being manufactured.
    """
    if not facility:
        if return_breakdown:
            return 1.0, 0.0, 0.0
        return 1.0

    sec_multiplier = 1.0
    if facility.security_space == "LOWSEC":
        sec_multiplier = 1.9
    elif facility.security_space == "NULLSEC_WH":
        sec_multiplier = 2.1

    rig_bonus = 0.0

    group_id = str(product_type.eve_group_id) if product_type.eve_group_id else None
    category_id = None
    if product_type.eve_group and product_type.eve_group.eve_category_id:
        category_id = str(product_type.eve_group.eve_category_id)

    for fac_rig in facility.rigs.all():
        rig = fac_rig.rig
        if rig.me_bonus > 0:
            applies = False
            if not rig.applies_to_groups and not rig.applies_to_categories:
                # If no specific group or category restrictions exist, it acts as a global rig
                applies = True
            else:
                if (
                    group_id
                    and rig.applies_to_groups
                    and group_id
                    in [x.strip() for x in rig.applies_to_groups.split(",")]
                ):
                    applies = True
                if (
                    category_id
                    and rig.applies_to_categories
                    and category_id
                    in [x.strip() for x in rig.applies_to_categories.split(",")]
                ):
                    applies = True

            if applies:
                rig_bonus_val = float(rig.me_bonus) / 100.0
                if rig_bonus_val > rig_bonus:
                    rig_bonus = rig_bonus_val

    hull_bonus = 0.0
    # Hardcode 1% for Upwell Engineering Complexes for MVP
    if facility.type_id in [35825, 35826, 35827]:  # Raitaru, Azbel, Sotiyo
        hull_bonus = 0.01

    multiplier = (1.0 - hull_bonus) * (1.0 - (rig_bonus * sec_multiplier))
    if return_breakdown:
        return multiplier, hull_bonus, (rig_bonus * sec_multiplier)
    return multiplier


def get_blueprint_me(product_type, corp_info=None, order=None):
    """
    Resolves the ME for a product in the following order:
    1. OrderBlueprintOverride
    2. CorpItemConfig
    3. Global Tech 1/Tech 2 Default
    """
    # AA Industry App
    from industry_reforged.models import CorpItemConfig, OrderBlueprintOverride

    # Check for order-specific override first
    if order:
        bp_override = OrderBlueprintOverride.objects.filter(
            order=order, item_type=product_type
        ).first()
        if bp_override and (bp_override.manual_me > 0 or bp_override.max_runs > 0):
            # If ME is 0, we still might want to return the override if max_runs is > 0,
            # but let's fall back to default ME if manual_me is 0.
            me_val = bp_override.manual_me if bp_override.manual_me > 0 else None
            return me_val, bp_override.max_runs

    # Then check for global corp config
    if corp_info:
        corp_config = CorpItemConfig.objects.filter(
            corporation=corp_info, item_type=product_type
        ).first()
        if corp_config and (corp_config.manual_me > 0 or corp_config.max_runs > 0):
            me_val = corp_config.manual_me if corp_config.manual_me > 0 else None
            return me_val, corp_config.max_runs

    default_t1 = 10
    default_t2 = 2
    if corp_info and hasattr(corp_info, "pricing_config"):
        default_t1 = corp_info.pricing_config.default_t1_me
        default_t2 = corp_info.pricing_config.default_t2_me

    # Third Party
    from eveuniverse.models import EveIndustryActivityProduct

    bp_prod = EveIndustryActivityProduct.objects.filter(
        product_eve_type_id=product_type.id, activity_id__in=[1, 11]
    ).first()

    # We still need a default ME if none was provided by overrides
    if bp_prod:
        is_invented = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=bp_prod.eve_type_id, activity_id=8
        ).exists()
        if is_invented:
            return default_t2, 0

    return default_t1, 0


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
    # Alliance Auth
    from allianceauth.eveonline.models import EveCorporationInfo

    try:
        corp_info = EveCorporationInfo.objects.get(
            corporation_id=order.character.corporation_id
        )
    except Exception:
        corp_info = None

    bom_splits = {}
    for child in order.child_orders.all():
        if child.notes and child.notes.startswith("Sub-component"):
            for child_item in child.items.all():
                bom_splits[child_item.item_type.id] = (
                    bom_splits.get(child_item.item_type.id, 0) + child_item.quantity
                )

    for item in order.items.all():
        type_id = item.item_type.id
        quantity = item.quantity

        if quantity <= 0:
            continue

        target_facility = order.target_facility
        facility_me_multiplier = calculate_facility_me_multiplier(
            target_facility, item.item_type
        )

        me_override, max_runs_override = get_blueprint_me(
            item.item_type, corp_info, order
        )
        product_me = (
            me_override
            if me_override is not None
            else get_blueprint_me(item.item_type, corp_info, None)[0]
        )

        materials, yield_qty = get_sde_bom(type_id)
        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity

        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)

            # EVE Math: run_cost = round(base_qty * ((100 - ME)/100) * facility_me_multiplier, 2)
            run_cost = round(
                base_qty * ((100.0 - product_me) / 100.0) * facility_me_multiplier, 2
            )

            # Chunking logic for max_runs
            if max_runs_override > 0 and runs > max_runs_override:
                full_jobs = runs // max_runs_override
                remaining_runs = runs % max_runs_override

                required_qty = 0
                if full_jobs > 0:
                    required_qty += full_jobs * max(
                        max_runs_override, math.ceil(run_cost * max_runs_override)
                    )
                if remaining_runs > 0:
                    required_qty += max(
                        remaining_runs, math.ceil(run_cost * remaining_runs)
                    )
            else:
                required_qty = max(runs, math.ceil(run_cost * runs))

            base_total = max(runs, base_qty * runs)

            available = bom_splits.get(mat_type_id, 0)
            if available > 0:
                if available >= required_qty:
                    bom_splits[mat_type_id] -= required_qty
                    required_qty = 0
                else:
                    required_qty -= available
                    bom_splits[mat_type_id] = 0

            if required_qty <= 0:
                continue

            if mat_type_id in bom:
                bom[mat_type_id]["quantity"] += required_qty
                bom[mat_type_id]["base_quantity"] += base_total
                bom[mat_type_id]["savings"] = bom[mat_type_id].get("savings", 0) + (
                    base_total - required_qty
                )
            else:
                bom[mat_type_id] = {
                    "type_id": mat_type_id,
                    "name": mat.get("name"),
                    "quantity": required_qty,
                    "base_quantity": base_total,
                    "savings": base_total - required_qty,
                }

    return bom


def calculate_tasks_bom(tasks, corp_info=None):
    """
    Calculates the aggregated Bill of Materials for a list of ProductionTask objects.
    Optionally pass corp_info (EveCorporationInfo) to apply corporate ME discounts.
    """
    bom = {}
    for task in tasks:
        type_id = task.item_type.id
        quantity = task.quantity
        order = task.created_from_order if hasattr(task, "created_from_order") else None

        target_facility = None
        if order and order.target_facility:
            target_facility = order.target_facility

        facility_me_multiplier = calculate_facility_me_multiplier(
            target_facility, task.item_type
        )

        me_override, max_runs_override = get_blueprint_me(
            task.item_type, corp_info, order
        )
        product_me = (
            me_override
            if me_override is not None
            else get_blueprint_me(task.item_type, corp_info, None)[0]
        )

        materials, yield_qty = get_sde_bom(type_id)
        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity

        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)

            run_cost = round(
                base_qty * ((100.0 - product_me) / 100.0) * facility_me_multiplier, 2
            )

            # Chunking logic for max_runs
            if max_runs_override > 0 and runs > max_runs_override:
                full_jobs = runs // max_runs_override
                remaining_runs = runs % max_runs_override

                required_qty = 0
                if full_jobs > 0:
                    required_qty += full_jobs * max(
                        max_runs_override, math.ceil(run_cost * max_runs_override)
                    )
                if remaining_runs > 0:
                    required_qty += max(
                        remaining_runs, math.ceil(run_cost * remaining_runs)
                    )
            else:
                required_qty = max(runs, math.ceil(run_cost * runs))

            base_total = max(runs, base_qty * runs)

            if mat_type_id in bom:
                bom[mat_type_id]["quantity"] += required_qty
                bom[mat_type_id]["base_quantity"] += base_total
                bom[mat_type_id]["savings"] = bom[mat_type_id].get("savings", 0) + (
                    base_total - required_qty
                )
            else:
                bom[mat_type_id] = {
                    "type_id": mat_type_id,
                    "name": mat.get("name"),
                    "quantity": required_qty,
                    "base_quantity": base_total,
                    "savings": base_total - required_qty,
                }

    return bom


def get_recursive_bom_tree(
    type_id,
    name,
    quantity,
    config_dict,
    depth=0,
    target_facility=None,
    stock_dict=None,
    corp_info=None,
    order=None,
    bom_splits=None,
    top_level_splits=None,
):
    """
    Recursively fetch manufacturing materials to build a hierarchical BOM.
    """
    original_quantity = quantity
    provided_from_stock = 0
    if stock_dict is not None and type_id in stock_dict:
        available = stock_dict[type_id]
        if available > 0:
            if available >= quantity:
                provided_from_stock = quantity
                stock_dict[type_id] -= quantity
                quantity = 0
            else:
                provided_from_stock = available
                quantity -= available
                stock_dict[type_id] = 0

    provided_from_child_order = 0

    # For top-level items, we do NOT offset quantity because it's already reduced in the DB.
    # We only reconstruct the original quantity and display it was split.
    if depth == 0 and top_level_splits is not None and type_id in top_level_splits:
        available = top_level_splits[type_id]
        if available > 0:
            provided_from_child_order = available
            original_quantity += available
            top_level_splits[type_id] -= available

    # For sub-materials (and BOM-split top-level items), we DO offset the requirements.
    elif bom_splits is not None and type_id in bom_splits:
        available = bom_splits[type_id]
        if available > 0:
            if available >= quantity:
                provided_from_child_order = quantity
                bom_splits[type_id] -= quantity
                quantity = 0
            else:
                provided_from_child_order = available
                quantity -= available
                bom_splits[type_id] = 0

    if depth > 15:  # Safety limit for recursion
        return {
            "type_id": type_id,
            "name": name,
            "quantity": quantity,
            "base_quantity": original_quantity,
            "provided_from_stock": provided_from_stock,
            "provided_from_child_order": provided_from_child_order,
            "activity_id": 1,
            "sub_materials": [],
            "product_me": 0,
            "hull_bonus": 0.0,
            "rig_bonus": 0.0,
            "facility_name": target_facility.name if target_facility else "None",
        }

    if quantity == 0:
        return {
            "type_id": type_id,
            "name": name,
            "quantity": 0,
            "base_quantity": original_quantity,
            "provided_from_stock": provided_from_stock,
            "provided_from_child_order": provided_from_child_order,
            "activity_id": 1,
            "sub_materials": [],
            "product_me": 0,
            "hull_bonus": 0.0,
            "rig_bonus": 0.0,
            "facility_name": target_facility.name if target_facility else "None",
        }

    # If the root item itself is excluded, treat it as a raw material (leaf node)
    if config_dict.get(type_id, {}).get("exclude_from_orders", False):
        return {
            "type_id": type_id,
            "name": name,
            "quantity": quantity,
            "base_quantity": original_quantity,
            "provided_from_stock": provided_from_stock,
            "provided_from_child_order": provided_from_child_order,
            "activity_id": 1,
            "sub_materials": [],
            "product_me": 0,
            "hull_bonus": 0.0,
            "rig_bonus": 0.0,
            "facility_name": target_facility.name if target_facility else "None",
        }

    # Third Party
    from eveuniverse.models import EveType

    try:
        product_type = EveType.objects.get(id=type_id)
        facility_me_multiplier, hull_bonus, total_rig_bonus = (
            calculate_facility_me_multiplier(
                target_facility, product_type, return_breakdown=True
            )
        )
    except EveType.DoesNotExist:
        facility_me_multiplier = 1.0
        hull_bonus = 0.0
        total_rig_bonus = 0.0

    if "product_type" in locals():
        product_me, max_runs = get_blueprint_me(product_type, corp_info, order)
    else:
        product_me, max_runs = 0, 0

    materials, yield_qty = get_sde_bom(type_id)
    runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity
    sub_materials = []

    for mat in materials:
        mat_type_id = mat.get("typeid")
        mat_config = config_dict.get(mat_type_id, {})
        mat_name = mat.get("name")
        base_qty = mat.get("quantity", 0)

        run_cost = round(
            base_qty * ((100.0 - product_me) / 100.0) * facility_me_multiplier, 2
        )

        # Chunking logic for max_runs
        if max_runs > 0 and runs > max_runs:
            full_jobs = runs // max_runs
            remaining_runs = runs % max_runs

            chunked_qty = full_jobs * max(max_runs, math.ceil(run_cost * max_runs))
            if remaining_runs > 0:
                chunked_qty += max(remaining_runs, math.ceil(run_cost * remaining_runs))
            required_qty = chunked_qty
        else:
            required_qty = max(runs, math.ceil(run_cost * runs))

        base_total = max(runs, base_qty * runs)

        # If excluded from orders, skip adding it to the visual tree
        if mat_config.get("exclude_from_orders", False):
            continue
        else:
            sub_node = get_recursive_bom_tree(
                mat_type_id,
                mat_name,
                required_qty,
                config_dict,
                depth=depth + 1,
                target_facility=target_facility,
                stock_dict=stock_dict,
                corp_info=corp_info,
                order=order,
                bom_splits=bom_splits,
                top_level_splits=top_level_splits,
            )
        sub_materials.append(sub_node)

    # Fetch blueprints for science jobs (Copying / Invention)
    try:
        bp_prod = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=type_id, activity_id__in=[1, 11]
        ).first()
        if bp_prod:
            blueprint_type = bp_prod.eve_type

            # Check if this blueprint comes from invention (activity 8)
            inv_prod = EveIndustryActivityProduct.objects.filter(
                product_eve_type_id=blueprint_type.id, activity_id=8
            ).first()
            if inv_prod:
                t1_blueprint = inv_prod.eve_type

                inv_sub_materials = []
                inv_mats = EveIndustryActivityMaterial.objects.filter(
                    eve_type_id=t1_blueprint.id, activity_id=8
                )
                for m in inv_mats:
                    mat_id = m.material_eve_type.id
                    if config_dict.get(mat_id, {}).get("exclude_from_orders", False):
                        continue
                    inv_sub_materials.append(
                        {
                            "type_id": m.material_eve_type.id,
                            "name": m.material_eve_type.name,
                            "quantity": math.ceil(m.quantity * runs),
                            "base_quantity": math.ceil(m.quantity * runs),
                            "activity_id": 0,
                            "sub_materials": [],
                        }
                    )

                # Copying task for T1 Blueprint
                if not config_dict.get(t1_blueprint.id, {}).get(
                    "exclude_from_orders", False
                ):
                    inv_sub_materials.append(
                        {
                            "type_id": t1_blueprint.id,
                            "name": t1_blueprint.name,
                            "quantity": runs,
                            "base_quantity": runs,
                            "activity_id": 5,  # Copying
                            "sub_materials": [],
                        }
                    )

                if not config_dict.get(blueprint_type.id, {}).get(
                    "exclude_from_orders", False
                ):
                    sub_materials.append(
                        {
                            "type_id": blueprint_type.id,
                            "name": blueprint_type.name,
                            "quantity": runs,
                            "activity_id": 8,  # Invention
                            "sub_materials": inv_sub_materials,
                        }
                    )
            else:
                # T1 Blueprint -> Copying
                if not config_dict.get(blueprint_type.id, {}).get(
                    "exclude_from_orders", False
                ):
                    sub_materials.append(
                        {
                            "type_id": blueprint_type.id,
                            "name": blueprint_type.name,
                            "quantity": runs,
                            "base_quantity": runs,
                            "activity_id": 5,  # Copying
                            "sub_materials": [],
                        }
                    )
    except Exception as e:
        logger.warning(f"Failed to process science jobs for type {type_id}: {e}")

    return {
        "type_id": type_id,
        "name": name,
        "quantity": quantity,
        "base_quantity": original_quantity,  # The root's quantity is the requested quantity
        "provided_from_stock": provided_from_stock,
        "provided_from_child_order": provided_from_child_order,
        "activity_id": 1,  # Manufacturing
        "sub_materials": sub_materials,
        "product_me": product_me if "product_me" in locals() else 0,
        "hull_bonus": (hull_bonus * 100.0) if "hull_bonus" in locals() else 0.0,
        "rig_bonus": (
            (total_rig_bonus * 100.0) if "total_rig_bonus" in locals() else 0.0
        ),
        "facility_name": target_facility.name if target_facility else "None",
    }


def calculate_recursive_order_bom(order):
    """
    Calculates the hierarchical Bill of Materials for a MemberOrder.
    Returns a list of trees (one for each requested item).
    """
    # Alliance Auth
    from allianceauth.eveonline.models import EveCorporationInfo

    try:
        corp_info = EveCorporationInfo.objects.get(
            corporation_id=order.character.corporation_id
        )
    except Exception:
        corp_info = None

    stock_dict = None
    if order.target_facility:
        # AA Industry App
        from industry_reforged.models import CorpInventory

        invs = CorpInventory.objects.filter(
            corporation_id=order.character.corporation_id,
            location_id=order.target_facility.facility_id,
        )
        stock_dict = {inv.item_type_id: inv.quantity for inv in invs}

    bom_splits = {}
    top_level_splits = {}
    for child in order.child_orders.all():
        if child.notes and child.notes.startswith("Sub-component"):
            for item in child.items.all():
                bom_splits[item.item_type.id] = (
                    bom_splits.get(item.item_type.id, 0) + item.quantity
                )
        else:
            for item in child.items.all():
                top_level_splits[item.item_type.id] = (
                    top_level_splits.get(item.item_type.id, 0) + item.quantity
                )

    config_dict = {}
    if corp_info:
        # AA Industry App
        from industry_reforged.models import CorpItemConfig

        configs = CorpItemConfig.objects.filter(corporation=corp_info)
        for c in configs:
            config_dict[c.item_type_id] = {
                "exclude_from_orders": c.exclude_from_orders,
            }

    tree = []
    for item in order.items.all():
        type_id = item.item_type.id
        quantity = item.quantity
        name = item.item_type.name

        node = get_recursive_bom_tree(
            type_id,
            name,
            quantity,
            config_dict,
            target_facility=order.target_facility,
            stock_dict=stock_dict,
            corp_info=corp_info,
            order=order,
            bom_splits=bom_splits,
            top_level_splits=top_level_splits,
        )
        tree.append(node)

    return tree


def calculate_recursive_tasks_bom(tasks, corp_info=None):
    """
    Calculates the hierarchical Bill of Materials for a list of ProductionTasks.
    Returns a list of trees (one for each task).
    """
    config_dict = {}
    if corp_info:
        # AA Industry App
        from industry_reforged.models import CorpItemConfig

        configs = CorpItemConfig.objects.filter(corporation=corp_info)
        for c in configs:
            config_dict[c.item_type_id] = {
                "exclude_from_orders": c.exclude_from_orders,
            }

    tree = []
    for task in tasks:
        type_id = task.item_type.id
        quantity = task.quantity
        name = task.item_type.name

        target_facility = None
        if (
            hasattr(task, "created_from_order")
            and task.created_from_order
            and task.created_from_order.target_facility
        ):
            target_facility = task.created_from_order.target_facility
        elif hasattr(task, "facility") and task.facility:
            target_facility = task.facility
        order = task.created_from_order if hasattr(task, "created_from_order") else None
        node = get_recursive_bom_tree(
            type_id,
            name,
            quantity,
            config_dict,
            target_facility=target_facility,
            corp_info=corp_info,
            order=order,
        )
        tree.append(node)

    return tree
