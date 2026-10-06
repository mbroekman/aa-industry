"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...models import (
    CorpInventory,
    CorporationWebhookConfig,
    CorpPricingConfig,
    MemberOrder,
    ProductionTask,
)
from ...utils.bom_engine import (
    calculate_order_bom,
    calculate_recursive_order_bom,
)
from ...utils.discord import send_discord_webhook
from ...utils.pricing_engine import (
    calculate_quote,
    get_detailed_prices,
    get_prices_with_overrides,
)


def view_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    """View details of a quote/order"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    order = MemberOrder.objects.filter(id=order_id).first()

    if not order:
        messages.error(request, _("Order not found."))
        return redirect("industry_reforged:orders_dashboard")

    # Access control: owner OR director OR industrialist
    if (
        order.character_id not in user_characters
        and not request.user.has_perm("industry_reforged.corp_access")
        and not request.user.has_perm("industry_reforged.industrialist_access")
    ):
        messages.error(request, _("Access denied."))
        return redirect("industry_reforged:orders_dashboard")

    # If the order is still REQUESTED, we recalculate the quote dynamically
    # so that any new Item Configurations or Type Discounts are applied immediately.
    corp_info = None
    if order.character and order.character.corporation:
        corp_info = order.character.corporation

    if order.status == "REQUESTED":
        parsed_items = {item.item_type: item.quantity for item in order.items.all()}
        new_total, item_details = calculate_quote(
            parsed_items, corp_info, ignore_discounts=order.ignore_discounts
        )

        for detail in item_details:
            order_item = order.items.filter(item_type=detail["eve_type"]).first()
            if order_item:
                order_item.price_per_unit = detail["final_price_per_unit"]
                order_item.discount_applied = detail["discount_percent"]
                order_item.save()

        order.total_price = new_total
        order.save()

    bom_materials = calculate_order_bom(order)

    total_bom_price = 0
    bom_materials_list = []
    bom_blueprints_list = []
    
    if bom_materials:
        mat_ids = list(bom_materials.keys())

        from eveuniverse.models import EveType
        blueprint_ids = set(
            EveType.objects.filter(
                id__in=mat_ids, eve_group__eve_category_id=9
            ).values_list("id", flat=True)
        )

        prices = get_detailed_prices(mat_ids, corp_info)
        for mat_id, data in bom_materials.items():
            price_info = prices.get(
                mat_id, {"original_jita_price": 0, "final_price": 0}
            )
            data["price_per_unit"] = price_info["final_price"]
            data["original_jita_price"] = price_info["original_jita_price"]
            data["total_price"] = price_info["final_price"] * data["quantity"]
            total_bom_price += data["total_price"]
            
            if mat_id in blueprint_ids:
                bom_blueprints_list.append(data)
            else:
                bom_materials_list.append(data)

    # Calculate original price from items before any discounts
    order_items = list(order.items.all().select_related("item_type"))
    original_price = sum(item.original_line_total for item in order_items)
    savings = float(original_price) - float(order.total_price)

    # Annotate buy products
    build_items = []
    buy_items = []
    from eveuniverse.models import EveIndustryActivityProduct
    for item in order_items:
        has_bp = EveIndustryActivityProduct.objects.filter(
            product_eve_type=item.item_type, activity_id=1
        ).exists()
        item.is_buy_product = not has_bp
        if item.is_buy_product:
            buy_items.append(item)
        else:
            build_items.append(item)

    recursive_bom_tree = []
    if request.user.has_perm(
        "industry_reforged.industrialist_access"
    ) or request.user.has_perm("industry_reforged.corp_access"):
        recursive_bom_tree = calculate_recursive_order_bom(order)

    from ...models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)

    # Third Party
    from eveuniverse.models import EveType

    from ...utils.bom_engine import get_blueprint_me

    def extract_manufactured_types(nodes, result_dict):
        for node in nodes:
            # Anything with sub_materials or explicitly built
            if node.get("activity_id") == 1 or node.get("sub_materials"):
                result_dict[node["type_id"]] = node["name"]
            if node.get("sub_materials"):
                extract_manufactured_types(node["sub_materials"], result_dict)

    products_me_dict = {}
    if request.user.has_perm("industry_reforged.corp_access"):
        # We need the tree to extract everything for the quote form
        if not recursive_bom_tree:
            recursive_bom_tree = calculate_recursive_order_bom(order)
        extract_manufactured_types(recursive_bom_tree, products_me_dict)

    invented_blueprint_types = set()
    def extract_invented(nodes):
        for node in nodes:
            if node.get("activity_id") == 8:
                invented_blueprint_types.add(node["type_id"])
            if node.get("sub_materials"):
                extract_invented(node["sub_materials"])
    if recursive_bom_tree:
        extract_invented(recursive_bom_tree)

    # Fallback if empty
    if not products_me_dict:
        for item in order_items:
            products_me_dict[item.item_type.id] = item.item_type.name

    products_me = []
    for type_id, name in products_me_dict.items():
        eve_type = EveType.objects.filter(id=type_id).first()
        if eve_type:
            me_val, max_runs, has_corp_bp = get_blueprint_me(eve_type, corp_info, order)
            if me_val is None:
                me_val = get_blueprint_me(eve_type, corp_info, None)[0]

            has_bp = EveIndustryActivityProduct.objects.filter(
                product_eve_type=eve_type, activity_id=1
            ).exists()

            if not has_bp:
                continue

            bp_prod = EveIndustryActivityProduct.objects.filter(
                product_eve_type_id=eve_type.id, activity_id__in=[1, 11]
            ).first()

            is_invented = False
            missing_bp = not has_corp_bp
            if bp_prod:
                if bp_prod.eve_type_id in invented_blueprint_types:
                    is_invented = True
                    missing_bp = False
                else:
                    bp_in_bom = next((bp for bp in bom_blueprints_list if bp.get("type_id") == bp_prod.eve_type_id), None)
                    if bp_in_bom:
                        missing_bp = bp_in_bom.get("corp_stock", 0) < bp_in_bom.get("quantity", 0)

            products_me.append(
                {
                    "type_id": type_id,
                    "name": name,
                    "current_me": me_val,
                    "current_max_runs": max_runs,
                    "has_blueprint": has_bp,
                    "missing_bp": missing_bp,
                }
            )

    missing_bps = []
    if corp_info:
        from ...models import CorpBlueprint
        has_corp_bp_cache = {}
        for bp in bom_blueprints_list:
            stock = bp.get("corp_stock", 0)
            req = bp.get("quantity", 0)
            if stock < req:
                bp_type_id = bp.get("type_id")
                has_bpo = False
                if bp_type_id:
                    if bp_type_id not in has_corp_bp_cache:
                        has_corp_bp_cache[bp_type_id] = CorpBlueprint.objects.filter(
                            corporation=corp_info, eve_type_id=bp_type_id
                        ).exists()
                    has_bpo = has_corp_bp_cache[bp_type_id]
                
                bp_copy = bp.copy()
                bp_copy["shortage"] = req - stock
                bp_copy["has_bpo"] = has_bpo
                missing_bps.append(bp_copy)

    estimated_build_cost = total_bom_price
    profit_margin = float(order.total_price) - estimated_build_cost

    is_privileged = request.user.has_perm(
        "industry_reforged.corp_access"
    ) or request.user.has_perm("industry_reforged.industrialist_access")
    
    from ...utils.pricing_engine import get_market_prices
    plex_price = get_market_prices([44992]).get(44992, 0.0)

    context = {
        "title": f"Order #{order.id}",
        "order": order,
        "order_items": order_items,
        "build_items": build_items,
        "buy_items": buy_items,
        "display_child_orders": is_privileged,
        "bom_materials": bom_materials_list,
        "bom_blueprints": bom_blueprints_list,
        "total_bom_price": total_bom_price,
        "estimated_build_cost": estimated_build_cost,
        "profit_margin": profit_margin,
        "original_price": original_price,
        "savings": savings,
        "is_owner": order.character_id in user_characters,
        "recursive_bom_tree": recursive_bom_tree,
        "facilities": facilities,
        "products_me": products_me,
        "missing_bps": missing_bps,
        "plex_price": plex_price,
    }
    output_locations = []
    if is_privileged:
        from ...models.orders import OutputLocation
        corp_info = request.user.profile.main_character.corporation_id
        from allianceauth.eveonline.models import EveCorporationInfo
        corp = EveCorporationInfo.objects.filter(corporation_id=corp_info).first()
        if corp:
            output_locations = OutputLocation.objects.filter(corporation=corp).order_by("name")
    
    context["output_locations"] = output_locations

    return render(request, "industry_reforged/view_quote.html", context)


def provide_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Director provides a final quote for a requested order"""
    if request.method == "POST":
        order = MemberOrder.objects.filter(id=order_id, status="REQUESTED").first()
        if not order:
            messages.error(request, _("Order not found or is not in REQUESTED status."))
            return redirect("industry_reforged:director_dashboard")

        try:
            new_total = float(request.POST.get("total_price", 0))
            if new_total < 0:
                raise ValueError("Price cannot be negative")

            upfront = float(request.POST.get("upfront_payment", 0))
            if upfront < 0 or upfront > new_total:
                raise ValueError("Upfront payment invalid")

            target_facility_id = request.POST.get("target_facility", None)
            if target_facility_id:
                from ...models import IndustryFacility

                facility = IndustryFacility.objects.filter(
                    facility_id=target_facility_id
                ).first()
                if facility:
                    order.target_facility = facility

            # Standard Library
            from decimal import Decimal

            new_total_decimal = Decimal(str(new_total))

            # Calculate proportion to scale individual items
            old_total = sum(item.line_total for item in order.items.all())

            order.total_price = new_total_decimal
            order.upfront_payment = upfront
            
            upfront_plex = int(request.POST.get("upfront_payment_plex", 0))
            if upfront_plex < 0:
                raise ValueError("PLEX payment cannot be negative")
            order.upfront_payment_plex = upfront_plex
            
            if "ignore_discounts" in request.POST:
                order.ignore_discounts = request.POST.get("ignore_discounts") == "on"
            else:
                order.ignore_discounts = False

            output_location_id = request.POST.get("output_location", "")
            if output_location_id:
                if output_location_id.startswith("new_"):
                    # Create new location
                    new_loc_name = output_location_id.replace("new_", "", 1).strip()
                    if new_loc_name:
                        from ...models.orders import OutputLocation
                        corp_info = request.user.profile.main_character.corporation_id
                        from allianceauth.eveonline.models import EveCorporationInfo
                        corp = EveCorporationInfo.objects.filter(corporation_id=corp_info).first()
                        if corp:
                            new_loc, created = OutputLocation.objects.get_or_create(
                                corporation=corp, name=new_loc_name
                            )
                            order.output_location = new_loc
                else:
                    from ...models.orders import OutputLocation
                    loc = OutputLocation.objects.filter(id=output_location_id).first()
                    if loc:
                        order.output_location = loc

            output_container = request.POST.get("output_container", "").strip()
            if output_container:
                order.output_container = output_container

            if old_total > 0 and old_total != order.total_price:
                ratio = float(order.total_price) / float(old_total)
                for item in order.items.all():
                    item.price_per_unit = Decimal(
                        str(float(item.price_per_unit) * ratio)
                    ).quantize(Decimal("0.01"))
                    item.save(update_fields=["price_per_unit"])

            # Save Blueprint ME Overrides
            # Third Party
            from eveuniverse.models import EveType

            from ...models import OrderBlueprintOverride

            for key, value in request.POST.items():
                if key.startswith("bp_me_"):
                    try:
                        type_id = int(key.replace("bp_me_", ""))
                        me_val = int(value)
                        if me_val >= 0:
                            eve_type = EveType.objects.filter(id=type_id).first()
                            if eve_type:
                                OrderBlueprintOverride.objects.update_or_create(
                                    order=order,
                                    item_type=eve_type,
                                    defaults={"manual_me": me_val},
                                )
                    except ValueError:
                        pass

            # Treat upfront payment as already paid by the user
            if upfront > 0:
                order.amount_paid = upfront

            order.status = "QUOTED"
            order.quoted_at = timezone.now()

            note_str = request.POST.get("note", "").strip()
            ts = timezone.now().strftime("%Y-%m-%d %H:%M")

            # Combine upfront payment logging and custom note
            log_entries = []
            if upfront > 0:
                log_entries.append(
                    f"[{ts}] Quote: Registered downpayment of {upfront:,.2f} ISK."
                )
            if note_str:
                log_entries.append(f"[{ts}] Quote Note: {note_str}")

            if log_entries:
                combined_note = "\n".join(log_entries)
                if order.notes:
                    order.notes += f"\n{combined_note}"
                else:
                    order.notes = combined_note

            order.save()

            # --- Check family quoting status ---
            parent = order.parent_order if order.parent_order else order

            family_unquoted = False
            if parent.status == "REQUESTED":
                family_unquoted = True
            elif parent.child_orders.filter(status="REQUESTED").exists():
                family_unquoted = True

            if not family_unquoted:
                # Everyone is quoted, send ONE unified notification using the grand total
                corporation = None
                if parent.character and parent.character.corporation:
                    corporation = parent.character.corporation

                grand_total = parent.grand_total

                if corporation:
                    webhook_config = CorporationWebhookConfig.objects.filter(
                        corporation=corporation
                    ).first()
                    if webhook_config and webhook_config.orders_webhook:
                        embed = {
                            "title": f"Quote Provided: Order #{parent.id}",
                            "description": f"A quote of **{grand_total:,.2f} ISK** has been provided for your order. Please review and accept.",
                            "color": 3447003,  # Blue
                        }
                        send_discord_webhook(webhook_config.orders_webhook, embed)

                # Send a direct message to the user who placed the order
                # AA Industry App
                from industry_reforged.tasks.utils import notify_discord_user

                dm_msg = f"**Industry Quote Received**\nYour order `#{parent.id}` has been quoted for **{grand_total:,.2f} ISK**. Please check the dashboard to accept or reject it."
                notify_discord_user(parent.character, dm_msg)

            messages.success(
                request,
                _("Quote of %(total)s ISK submitted successfully.")
                % {"total": f"{new_total:,.2f}"},
            )
            if family_unquoted:
                messages.info(
                    request,
                    _(
                        "Notification pending: other sub-orders in this group still require a quote."
                    ),
                )
        except ValueError:
            messages.error(request, _("Invalid price provided."))

        redirect_id = order.parent_order.id if order.parent_order else order.id
        return redirect("industry_reforged:view_quote", order_id=redirect_id)
    return redirect("industry_reforged:director_dashboard")


def htmx_update_quote_facility(request: WSGIRequest, order_id: int) -> HttpResponse:
    """HTMX endpoint to update the target facility and recalculate BOM live"""
    order = MemberOrder.objects.filter(id=order_id).first()
    if not order or order.status != "REQUESTED":
        return HttpResponse("")

    if "target_facility" in request.POST:
        target_facility_id = request.POST.get("target_facility")
        from ...models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        order.target_facility = facility
        order.save()

    # Recalculate BOM
    bom_materials = calculate_order_bom(order)

    corp_info = None
    if order.character and order.character.corporation:
        corp_info = order.character.corporation

    recursive_bom_tree = calculate_recursive_order_bom(order)

    from ...utils.pricing_engine import get_prices_with_overrides

    total_bom_price = 0
    bom_materials_list = []
    bom_blueprints_list = []
    
    if bom_materials:
        mat_ids = list(bom_materials.keys())
        
        from eveuniverse.models import EveType
        blueprint_ids = set(
            EveType.objects.filter(
                id__in=mat_ids, eve_group__eve_category_id=9
            ).values_list("id", flat=True)
        )
        
        prices = get_prices_with_overrides(mat_ids, corp_info)
        for mat_id, data in bom_materials.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]
            
            if mat_id in blueprint_ids:
                bom_blueprints_list.append(data)
            else:
                bom_materials_list.append(data)

    context = {
        "order": order,
        "bom_materials": bom_materials_list,
        "bom_blueprints": bom_blueprints_list,
        "total_bom_price": total_bom_price,
        "recursive_bom_tree": recursive_bom_tree,
    }
    return render(request, "industry_reforged/partials/quote_bom_panes.html", context)


def update_quote_me_overrides(request: WSGIRequest, order_id: int) -> HttpResponse:
    """HTMX endpoint to update the target facility and recalculate BOM live"""
    order = MemberOrder.objects.filter(id=order_id).first()
    if not order or order.status != "REQUESTED":
        return HttpResponse("")

    if "target_facility" in request.POST:
        target_facility_id = request.POST.get("target_facility")
        from ...models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        order.target_facility = facility
        order.save()

    if "ignore_discounts" in request.POST:
        order.ignore_discounts = request.POST.get("ignore_discounts") == "on"
        order.save()

    # Save Blueprint ME Overrides
    # Third Party
    from eveuniverse.models import EveType

    from ...models import OrderBlueprintOverride

    for key, value in request.POST.items():
        if key.startswith("bp_me_"):
            try:
                type_id = int(key.replace("bp_me_", ""))
                me_val = int(value) if value else 0
                runs_val_str = request.POST.get(f"bp_runs_{type_id}", "0")
                runs_val = int(runs_val_str) if runs_val_str else 0

                if me_val >= 0 or runs_val >= 0:
                    eve_type = EveType.objects.filter(id=type_id).first()
                    if eve_type:
                        OrderBlueprintOverride.objects.update_or_create(
                            order=order,
                            item_type=eve_type,
                            defaults={"manual_me": me_val, "max_runs": runs_val},
                        )
            except ValueError:
                pass

    messages.success(
        request,
        _("Material Efficiency overrides have been applied and BOM recalculated."),
    )
    url = reverse("industry_reforged:view_quote", kwargs={"order_id": order.id})
    return redirect(f"{url}#bom-pane")


def accept_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    order = MemberOrder.objects.filter(
        id=order_id, character_id__in=user_characters, status="QUOTED"
    ).first()

    if order:
        orders_to_accept = [order] + list(order.child_orders.filter(status="QUOTED"))

        for o in orders_to_accept:
            o.status = "ACCEPTED"
            o.accepted_at = timezone.now()
            o.save()

            # Get the corp config to calculate the reward value
            pricing_config = None
            if o.character.corporation:
                pricing_config = CorpPricingConfig.objects.filter(
                    corporation=o.character.corporation
                ).first()

            reward_percent = (
                pricing_config.builder_reward_percent if pricing_config else 0.0
            )

            # Calculate full BOM tree
            recursive_bom_tree = calculate_recursive_order_bom(o)

            # Extract all unique type_ids for pricing
            all_type_ids = set()

            def extract_types(node):
                all_type_ids.add(node["type_id"])
                for sub in node.get("sub_materials", []):
                    extract_types(sub)

            for tree in recursive_bom_tree:
                extract_types(tree)

            # Get prices
            corp_info = o.character.corporation if o.character else None
            prices = get_prices_with_overrides(list(all_type_ids), corp_info)

            # Third Party
            from eveuniverse.models import EveType

            eve_types = {
                t.id: t for t in EveType.objects.filter(id__in=list(all_type_ids))
            }

            # Recursive task creation
            def build_tasks(node, parent_task=None):
                # Only create a task if it has sub_materials (it's built)
                if node.get("sub_materials"):
                    type_id = node["type_id"]
                    quantity = node["quantity"]
                    eve_type = eve_types.get(type_id)
                    if not eve_type:
                        eve_type, _ = EveType.objects.get_or_create_esi(id=type_id)
                        eve_types[type_id] = eve_type

                    price_per_unit = prices.get(type_id, 0)
                    line_total = float(price_per_unit) * quantity
                    task_reward_value = line_total * (reward_percent / 100.0)

                    task = ProductionTask.objects.create(
                        item_type=eve_type,
                        quantity=quantity,
                        activity_id=node.get("activity_id", 1),
                        status="UNCLAIMED",
                        origin="MEMBER_ORDER",
                        created_from_order=o,
                        gamification_value=line_total,
                        builder_reward=task_reward_value,
                        bom_parent=parent_task,
                    )

                    for sub in node.get("sub_materials", []):
                        build_tasks(sub, parent_task=task)

            for tree in recursive_bom_tree:
                build_tasks(tree, parent_task=None)

            # Deduct used stock from the database
            def deduct_db_stock(node):
                qty = node.get("provided_from_stock", 0)
                if qty > 0 and o.target_facility:
                    inv = CorpInventory.objects.filter(
                        corporation_id=o.character.corporation_id,
                        location_id=o.target_facility.facility_id,
                        item_type_id=node["type_id"],
                    ).first()
                    if inv:
                        inv.quantity = max(0, inv.quantity - qty)
                        inv.save()

                for sub in node.get("sub_materials", []):
                    deduct_db_stock(sub)

            for tree in recursive_bom_tree:
                deduct_db_stock(tree)

        # Discord Webhook Notification
        corporation = None
        if order.character and order.character.corporation:
            corporation = order.character.corporation
        if corporation:
            webhook_config = CorporationWebhookConfig.objects.filter(
                corporation=corporation
            ).first()
            if webhook_config and webhook_config.orders_webhook:
                embed = {
                    "title": f"Quote Accepted: Order #{order.id}",
                    "description": f"**{order.character.character_name}** has accepted the quote. Tasks generated.",
                    "color": 3066993,  # Green
                }
                send_discord_webhook(webhook_config.orders_webhook, embed)

        messages.success(
            request,
            _(
                "Quote accepted! Your order is now in progress and tasks have been generated for builders."
            ),
        )
    return redirect("industry_reforged:orders_dashboard")


def reject_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    order = MemberOrder.objects.filter(
        id=order_id, character_id__in=user_characters, status="QUOTED"
    ).first()

    if order:
        orders_to_reject = [order] + list(order.child_orders.filter(status="QUOTED"))
        for o in orders_to_reject:
            o.status = "REJECTED"
            o.save()

        # Discord Webhook Notification
        corporation = None
        if order.character and order.character.corporation:
            corporation = order.character.corporation
        if corporation:
            webhook_config = CorporationWebhookConfig.objects.filter(
                corporation=corporation
            ).first()
            if webhook_config and webhook_config.orders_webhook:
                embed = {
                    "title": f"Quote Rejected: Order #{order.id}",
                    "description": f"**{order.character.character_name}** has rejected the quote.",
                    "color": 15158332,  # Red
                }
                send_discord_webhook(webhook_config.orders_webhook, embed)

        messages.info(request, _("Quote rejected and order cancelled."))
    return redirect("industry_reforged:orders_dashboard")
