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
            product_eve_type_id=type_id, activity_id__in=[1, 11], eve_type__published=True
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
                return materials, yield_qty, activity

        # Fallback to legacy EveType.materials
        eve_type = EveType.objects.get(id=type_id)

        fallback_yield = eve_type.portion_size or 1

        if not eve_type.materials.exists():
            return [], fallback_yield, 1

        materials = []
        for mat in eve_type.materials.all():
            materials.append(
                {
                    "typeid": mat.material_eve_type_id,
                    "name": mat.material_eve_type.name,
                    "quantity": mat.quantity,
                }
            )
        return materials, fallback_yield, 1
    except Exception as e:
        logger.error(f"Failed to get SDE bom for {type_id}: {e}")
        try:
            # Third Party
            from eveuniverse.models import EveType

            return [], EveType.objects.get(id=type_id).portion_size or 1, 1
        except Exception:
            return [], 1, 1


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
    # Third Party
    from eveuniverse.models import EveIndustryActivityProduct

    # AA Industry App
    from industry_reforged.models import CorpItemConfig, OrderBlueprintOverride

    # First determine the default ME based on T1/T2
    default_t1 = 10
    default_t2 = 2
    if corp_info and hasattr(corp_info, "pricing_config"):
        default_t1 = corp_info.pricing_config.default_t1_me
        default_t2 = corp_info.pricing_config.default_t2_me

    bp_prod = EveIndustryActivityProduct.objects.filter(
        product_eve_type_id=product_type.id, activity_id__in=[1, 11], eve_type__published=True
    ).first()

    has_corp_bp = True
    if bp_prod:
        if corp_info:
            from industry_reforged.models import CorpBlueprint
            has_corp_bp = CorpBlueprint.objects.filter(
                corporation=corp_info, eve_type_id=bp_prod.eve_type_id
            ).exists()
        else:
            has_corp_bp = False

    default_me = default_t1
    if not bp_prod or bp_prod.activity_id == 11 or not has_corp_bp:
        # Reactions, non-industry items, or missing corp blueprints
        default_me = 0
    else:
        # Third Party
        from eveuniverse.models import EveIndustryActivityDuration

        is_invented = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=bp_prod.eve_type_id, activity_id=8, eve_type__published=True
        ).exists()

        if is_invented:
            default_me = default_t2
        else:
            has_me_research = EveIndustryActivityDuration.objects.filter(
                eve_type_id=bp_prod.eve_type_id, activity_id=4
            ).exists()

            if not has_me_research:
                default_me = 0
            else:
                default_me = default_t1

    # Check for order-specific override first
    if order:
        bp_override = OrderBlueprintOverride.objects.filter(
            order=order, item_type=product_type
        ).first()
        if bp_override and (bp_override.manual_me > 0 or bp_override.max_runs > 0):
            # If manual_me is 0 but max_runs > 0, fallback to default ME
            me_val = bp_override.manual_me if bp_override.manual_me > 0 else default_me
            return me_val, bp_override.max_runs, has_corp_bp

    # Then check for global corp config
    if corp_info:
        corp_config = CorpItemConfig.objects.filter(
            corporation=corp_info, item_type=product_type
        ).first()
        if corp_config and (corp_config.manual_me > 0 or corp_config.max_runs > 0):
            me_val = corp_config.manual_me if corp_config.manual_me > 0 else default_me
            return me_val, corp_config.max_runs, has_corp_bp

    return default_me, 0, has_corp_bp


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

    corp_stock = {}
    if corp_info:
        # Django
        from django.db.models import Sum

        # AA Industry App
        from industry_reforged.models import CorpInventory, CorpBlueprint

        inventory = (
            CorpInventory.objects.filter(corporation=corp_info, quantity__gt=0)
            .values("item_type_id")
            .annotate(total=Sum("quantity"))
        )
        for inv in inventory:
            corp_stock[inv["item_type_id"]] = inv["total"]
            
        # Overwrite blueprint stock with actual BPC runs instead of copy counts
        bpc_inventory = (
            CorpBlueprint.objects.filter(corporation=corp_info, quantity=-2, runs__gt=0)
            .values("eve_type_id")
            .annotate(total_runs=Sum("runs"))
        )
        for bpc in bpc_inventory:
            corp_stock[bpc["eve_type_id"]] = bpc["total_runs"]

    return flatten_bom_tree(calculate_recursive_order_bom(order), corp_stock=corp_stock)


def calculate_tasks_bom(tasks, corp_info=None):
    """
    Calculates the aggregated Bill of Materials for a list of ProductionTask objects.
    Optionally pass corp_info (EveCorporationInfo) to apply corporate ME discounts.
    """
    corp_stock = {}
    if corp_info:
        # Django
        from django.db.models import Sum

        # AA Industry App
        from industry_reforged.models import CorpInventory, CorpBlueprint

        inventory = (
            CorpInventory.objects.filter(corporation=corp_info, quantity__gt=0)
            .values("item_type_id")
            .annotate(total=Sum("quantity"))
        )
        for inv in inventory:
            corp_stock[inv["item_type_id"]] = inv["total"]
            
        # Overwrite blueprint stock with actual BPC runs instead of copy counts
        bpc_inventory = (
            CorpBlueprint.objects.filter(corporation=corp_info, quantity=-2, runs__gt=0)
            .values("eve_type_id")
            .annotate(total_runs=Sum("runs"))
        )
        for bpc in bpc_inventory:
            corp_stock[bpc["eve_type_id"]] = bpc["total_runs"]

    return flatten_bom_tree(calculate_recursive_tasks_bom(tasks, corp_info=corp_info), corp_stock=corp_stock)


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
    base_quantity=None,
):
    """
    Recursively fetch manufacturing materials to build a hierarchical BOM.
    """
    original_quantity = quantity
    original_base_quantity = base_quantity if base_quantity is not None else quantity
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

    materials, yield_qty, activity_id = get_sde_bom(type_id)

    if depth > 15:  # Safety limit for recursion
        return {
            "type_id": type_id,
            "name": name,
            "quantity": quantity,
            "base_quantity": original_quantity,
            "provided_from_stock": provided_from_stock,
            "provided_from_child_order": provided_from_child_order,
            "activity_id": activity_id,
            "sub_materials": [],
            "product_me": 0,
            "hull_bonus": 0.0,
            "rig_bonus": 0.0,
            "facility_name": target_facility.name if target_facility else "None",
            "missing_bp": False,
        }

    build_or_buy = config_dict.get(type_id, {}).get("build_or_buy", "BUILD")
    if build_or_buy == "BUY":
        return {
                "type_id": type_id,
                "name": name,
                "quantity": quantity,
                "base_quantity": original_quantity,
                "provided_from_stock": provided_from_stock,
                "provided_from_child_order": provided_from_child_order,
                "activity_id": activity_id,
                "sub_materials": [],
                "product_me": 0,
                "hull_bonus": 0.0,
                "rig_bonus": 0.0,
                "facility_name": "Market",
                "missing_bp": False,
            }

    if quantity == 0:
        return {
            "type_id": type_id,
            "name": name,
            "quantity": 0,
            "base_quantity": original_quantity,
            "provided_from_stock": provided_from_stock,
            "provided_from_child_order": provided_from_child_order,
            "activity_id": activity_id,
            "sub_materials": [],
            "product_me": 0,
            "hull_bonus": 0.0,
            "rig_bonus": 0.0,
            "facility_name": target_facility.name if target_facility else "None",
            "missing_bp": False,
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
            "activity_id": activity_id,
            "sub_materials": [],
            "product_me": 0,
            "hull_bonus": 0.0,
            "rig_bonus": 0.0,
            "facility_name": target_facility.name if target_facility else "None",
            "missing_bp": False,
        }

    # Third Party
    from eveuniverse.models import EveType

    try:
        product_type = EveType.objects.get(id=type_id)
        
        if activity_id == 11:
            from industry_reforged.models import IndustryFacility
            reaction_fac = None
            if corp_info:
                from django.db.models import Q
                valid_facility_ids = list(corp_info.known_locations.values_list("location_id", flat=True))
                reaction_fac = IndustryFacility.objects.filter(
                    Q(owner_id=corp_info.corporation_id) | Q(facility_id__in=valid_facility_ids) | Q(owner_id__isnull=True),
                    is_default_reaction=True
                ).first()
            if not reaction_fac:
                reaction_fac = IndustryFacility.objects.filter(is_default_reaction=True).first()
            if reaction_fac:
                target_facility = reaction_fac
        elif target_facility is None:
            from industry_reforged.models import IndustryFacility
            if corp_info:
                from django.db.models import Q
                valid_facility_ids = list(corp_info.known_locations.values_list("location_id", flat=True))
                target_facility = IndustryFacility.objects.filter(
                    Q(owner_id=corp_info.corporation_id) | Q(facility_id__in=valid_facility_ids) | Q(owner_id__isnull=True),
                    is_default=True
                ).first()
            if not target_facility:
                target_facility = IndustryFacility.objects.filter(is_default=True).first()

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
        product_me, max_runs, has_corp_bp = get_blueprint_me(product_type, corp_info, order)
    else:
        product_me, max_runs, has_corp_bp = 0, 0, False

    runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity
    sub_materials = []

    for mat in materials:
        mat_type_id = mat.get("typeid")
        mat_config = config_dict.get(mat_type_id, {})
        mat_name = mat.get("name")
        base_qty = mat.get("quantity", 0)

        # Do NOT round run_cost prematurely to 2 decimals, to prevent drift on large run counts
        run_cost = (
            base_qty * ((100.0 - product_me) / 100.0) * facility_me_multiplier
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
                base_quantity=base_total,
            )
        sub_materials.append(sub_node)

    # Fetch blueprints for science jobs (Copying / Invention) or reaction formula
    bp_prod = None
    blueprint_type = None
    try:
        bp_prod = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=type_id, activity_id__in=[1, 11], eve_type__published=True
        ).first()
        if bp_prod:
            blueprint_type = bp_prod.eve_type

            # Check if this blueprint comes from invention (activity 8)
            inv_prod = EveIndustryActivityProduct.objects.filter(
                product_eve_type_id=blueprint_type.id, activity_id=8, eve_type__published=True
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
                            "base_quantity": runs,
                            "activity_id": 8,  # Invention
                            "sub_materials": inv_sub_materials,
                        }
                    )
            elif bp_prod.activity_id == 11:
                # Reaction Formula: reusable formula
                if not config_dict.get(blueprint_type.id, {}).get(
                    "exclude_from_orders", False
                ):
                    sub_materials.append(
                        {
                            "type_id": blueprint_type.id,
                            "name": blueprint_type.name,
                            "quantity": 1,
                            "base_quantity": 1,
                            "activity_id": 11,  # Reaction Formula
                            "sub_materials": [],
                            "facility_name": target_facility.name if target_facility else "None",
                            "is_reaction": True,
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
                            "facility_name": target_facility.name if target_facility else "None",
                            "is_reaction": False,
                        }
                    )
    except Exception as e:
        logger.warning(f"Failed to process science jobs for type {type_id}: {e}")

    return {
        "type_id": type_id,
        "name": name,
        "quantity": quantity,
        "base_quantity": original_base_quantity,
        "provided_from_stock": provided_from_stock,
        "provided_from_child_order": provided_from_child_order,
        "activity_id": activity_id,
        "is_reaction": (activity_id == 11),
        "blueprint_type_id": blueprint_type.id if blueprint_type else None,
        "blueprint_name": blueprint_type.name if blueprint_type else None,
        "sub_materials": sub_materials,
        "product_me": product_me if "product_me" in locals() else 0,
        "hull_bonus": (hull_bonus * 100.0) if "hull_bonus" in locals() else 0.0,
        "rig_bonus": (
            (total_rig_bonus * 100.0) if "total_rig_bonus" in locals() else 0.0
        ),
        "facility_name": target_facility.name if target_facility else "None",
        "missing_bp": not has_corp_bp if "has_corp_bp" in locals() else False,
    }


def flatten_bom_tree(recursive_tree, corp_stock=None):
    """
    Flattens a recursive BOM tree into an aggregated dictionary of leaf nodes.
    Leaf nodes are materials that have no sub_materials.
    """
    bom = {}
    if corp_stock is None:
        corp_stock = {}

    def _flatten(node, is_top_level=False):
        # We only aggregate leaf nodes (raw materials or components explicitly excluded from breakdown)
        if not node.get("sub_materials"):
            if is_top_level:
                # Top-level items that cannot be built (e.g. BUY items) should not be in the BOM materials
                # because they are already listed on the order details.
                return
                
            type_id = node.get("type_id")
            if type_id not in bom:
                bom[type_id] = {
                    "type_id": type_id,
                    "name": node.get("name"),
                    "quantity": 0,
                    "base_quantity": 0,
                    "corp_stock": corp_stock.get(type_id, 0),
                }
            bom[type_id]["quantity"] += node.get("quantity", 0)
            bom[type_id]["base_quantity"] += node.get("base_quantity", node.get("quantity", 0))
        else:
            for sub in node.get("sub_materials", []):
                _flatten(sub, is_top_level=False)

    for tree in recursive_tree:
        _flatten(tree, is_top_level=True)

    # Fetch group names for all unique types
    type_ids = list(bom.keys())
    if type_ids:
        from eveuniverse.models import EveType
        types = EveType.objects.filter(id__in=type_ids).select_related("eve_group")
        
        def get_custom_group(t):
            if not t.eve_group:
                return "Other"
            cat_id = t.eve_group.eve_category_id
            group_id = t.eve_group.id
            group_name = t.eve_group.name
            
            if cat_id == 9:
                return "Blueprints"
            if cat_id == 43:
                return "Planetary Commodities"
            if group_id == 18:
                return "Minerals"
            if group_id == 429:
                return "Moon Goo"
            if group_id in [428, 427, 974]: # Intermediate, Composite, Hybrid Polymers
                return "Reaction Materials"
            if group_id in [711, 712, 1034]: # Gas clouds, Biochemical Silos
                return "Gases"
            if group_id == 423:
                return "Ice Products"
            if group_id == 754:
                return "Salvage"
            if group_id in [334, 913, 873]: # Construction Components, Advanced, Capital
                return "Components"
            
            return group_name
            
        group_map = {t.id: get_custom_group(t) for t in types}
        for type_id, data in bom.items():
            data["group_name"] = group_map.get(type_id, "Unknown")

    return bom


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
                "build_or_buy": c.build_or_buy,
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
                "build_or_buy": c.build_or_buy,
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
