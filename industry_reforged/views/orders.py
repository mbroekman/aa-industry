"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import (
    CorpInventory,
    CorpItemConfig,
    CorporationWebhookConfig,
    CorpPricingConfig,
    MemberOrder,
    OrderFit,
    OrderItem,
    ProductionTask,
)
from ..utils.bom_engine import (
    calculate_order_bom,
    calculate_recursive_order_bom,
    calculate_recursive_tasks_bom,
    get_recursive_bom_tree,
    get_sde_bom,
)
from ..utils.discord import send_discord_webhook
from ..utils.fit_parser import parse_fit_text
from ..utils.pricing_engine import (
    calculate_quote,
    get_detailed_prices,
    get_prices_with_overrides,
)


def notify_order_ready(order: MemberOrder):
    # Django
    from django.contrib.auth.models import User
    from django.db.models import Q

    # Alliance Auth
    from allianceauth.notifications.models import Notification

    # 1. Auth Notification to Directors
    directors = User.objects.filter(
        Q(groups__permissions__codename="director_access")
        | Q(user_permissions__codename="director_access")
    ).distinct()

    message = f"Order #{order.id} from {order.character.character_name} is ready for delivery! Total price: {order.total_price} ISK. Payment Reference: {order.payment_reference}"

    for director in directors:
        Notification.objects.notify_user(
            user=director,
            title=f"Order #{order.id} Ready",
            message=message,
            level="success",
        )

    # 2. Discord Webhook
    webhook_config = CorporationWebhookConfig.objects.filter(
        corporation=order.corporation
    ).first()
    if webhook_config and webhook_config.directors_webhook:
        embed = {
            "title": f"Order #{order.id} Ready",
            "description": f"**{order.character.character_name}**'s order is fully built and ready to be delivered!\nPayment Reference: `{order.payment_reference}`\nTotal: `{order.total_price:,.2f} ISK`",
            "color": 3066993,  # Green
        }
        send_discord_webhook(webhook_config.directors_webhook, embed)


@login_required
@permission_required("industry_reforged.basic_access")
def shopping_list(request: WSGIRequest) -> HttpResponse:
    """Generate a consolidated Shopping List for selected orders."""
    order_ids = request.GET.getlist("order_ids")
    task_ids = request.GET.getlist("task_ids")
    type_id = request.GET.get("type_id")
    quantity = request.GET.get("quantity")
    item_name = request.GET.get("item_name")

    if not order_ids and not task_ids and not type_id:
        messages.warning(request, _("No items selected for shopping list."))
        return redirect(request.headers.get("referer", "industry_reforged:index"))

    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    bom = {}
    orders = []
    tasks = []
    recursive_bom_tree = []

    def merge_bom(target, source):
        for mat_id, data in source.items():
            if mat_id in target:
                target[mat_id]["quantity"] += data["quantity"]
                target[mat_id]["base_quantity"] += data.get(
                    "base_quantity", data["quantity"]
                )
            else:
                target[mat_id] = data

    if order_ids:
        orders = MemberOrder.objects.filter(
            id__in=order_ids, character_id__in=user_characters
        )
        for order in orders:
            recursive_bom_tree.extend(calculate_recursive_order_bom(order))
            merge_bom(bom, calculate_order_bom(order))

    if task_ids:
        # User can view tasks if they have basic_access (to claim them) or corp_access.
        # Unclaimed tasks are visible to all. Claimed tasks should be filtered by ownership.
        all_tasks = ProductionTask.objects.filter(id__in=task_ids)
        valid_tasks = []
        for t in all_tasks:
            if t.status == "UNCLAIMED" or (
                t.assigned_to_id and t.assigned_to_id in user_characters
            ):
                valid_tasks.append(t)

        tasks = valid_tasks

        corp_info = None
        main_char = request.user.profile.main_character
        if main_char and main_char.corporation:
            corp_info = main_char.corporation

        recursive_bom_tree.extend(
            calculate_recursive_tasks_bom(tasks, corp_info=corp_info)
        )
        from ..utils.bom_engine import calculate_tasks_bom

        merge_bom(bom, calculate_tasks_bom(tasks, corp_info=corp_info))

    if type_id and quantity:
        quantity = int(quantity)
        materials, yield_qty = get_sde_bom(type_id)

        corp_info = None
        main_char = request.user.profile.main_character
        if main_char and main_char.corporation:
            corp_info = main_char.corporation

        me_level = 0
        if corp_info:
            config = CorpItemConfig.objects.filter(
                item_type_id=type_id, corporation=corp_info
            ).first()
            if config:
                me_level = config.manual_me

        node = get_recursive_bom_tree(
            type_id, item_name or str(type_id), quantity, {type_id: me_level}
        )
        recursive_bom_tree.append(node)

        # Standard Library
        import math

        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity
        type_bom = {}
        for mat in materials:
            mat_type_id = mat.get("typeid")
            base_qty = mat.get("quantity", 0)
            req = max(runs, math.ceil(base_qty * runs))
            type_bom[mat_type_id] = {
                "type_id": mat_type_id,
                "name": mat.get("name"),
                "quantity": req,
                "base_quantity": req,
            }
        merge_bom(bom, type_bom)

    total_bom_price = 0
    sorted_bom = []
    if bom:
        mat_ids = list(bom.keys())

        from ..utils.pricing_engine import get_fuzzwork_prices

        prices = get_fuzzwork_prices(mat_ids)
        for mat_id, data in bom.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]

        sorted_bom = sorted(bom.values(), key=lambda x: x["name"])

    context = {
        "title": _("Shopping List"),
        "orders": orders,
        "tasks": tasks,
        "custom_item_name": item_name,
        "custom_item_quantity": quantity,
        "bom_materials": sorted_bom,
        "total_bom_price": total_bom_price,
        "recursive_bom_tree": recursive_bom_tree,
    }
    return render(request, "industry_reforged/shopping_list.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
def create_order(request: WSGIRequest) -> HttpResponse:
    """Create a new order from EFT fit or single items"""
    if request.method == "POST":
        fit_text = request.POST.get("fit_text", "").strip()

        if not fit_text:
            messages.error(request, _("Please provide an EFT fit."))
            return redirect("industry_reforged:create_order")

        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to create orders.")
            )
            return redirect("industry_reforged:create_order")

        parsed_items, unrecognized = parse_fit_text(fit_text)

        if unrecognized:
            messages.warning(
                request,
                f"Could not recognize the following items: {', '.join(unrecognized)}",
            )

        # Optional: Apply corp discount if user's main character is in a corp with config
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        # Filter out excluded items
        if corporation and parsed_items:
            excluded_configs = CorpItemConfig.objects.filter(
                corporation=corporation,
                exclude_from_orders=True,
                item_type_id__in=parsed_items.keys(),
            ).select_related("item_type")

            for config in excluded_configs:
                # Remove from the parsed dictionary
                if config.item_type_id in parsed_items:
                    del parsed_items[config.item_type_id]

                # Show warning message to the user
                msg = _(
                    "Item '%(item)s' was automatically removed from your order."
                ) % {"item": config.item_type.name}
                if config.exclude_warning_message:
                    msg += f" {config.exclude_warning_message}"
                messages.warning(request, msg)

        if not parsed_items:
            messages.error(
                request, _("No valid items remaining in the fit after filtering.")
            )
            return redirect("industry_reforged:create_order")

        total_price, item_details = calculate_quote(parsed_items, corporation)

        # Django
        from django.utils.crypto import get_random_string

        ref = "ORD-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()

        from ..models import IndustryFacility

        default_facility = IndustryFacility.objects.filter(is_default=True).first()

        order = MemberOrder.objects.create(
            character=character,
            status="REQUESTED",
            total_price=total_price,
            payment_reference=ref,
            target_facility=default_facility,
        )

        OrderFit.objects.create(order=order, raw_fit_text=fit_text)

        order_items = []
        for detail in item_details:
            order_items.append(
                OrderItem(
                    order=order,
                    item_type=detail["eve_type"],
                    quantity=detail["quantity"],
                    price_per_unit=detail["final_price_per_unit"],
                    discount_applied=detail["discount_percent"],
                )
            )
        OrderItem.objects.bulk_create(order_items)

        # Send to all configured webhooks in the system, since orders are global
        webhook_configs = CorporationWebhookConfig.objects.all()
        for config in webhook_configs:
            embed = {
                "title": f"New Quote Requested: Order #{order.id}",
                "description": f"**{character.character_name}** has requested a quote.",
                "color": 3447003,  # Blue
                "fields": [
                    {
                        "name": "Total Estimated Price",
                        "value": f"{total_price:,.2f} ISK",
                        "inline": False,
                    }
                ],
            }
            if config.orders_webhook:
                send_discord_webhook(config.orders_webhook, embed)
            elif config.directors_webhook:
                send_discord_webhook(config.directors_webhook, embed)

        messages.success(request, _("Order parsed and quoted successfully!"))
        return redirect("industry_reforged:view_quote", order_id=order.id)

    characters = request.user.character_ownerships.all().select_related("character")
    context = {"title": "Create Order", "characters": [c.character for c in characters]}
    return render(request, "industry_reforged/create_order.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
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
        new_total, item_details = calculate_quote(parsed_items, corp_info)

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
    if bom_materials:
        mat_ids = list(bom_materials.keys())

        prices = get_detailed_prices(mat_ids, corp_info)
        for mat_id, data in bom_materials.items():
            price_info = prices.get(
                mat_id, {"original_jita_price": 0, "final_price": 0}
            )
            data["price_per_unit"] = price_info["final_price"]
            data["original_jita_price"] = price_info["original_jita_price"]
            data["total_price"] = price_info["final_price"] * data["quantity"]
            total_bom_price += data["total_price"]

    # Calculate original price from items before any discounts
    original_price = sum(item.original_line_total for item in order.items.all())
    savings = float(original_price) - float(order.total_price)

    recursive_bom_tree = []
    if request.user.has_perm(
        "industry_reforged.industrialist_access"
    ) or request.user.has_perm("industry_reforged.corp_access"):
        recursive_bom_tree = calculate_recursive_order_bom(order)

    from ..models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)

    # Third Party
    from eveuniverse.models import EveType

    from ..utils.bom_engine import get_blueprint_me

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

    # Fallback if empty
    if not products_me_dict:
        for item in order.items.all():
            products_me_dict[item.item_type.id] = item.item_type.name

    products_me = []
    for type_id, name in products_me_dict.items():
        eve_type = EveType.objects.filter(id=type_id).first()
        if eve_type:
            me_val, max_runs = get_blueprint_me(eve_type, corp_info, order)
            if me_val is None:
                me_val = get_blueprint_me(eve_type, corp_info, None)[0]

            products_me.append(
                {
                    "type_id": type_id,
                    "name": name,
                    "current_me": me_val,
                    "current_max_runs": max_runs,
                }
            )

    is_privileged = request.user.has_perm(
        "industry_reforged.corp_access"
    ) or request.user.has_perm("industry_reforged.industrialist_access")
    context = {
        "title": f"Order #{order.id}",
        "order": order,
        "display_child_orders": is_privileged,
        "bom_materials": bom_materials.values() if bom_materials else [],
        "total_bom_price": total_bom_price,
        "original_price": original_price,
        "savings": savings,
        "is_owner": order.character_id in user_characters,
        "recursive_bom_tree": recursive_bom_tree,
        "facilities": facilities,
        "products_me": products_me,
    }
    return render(request, "industry_reforged/view_quote.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
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
                from ..models import IndustryFacility

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

            from ..models import OrderBlueprintOverride

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
                from ..tasks.utils import notify_discord_user

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


@login_required
@permission_required("industry_reforged.corp_access")
def split_order(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Director splits specific items from an order into a new child order"""
    if request.method == "POST":
        order = MemberOrder.objects.filter(id=order_id, status="REQUESTED").first()
        if not order:
            messages.error(request, _("Order not found or is not in REQUESTED status."))
            return redirect("industry_reforged:director_dashboard")

        item_ids = request.POST.getlist("item_ids")
        if not item_ids:
            messages.error(request, _("No items selected for splitting."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        items_to_split = order.items.filter(id__in=item_ids)

        target_facility_id = request.POST.get("target_facility")
        from ..models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        # Parse requested quantities
        split_requests = []
        is_full_split = True
        for item in items_to_split:
            qty_str = request.POST.get(f"split_qty_{item.id}")
            try:
                split_qty = int(qty_str) if qty_str else item.quantity
            except ValueError:
                split_qty = item.quantity

            if split_qty <= 0 or split_qty > item.quantity:
                split_qty = item.quantity

            if split_qty < item.quantity:
                is_full_split = False

            split_requests.append((item, split_qty))

        if is_full_split and items_to_split.count() == order.items.count():
            messages.error(
                request,
                _(
                    "Cannot split all items completely from the order. Just change the facility instead."
                ),
            )
            return redirect("industry_reforged:view_quote", order_id=order.id)

        # Ensure parent has a payment reference
        # Django
        from django.utils.crypto import get_random_string

        if not order.payment_reference:
            order.payment_reference = (
                "ORD-"
                + get_random_string(4).upper()
                + "-"
                + get_random_string(4).upper()
            )
            order.save(update_fields=["payment_reference"])

        child_ref = (
            "ORD-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()
        )

        # Create child order
        child_order = MemberOrder.objects.create(
            character=order.character,
            status="REQUESTED",
            target_facility=facility,
            parent_order=order,
            payment_reference=child_ref,
            notes=f"Split from Order #{order.id}",
        )

        # Process splits
        from ..models import OrderItem

        for item, split_qty in split_requests:
            if split_qty == item.quantity:
                # Full split: move item to child
                item.order = child_order
                item.save(update_fields=["order"])
            else:
                # Partial split
                # 1. Reduce parent item
                item.quantity -= split_qty
                item.save(update_fields=["quantity"])

                # 2. Create child item
                OrderItem.objects.create(
                    order=child_order,
                    item_type=item.item_type,
                    quantity=split_qty,
                    price_per_unit=item.price_per_unit,
                    discount_applied=item.discount_applied,
                )

        # Recalculate estimated total price for both parent and child based on line_totals
        parent_total = sum(item.line_total for item in order.items.all())
        order.total_price = parent_total
        order.save(update_fields=["total_price"])

        child_total = sum(item.line_total for item in child_order.items.all())
        child_order.total_price = child_total
        child_order.save(update_fields=["total_price"])

        messages.success(
            request,
            _("Order split successfully into Child Order #%(child_id)s.")
            % {"child_id": child_order.id},
        )

    return redirect("industry_reforged:view_quote", order_id=order.id)


@login_required
@permission_required("industry_reforged.corp_access")
def split_bom_component(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Director splits a specific sub-component from the BOM into a new child order"""
    if request.method == "POST":
        order = MemberOrder.objects.filter(id=order_id, status="REQUESTED").first()
        if not order:
            messages.error(request, _("Order not found or is not in REQUESTED status."))
            return redirect("industry_reforged:director_dashboard")

        type_id = request.POST.get("type_id")
        quantity_str = request.POST.get("quantity")
        target_facility_id = request.POST.get("target_facility")

        if not type_id or not quantity_str:
            messages.error(request, _("Invalid component selection."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        try:
            quantity = int(quantity_str)
        except ValueError:
            messages.error(request, _("Invalid quantity."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        # Third Party
        from eveuniverse.models import EveType

        product_type = EveType.objects.filter(id=type_id).first()
        if not product_type:
            messages.error(request, _("Invalid EveType."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        from ..models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        # Ensure parent has a payment reference
        # Django
        from django.utils.crypto import get_random_string

        if not order.payment_reference:
            order.payment_reference = (
                "ORD-"
                + get_random_string(4).upper()
                + "-"
                + get_random_string(4).upper()
            )
            order.save(update_fields=["payment_reference"])

        child_ref = (
            "ORD-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()
        )

        # Create child order
        child_order = MemberOrder.objects.create(
            character=order.character,
            status="REQUESTED",
            target_facility=facility,
            parent_order=order,
            payment_reference=child_ref,
            notes=f"Sub-component '{product_type.name}' split from Order #{order.id}",
        )

        from ..models import CorpPricingConfig, CorpTypeDiscount

        corp_id = order.character.corporation_id
        pricing_config = CorpPricingConfig.objects.filter(
            corporation__corporation_id=corp_id
        ).first()

        child_discount = (
            pricing_config.default_discount_percent if pricing_config else 0.0
        )
        if pricing_config:
            td = CorpTypeDiscount.objects.filter(
                config=pricing_config, eve_type=product_type
            ).first()
            if td:
                child_discount = td.discount_percent

        # Create OrderItem on the child order
        from ..models import OrderItem

        item = OrderItem.objects.create(
            order=child_order,
            item_type=product_type,
            quantity=quantity,
            discount_applied=child_discount,
            price_per_unit=0,  # Will be set below
        )

        # Recalculate estimated total price for both parent and child
        # This will now trigger the BOM engine which automatically deducts the child order's items
        # from the parent's BOM.
        # Alliance Auth
        from allianceauth.eveonline.models import EveCorporationInfo

        from ..utils.pricing_engine import calculate_quote

        corp_id = order.character.corporation_id
        try:
            corp_info = EveCorporationInfo.objects.get(corporation_id=corp_id)
        except Exception:
            corp_info = None

        # Child Total (using calculate_quote which looks at the top-level items, i.e., the subcomponent itself)
        child_parsed_items = {item.item_type: item.quantity}
        child_new_total, child_item_details = calculate_quote(
            child_parsed_items, corp_info
        )

        child_order.total_price = child_new_total
        child_order.save(update_fields=["total_price"])

        # Update the child item with the correct quoted price
        if child_item_details:
            detail = child_item_details[0]
            item.price_per_unit = detail["final_price_per_unit"]
            item.discount_applied = detail["discount_percent"]
            item.save(update_fields=["price_per_unit", "discount_applied"])

        # Parent Total (Recalculate parent order total just in case, though view_quote will handle it anyway)
        parent_parsed_items = {i.item_type: i.quantity for i in order.items.all()}
        parent_new_total, parent_item_details = calculate_quote(
            parent_parsed_items, corp_info
        )

        order.total_price = parent_new_total
        order.save(update_fields=["total_price"])

        for detail in parent_item_details:
            i = order.items.filter(item_type=detail["eve_type"]).first()
            if i:
                i.price_per_unit = detail["final_price_per_unit"]
                i.discount_applied = detail["discount_percent"]
                i.save(update_fields=["price_per_unit", "discount_applied"])

        messages.success(
            request,
            _(
                "Sub-component %(name)s split successfully into Child Order #%(child_id)s."
            )
            % {"name": product_type.name, "child_id": child_order.id},
        )

    return redirect("industry_reforged:view_quote", order_id=order.id)


@login_required
@permission_required("industry_reforged.corp_access")
def htmx_update_quote_facility(request: WSGIRequest, order_id: int) -> HttpResponse:
    """HTMX endpoint to update the target facility and recalculate BOM live"""
    order = MemberOrder.objects.filter(id=order_id).first()
    if not order or order.status != "REQUESTED":
        return HttpResponse("")

    if "target_facility" in request.POST:
        target_facility_id = request.POST.get("target_facility")
        from ..models import IndustryFacility

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

    from ..utils.pricing_engine import get_prices_with_overrides

    total_bom_price = 0
    if bom_materials:
        mat_ids = list(bom_materials.keys())
        prices = get_prices_with_overrides(mat_ids, corp_info)
        for mat_id, data in bom_materials.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]

    context = {
        "order": order,
        "bom_materials": bom_materials.values() if bom_materials else [],
        "total_bom_price": total_bom_price,
        "recursive_bom_tree": recursive_bom_tree,
    }
    return render(request, "industry_reforged/partials/quote_bom_panes.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def update_quote_me_overrides(request: WSGIRequest, order_id: int) -> HttpResponse:
    """HTMX endpoint to update the target facility and recalculate BOM live"""
    order = MemberOrder.objects.filter(id=order_id).first()
    if not order or order.status != "REQUESTED":
        return HttpResponse("")

    if "target_facility" in request.POST:
        target_facility_id = request.POST.get("target_facility")
        from ..models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        order.target_facility = facility
        order.save()

    # Save Blueprint ME Overrides
    # Third Party
    from eveuniverse.models import EveType

    from ..models import OrderBlueprintOverride

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


@login_required
@permission_required("industry_reforged.basic_access")
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


@login_required
@permission_required("industry_reforged.basic_access")
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


@login_required
@permission_required("industry_reforged.basic_access")
def delete_order(request: WSGIRequest, order_id: int) -> HttpResponse:
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    # Check if the user is a director or the owner
    is_director = request.user.has_perm("industry_reforged.corp_access")

    if is_director:
        order = MemberOrder.objects.filter(id=order_id).first()
    else:
        order = MemberOrder.objects.filter(
            id=order_id,
            character_id__in=user_characters,
            status__in=["REQUESTED", "QUOTED"],
        ).first()

    if order:
        parent = order.parent_order

        # Move OrderItems back to parent if this was a standard item split (not a component split)
        # We can guess it's a component split if the parent's BOM would normally contain the child's items.
        # But actually, it's safer to let component splits just be deleted (since the parent BOM recalculates them).
        # Wait, if we just delete the child, the BOM engine naturally absorbs the components back.
        # So we just need to recalculate the parent order's total price.

        # Delete related tasks explicitly since they have on_delete=models.SET_NULL
        ProductionTask.objects.filter(created_from_order=order).delete()

        # Discord Webhook Notification
        corporation = None
        if order.character and order.character.corporation:
            corporation = order.character.corporation
        if corporation:
            webhook_config = CorporationWebhookConfig.objects.filter(
                corporation=corporation
            ).first()
            if webhook_config and webhook_config.orders_webhook:
                main_char = request.user.profile.main_character
                deleted_by_name = (
                    main_char.character_name if main_char else request.user.username
                )
                embed = {
                    "title": f"Order Deleted: #{order.id}",
                    "description": f"**{order.character.character_name}**'s order was deleted by **{deleted_by_name}**.",
                    "color": 15158332,  # Red
                }
                send_discord_webhook(webhook_config.orders_webhook, embed)

        # If this is a child order created via Split Items, we should move the items back to the parent!
        # How to distinguish? Component splits have a specific note: "Sub-component ... split from Order"
        if parent and not order.notes.startswith("Sub-component"):
            order.items.update(order=parent)

        order.delete()

        # Recalculate parent if it exists
        if parent:
            # Alliance Auth
            from allianceauth.eveonline.models import EveCorporationInfo

            from ..utils.bom_engine import calculate_order_bom
            from ..utils.pricing_engine import get_prices_with_overrides

            try:
                corp_info = EveCorporationInfo.objects.get(
                    corporation_id=parent.character.corporation_id
                )
            except Exception:
                corp_info = None

            from ..models import CorpPricingConfig

            pricing_config = CorpPricingConfig.objects.filter(
                corporation__corporation_id=parent.character.corporation_id
            ).first()

            parent_bom = calculate_order_bom(parent)
            parent_bom_price = 0
            if parent_bom:
                mat_ids = list(parent_bom.keys())
                prices = get_prices_with_overrides(mat_ids, corp_info)
                for mat_id, data in parent_bom.items():
                    price = prices.get(mat_id, 0)
                    parent_bom_price += price * data["quantity"]

            parent_discount = (
                parent.items.first().discount_applied
                if parent.items.exists()
                else (
                    pricing_config.default_discount_percent if pricing_config else 0.0
                )
            )
            parent_discount_multiplier = (100.0 - parent_discount) / 100.0
            parent_discounted_price = parent_bom_price * parent_discount_multiplier

            tax = 0.0
            # Facility tax rate removed as it's not present on IndustryFacility
            parent_tax_amount = parent_discounted_price * tax

            corp_tax = 0.0
            parent_corp_tax_amount = parent_discounted_price * corp_tax

            parent_final = (
                parent_discounted_price + parent_tax_amount + parent_corp_tax_amount
            )
            parent.total_price = parent_final

            # If the parent was quoted, we might want to drop it back to requested since the scope changed,
            # but let's just update the price for now so the director can review it.
            if parent.status == "QUOTED":
                parent.status = "REQUESTED"

            parent.save(update_fields=["total_price", "status"])

            # Update line totals for parent if only 1 item
            if parent.items.count() == 1:
                i = parent.items.first()
                i.price_per_unit = (parent_final / i.quantity) if i.quantity > 0 else 0
                i.save(update_fields=["price_per_unit"])

        messages.success(request, _("Order successfully deleted."))
    else:
        messages.error(
            request,
            _("Order could not be found or you don't have permission to delete it."),
        )

    return redirect("industry_reforged:orders_dashboard")
