"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from esi.decorators import token_required

from .forms import (
    CorpItemConfigForm,
    CorpPricingConfigForm,
    CorpTypeDiscountForm,
)
from .models import (
    CharacterIndustryJob,
    CharacterPlanet,
    CorpInventory,
    CorpItemConfig,
    CorpMOTD,
    CorporationIndustryJob,
    CorporationSyncConfig,
    CorporationWebhookConfig,
    CorpPricingConfig,
    CorpTypeDiscount,
    CorpWalletDivision,
    CorpWalletJournal,
    MemberOrder,
    OrderFit,
    OrderItem,
    ProductionTask,
    TaskExecutionLog,
    TaxConfig,
)
from .tasks import task_sync_corp_inventory, task_sync_corp_wallets, update_character_pi
from .utils.bom_engine import (
    calculate_order_bom,
    calculate_recursive_order_bom,
    calculate_recursive_tasks_bom,
    get_recursive_bom_tree,
    get_sde_bom,
)
from .utils.discord import send_discord_webhook
from .utils.fit_parser import parse_fit_text
from .utils.pricing_engine import (
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
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view
    """
    return personal_dashboard(request)


@login_required
@permission_required("industry_reforged.basic_access")
def personal_dashboard(request: WSGIRequest) -> HttpResponse:
    """Personal Dashboard View"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    jobs = (
        CharacterIndustryJob.objects.filter(character_id__in=user_characters)
        .select_related("blueprint_type", "product_type", "character")
        .order_by("-end_date")
    )

    active_statuses = ["active", "paused", "ready"]
    active_jobs = [j for j in jobs if j.status in active_statuses]
    history_jobs = [j for j in jobs if j.status not in active_statuses]

    planets = list(
        CharacterPlanet.objects.filter(character_id__in=user_characters)
        .select_related("character", "planet_type")
        .prefetch_related("pins", "pins__type", "pins__product_type")
        .order_by("character__character_name", "planet_id")
    )

    expired_chars = set()
    full_storage_chars = set()

    for planet in planets:
        if planet.has_expired_extractors:
            expired_chars.add(planet.character_id)
        if planet.has_full_storage:
            full_storage_chars.add(planet.character_id)

    for planet in planets:
        planet.character_has_expired_extractors = planet.character_id in expired_chars
        planet.character_has_full_storage = planet.character_id in full_storage_chars
        planet.character_needs_attention = (
            planet.character_has_expired_extractors or planet.character_has_full_storage
        )

    context = {
        "active_jobs": active_jobs,
        "history_jobs": history_jobs,
        "planets": planets,
        "title": "Personal Industry Dashboard",
    }
    return render(request, "industry_reforged/personal_dashboard.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def corporate_dashboard(request: WSGIRequest) -> HttpResponse:
    """Corporate Dashboard View"""
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    jobs = (
        CorporationIndustryJob.objects.filter(
            corporation__corporation_id__in=user_corps
        )
        .select_related("blueprint_type", "product_type", "installer", "corporation")
        .order_by("-end_date")
    )

    active_statuses = ["active", "paused", "ready"]
    active_jobs = [j for j in jobs if j.status in active_statuses]
    history_jobs = [j for j in jobs if j.status not in active_statuses]

    context = {
        "active_jobs": active_jobs,
        "history_jobs": history_jobs,
        "title": "Corporate Industry Dashboard",
    }
    return render(request, "industry_reforged/corporate_dashboard.html", context)


@login_required
@token_required(
    scopes=["esi-industry.read_character_jobs.v1", "esi-planets.manage_planets.v1"]
)
def add_personal_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a personal token"""
    return redirect("industry_reforged:personal_dashboard")


@login_required
@token_required(
    scopes=[
        "esi-industry.read_corporation_jobs.v1",
        "esi-assets.read_corporation_assets.v1",
        "esi-universe.read_structures.v1",
        "esi-corporations.read_structures.v1",
        "esi-wallet.read_corporation_wallets.v1",
    ]
)
def add_corporate_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a corporate token and automatically configure sync."""
    character = EveCharacter.objects.filter(character_id=token.character_id).first()
    if character and character.corporation:
        CorporationSyncConfig.objects.update_or_create(
            corporation=character.corporation, defaults={"sync_character": character}
        )

    # After granting, redirect back to the page the user came from or the director dashboard
    referer = request.headers.get("referer")
    if referer and "director" in referer:
        return redirect("industry_reforged:director_config")
    return redirect("industry_reforged:corporate_dashboard")


@login_required
@permission_required("industry_reforged.basic_access")
def trigger_pi_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger PI sync for all characters of the user"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    for char_id in user_characters:
        update_character_pi.delay(character_id=char_id)

    messages.success(
        request,
        _(
            "Planetary Interaction sync has been queued in the background. Please refresh in a few minutes."
        ),
    )
    return redirect("industry_reforged:personal_dashboard")


@login_required
@permission_required("industry_reforged.basic_access")
def orders_dashboard(request: WSGIRequest) -> HttpResponse:
    """Member Orders Dashboard"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    orders = MemberOrder.objects.filter(
        character_id__in=user_characters, parent_order__isnull=True
    ).order_by("-created_at")

    context = {"orders": orders, "title": "My Orders"}
    return render(request, "industry_reforged/orders_dashboard.html", context)


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
        from .utils.bom_engine import calculate_tasks_bom

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

        from .utils.pricing_engine import get_fuzzwork_prices

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

        order = MemberOrder.objects.create(
            character=character,
            status="REQUESTED",
            total_price=total_price,
            payment_reference=ref,
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

    from .models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)

    # Third Party
    from eveuniverse.models import EveType

    from .utils.bom_engine import get_blueprint_me

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
            me_val = get_blueprint_me(eve_type, corp_info, order)
            products_me.append(
                {
                    "type_id": type_id,
                    "name": name,
                    "current_me": me_val,
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
                from .models import IndustryFacility

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

            from .models import OrderBlueprintOverride

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
                from .tasks import notify_discord_user

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
        if items_to_split.count() == order.items.count():
            messages.error(
                request,
                _(
                    "Cannot split all items from the order. Just change the facility instead."
                ),
            )
            return redirect("industry_reforged:view_quote", order_id=order.id)

        target_facility_id = request.POST.get("target_facility")
        from .models import IndustryFacility

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
            notes=f"Split from Order #{order.id}",
        )

        # Move items
        items_to_split.update(order=child_order)

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

        from .models import IndustryFacility

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

        from .models import CorpPricingConfig, CorpTypeDiscount

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
        from .models import OrderItem

        item = OrderItem.objects.create(
            order=child_order,
            item_type=product_type,
            quantity=quantity,
            discount_applied=child_discount,
            price_per_unit=0,  # Will be set below
            line_total=0,  # Will be calculated next
        )

        # Recalculate estimated total price for both parent and child
        # This will now trigger the BOM engine which automatically deducts the child order's items
        # from the parent's BOM.
        # Alliance Auth
        # Alliance Auth corp info
        from allianceauth.eveonline.models import EveCorporationInfo

        from .utils.bom_engine import calculate_order_bom
        from .utils.pricing_engine import get_prices_with_overrides

        try:
            corp_info = EveCorporationInfo.objects.get(corporation_id=corp_id)
        except Exception:
            corp_info = None

        # Child Total
        child_bom = calculate_order_bom(child_order)
        child_bom_price = 0
        if child_bom:
            mat_ids = list(child_bom.keys())
            prices = get_prices_with_overrides(mat_ids, corp_info)
            for mat_id, data in child_bom.items():
                price = prices.get(mat_id, 0)
                child_bom_price += price * data["quantity"]

        # Apply discount
        child_discount_multiplier = (100.0 - child_discount) / 100.0
        child_discounted_price = child_bom_price * child_discount_multiplier

        # Apply facility tax and corp tax to child
        tax = 0.0
        if child_order.target_facility:
            tax = float(child_order.target_facility.tax_rate) / 100.0
        child_tax_amount = child_discounted_price * tax
        corp_tax = 0.0
        child_corp_tax_amount = child_discounted_price * corp_tax

        child_final = child_discounted_price + child_tax_amount + child_corp_tax_amount
        child_order.total_price = child_final
        child_order.save(update_fields=["total_price"])

        item.price_per_unit = (child_final / quantity) if quantity > 0 else 0
        item.line_total = child_final
        item.save(update_fields=["price_per_unit", "line_total"])

        # Parent Total
        parent_bom = calculate_order_bom(order)
        parent_bom_price = 0
        if parent_bom:
            mat_ids = list(parent_bom.keys())
            prices = get_prices_with_overrides(mat_ids, corp_info)
            for mat_id, data in parent_bom.items():
                price = prices.get(mat_id, 0)
                parent_bom_price += price * data["quantity"]

        parent_discount = (
            order.items.first().discount_applied
            if order.items.exists()
            else (pricing_config.default_discount_percent if pricing_config else 0.0)
        )
        parent_discount_multiplier = (100.0 - parent_discount) / 100.0
        parent_discounted_price = parent_bom_price * parent_discount_multiplier

        # Apply facility tax and corp tax to parent
        tax = 0.0
        if order.target_facility:
            tax = float(order.target_facility.tax_rate) / 100.0
        parent_tax_amount = parent_discounted_price * tax
        parent_corp_tax_amount = parent_discounted_price * corp_tax

        parent_final = (
            parent_discounted_price + parent_tax_amount + parent_corp_tax_amount
        )
        order.total_price = parent_final
        order.save(update_fields=["total_price"])

        # Update line totals for parent (we just divide proportionally if multiple items)
        if order.items.count() == 1:
            i = order.items.first()
            i.price_per_unit = (parent_final / i.quantity) if i.quantity > 0 else 0
            i.line_total = parent_final
            i.save(update_fields=["price_per_unit", "line_total"])

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
        from .models import IndustryFacility

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

    from .utils.pricing_engine import get_prices_with_overrides

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
        from .models import IndustryFacility

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

    from .models import OrderBlueprintOverride

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

            from .utils.bom_engine import calculate_order_bom
            from .utils.pricing_engine import get_prices_with_overrides

            try:
                corp_info = EveCorporationInfo.objects.get(
                    corporation_id=parent.character.corporation_id
                )
            except Exception:
                corp_info = None

            from .models import CorpPricingConfig

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
            if parent.target_facility:
                tax = float(parent.target_facility.tax_rate) / 100.0
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
                i.line_total = parent_final
                i.save(update_fields=["price_per_unit", "line_total"])

        messages.success(request, _("Order successfully deleted."))
    else:
        messages.error(
            request,
            _("Order could not be found or you don't have permission to delete it."),
        )

    return redirect("industry_reforged:orders_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def industrialist_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main execution dashboard for industrialists"""

    # Setup corp context
    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    motd = None
    if corporation:
        motd = CorpMOTD.objects.filter(corporation=corporation).first()

    # Helper to convert a queryset into a depth-sorted tree list
    def build_task_tree(qs):
        roots = []
        task_map = {}
        for t in qs:
            t.depth = 0
            t.children_list = []
            task_map[t.id] = t

        for t in qs:
            if t.bom_parent_id and t.bom_parent_id in task_map:
                task_map[t.bom_parent_id].children_list.append(t)
            else:
                roots.append(t)

        flattened = []

        def flatten(node, d):
            node.depth = d
            flattened.append(node)
            for child in node.children_list:
                flatten(child, d + 1)

        for root in roots:
            flatten(root, 0)
        return flattened

    # Unclaimed tasks
    unclaimed_tasks_qs = (
        ProductionTask.objects.filter(status="UNCLAIMED")
        .select_related("item_type", "bom_parent", "created_from_order")
        .order_by("-created_from_order__created_at", "id")
    )
    unclaimed_tasks = build_task_tree(unclaimed_tasks_qs)

    # My active tasks
    # Django
    from django.db.models import Count, Q

    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    my_tasks_qs = (
        ProductionTask.objects.filter(
            status="IN_PRODUCTION", assigned_to_id__in=user_characters
        )
        .select_related("item_type", "bom_parent")
        .annotate(
            incomplete_children_count=Count(
                "bom_children", filter=~Q(bom_children__status="COMPLETED")
            )
        )
        .order_by("-assigned_at", "id")
    )
    my_tasks = build_task_tree(my_tasks_qs)

    # My completed tasks (limit to recent 10 to avoid clutter)
    my_completed_tasks = ProductionTask.objects.filter(
        status="COMPLETED", assigned_to_id__in=user_characters
    ).order_by("-completed_at")[:10]

    # Summary of claimed tasks vs active jobs
    my_claimed_summary = []

    # Django
    from django.db.models import Sum

    # Total Claimed (from ProductionTask)
    claimed_grouped = (
        ProductionTask.objects.filter(
            status="IN_PRODUCTION", assigned_to_id__in=user_characters
        )
        .values("item_type__id", "item_type__name", "activity_id")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("item_type__name")
    )

    if claimed_grouped:
        # Third Party
        from eveuniverse.models import EveIndustryActivityProduct

        # Get active Character/Corp jobs for the user
        char_jobs = CharacterIndustryJob.objects.filter(
            character_id__in=user_characters, status__in=["active", "ready"]
        )

        # Determine all corp IDs for this user
        corp_ids = request.user.character_ownerships.all().values_list(
            "character__corporation_id", flat=True
        )

        corp_jobs = CorporationIndustryJob.objects.filter(
            installer_id__in=user_characters,
            status__in=["active", "ready"],
            corporation__corporation_id__in=corp_ids,
        )

        # Calculate completed to be accurate
        completed_grouped = (
            ProductionTask.objects.filter(
                status="COMPLETED", assigned_to_id__in=user_characters
            )
            .values("item_type__id")
            .annotate(total_quantity=Sum("quantity"))
        )
        completed_dict = {
            item["item_type__id"]: item["total_quantity"] for item in completed_grouped
        }

        # Mapping for activity_name
        activity_name_map = {
            1: "Manufacturing",
            3: "Research TE",
            4: "Research ME",
            5: "Copying",
            8: "Invention",
            11: "Reactions",
        }

        for item in claimed_grouped:
            type_id = item["item_type__id"]
            activity_id = item["activity_id"]
            activity_name = activity_name_map.get(
                activity_id, f"Activity {activity_id}"
            )

            in_progress = 0

            # Fetch portion size
            portion_size = 1
            bp_prod = EveIndustryActivityProduct.objects.filter(
                product_eve_type_id=type_id, activity_id=activity_id
            ).first()
            if bp_prod:
                portion_size = bp_prod.quantity

            # Filter jobs matching the product
            matching_char_jobs = [j for j in char_jobs if j.product_type_id == type_id]
            matching_corp_jobs = [j for j in corp_jobs if j.product_type_id == type_id]

            for j in matching_char_jobs:
                in_progress += j.runs * portion_size
            for j in matching_corp_jobs:
                in_progress += j.runs * portion_size

            total_claimed = item["total_quantity"]
            completed = completed_dict.get(type_id, 0)
            remaining = max(0, total_claimed - in_progress)

            my_claimed_summary.append(
                {
                    "item_type_id": type_id,
                    "item_type_name": item["item_type__name"],
                    "activity_name": activity_name,
                    "total_claimed": total_claimed,
                    "in_progress": in_progress,
                    "completed": completed,
                    "remaining": remaining,
                }
            )

    # Active corp jobs (from ESI sync)
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    corp_active_jobs = CorporationIndustryJob.objects.filter(
        corporation__corporation_id__in=user_corps, status="active"
    ).select_related("blueprint_type", "product_type", "installer")

    # Standard Library
    import random

    # Django
    from django.db.models import Sum

    slogans = [
        _("Keep the forge burning!"),
        _("Building the future of the corporation, one module at a time."),
        _("Industry is the backbone of our fleet."),
        _("Another day, another Capital ship."),
        _("Tritanium flows where the industrialists go."),
        _("Measure twice, build once."),
        _("The anvil never sleeps."),
        _("Forging victory out of raw materials."),
    ]

    orders_qs = MemberOrder.objects.filter(status__in=["ACCEPTED", "IN_PRODUCTION"])
    dynamic_motd_stats = {
        "orders_in_production": orders_qs.count(),
        "open_tasks": len(unclaimed_tasks),
        "active_jobs": corp_active_jobs.count(),
        "value_in_progress": orders_qs.aggregate(total=Sum("total_price"))["total"]
        or 0.0,
        "slogan": random.choice(slogans),
    }

    context = {
        "title": "Industrialist Dashboard",
        "motd": motd,
        "dynamic_motd_stats": dynamic_motd_stats,
        "unclaimed_tasks": unclaimed_tasks,
        "my_tasks": my_tasks,
        "my_completed_tasks": my_completed_tasks,
        "corp_active_jobs": corp_active_jobs,
        "my_claimed_summary": my_claimed_summary,
    }
    return render(request, "industry_reforged/industrialist_dashboard.html", context)


@login_required
@permission_required("industry_reforged.industrialist_access")
def claim_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to claim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="UNCLAIMED").first()
        if task:
            task.status = "IN_PRODUCTION"
            task.assigned_to = character
            task.assigned_at = timezone.now()

            # Prevent double-dipping: If character owns any ancestor task, this task's reward is 0
            def has_owned_ancestor(t, char):
                current = t.bom_parent
                while current:
                    if current.assigned_to == char:
                        return True
                    current = current.bom_parent
                return False

            if has_owned_ancestor(task, character):
                task.builder_reward = 0

            task.save()

            # Prevent double-dipping: If character already owned sub-components, nullify their rewards
            def zero_owned_descendants(t, char):
                for child in t.bom_children.all():
                    if child.assigned_to == char and child.builder_reward > 0:
                        child.builder_reward = 0
                        child.save(update_fields=["builder_reward"])
                    zero_owned_descendants(child, char)

            zero_owned_descendants(task, character)

            messages.success(
                request, f"Successfully claimed {task.quantity}x {task.item_type.name}."
            )
        else:
            messages.error(request, _("Task is no longer available or does not exist."))

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def unclaim_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to unclaim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="IN_PRODUCTION").first()
        if not task:
            messages.error(request, _("Task is no longer available or does not exist."))
            return redirect("industry_reforged:industrialist_dashboard")

        if task.assigned_to != character and not request.user.has_perm(
            "industry_reforged.corp_access"
        ):
            messages.error(request, _("You can only unclaim your own tasks."))
            return redirect("industry_reforged:industrialist_dashboard")

        # AA Industry App
        from industry_reforged.models import CorpPricingConfig

        corp_info = None
        if character.corporation:
            corp_info = character.corporation
        elif (
            request.user.has_perm("industry_reforged.corp_access")
            and request.user.profile.main_character.corporation
        ):
            corp_info = request.user.profile.main_character.corporation

        pricing_config = (
            CorpPricingConfig.objects.filter(corporation=corp_info).first()
            if corp_info
            else None
        )
        reward_pct = (
            float(pricing_config.builder_reward_percent) if pricing_config else 0.0
        )

        def restore_owned_descendants(t, char, pct):
            for child in t.bom_children.all():
                if child.assigned_to == char and child.builder_reward == 0:
                    child.builder_reward = (
                        float(child.gamification_value) * pct
                    ) / 100.0
                    child.save(update_fields=["builder_reward"])
                restore_owned_descendants(child, char, pct)

        if task.assigned_to:
            restore_owned_descendants(task, task.assigned_to, reward_pct)

        task.status = "UNCLAIMED"
        task.assigned_to = None
        task.assigned_at = None
        task.builder_reward = (float(task.gamification_value) * reward_pct) / 100.0
        task.save()

        messages.success(
            request, f"Successfully unclaimed {task.quantity}x {task.item_type.name}."
        )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def bulk_claim_tasks(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")

        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to claim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        tasks = ProductionTask.objects.filter(id__in=task_ids, status="UNCLAIMED")
        if tasks.exists():
            count = 0
            for task in tasks:
                task.status = "IN_PRODUCTION"
                task.assigned_to = character
                task.assigned_at = timezone.now()

                # Prevent double-dipping: If character owns any ancestor task, this task's reward is 0
                def has_owned_ancestor(t, char):
                    current = t.bom_parent
                    while current:
                        if current.assigned_to == char:
                            return True
                        current = current.bom_parent
                    return False

                if has_owned_ancestor(task, character):
                    task.builder_reward = 0

                task.save()

                # Prevent double-dipping: If character already owned sub-components, nullify their rewards
                def zero_owned_descendants(t, char):
                    for child in t.bom_children.all():
                        if child.assigned_to == char and child.builder_reward > 0:
                            child.builder_reward = 0
                            child.save(update_fields=["builder_reward"])
                        zero_owned_descendants(child, char)

                zero_owned_descendants(task, character)
                count += 1

            messages.success(request, f"Successfully claimed {count} tasks.")
        else:
            messages.error(
                request, _("No valid tasks selected or they are already claimed.")
            )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def bulk_unclaim_tasks(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")

        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to unclaim tasks.")
            )
            return redirect("industry_reforged:industrialist_dashboard")

        tasks = ProductionTask.objects.filter(id__in=task_ids, status="IN_PRODUCTION")
        if not request.user.has_perm("industry_reforged.corp_access"):
            tasks = tasks.filter(assigned_to=character)

        if tasks.exists():
            count = 0
            # AA Industry App
            from industry_reforged.models import CorpPricingConfig

            corp_info = None
            if character.corporation:
                corp_info = character.corporation
            elif (
                request.user.has_perm("industry_reforged.corp_access")
                and request.user.profile.main_character.corporation
            ):
                corp_info = request.user.profile.main_character.corporation

            pricing_config = (
                CorpPricingConfig.objects.filter(corporation=corp_info).first()
                if corp_info
                else None
            )
            reward_pct = (
                float(pricing_config.builder_reward_percent) if pricing_config else 0.0
            )

            def restore_owned_descendants(t, char, pct):
                for child in t.bom_children.all():
                    if child.assigned_to == char and child.builder_reward == 0:
                        child.builder_reward = (
                            float(child.gamification_value) * pct
                        ) / 100.0
                        child.save(update_fields=["builder_reward"])
                    restore_owned_descendants(child, char, pct)

            for task in tasks:
                if task.assigned_to:
                    restore_owned_descendants(task, task.assigned_to, reward_pct)
                task.status = "UNCLAIMED"
                task.assigned_to = None
                task.assigned_at = None
                task.builder_reward = (
                    float(task.gamification_value) * reward_pct
                ) / 100.0
                task.save()
                count += 1

            messages.success(request, f"Successfully unclaimed {count} tasks.")
        else:
            messages.error(
                request, _("No valid tasks selected or you do not own them.")
            )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def complete_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        user_characters = request.user.character_ownerships.all().values_list(
            "character_id", flat=True
        )

        task = ProductionTask.objects.filter(
            id=task_id, assigned_to_id__in=user_characters, status="IN_PRODUCTION"
        ).first()
        if task:

            def complete_tree(t):
                if t.status != "COMPLETED":
                    t.status = "COMPLETED"
                    t.completed_at = timezone.now()
                    t.save()
                    for child in t.bom_children.exclude(status="COMPLETED"):
                        complete_tree(child)

            complete_tree(task)

            # Check if all tasks for the order are completed to update MemberOrder status
            if task.created_from_order:
                order = task.created_from_order
                remaining = order.production_tasks.exclude(status="COMPLETED").exists()
                if not remaining:
                    order.status = "READY"
                    order.save()
                    notify_order_ready(order)

            messages.success(
                request, f"Marked {task.quantity}x {task.item_type.name} as completed!"
            )
        else:
            messages.error(request, _("Task not found or not assigned to you."))

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.industrialist_access")
def bulk_complete_tasks(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")
        user_characters = request.user.character_ownerships.all().values_list(
            "character_id", flat=True
        )

        tasks = ProductionTask.objects.filter(
            id__in=task_ids, assigned_to_id__in=user_characters, status="IN_PRODUCTION"
        )
        if tasks.exists():

            def complete_tree(t):
                completed_count = 0
                if t.status != "COMPLETED":
                    t.status = "COMPLETED"
                    t.completed_at = timezone.now()
                    t.save()
                    completed_count += 1
                    for child in t.bom_children.exclude(status="COMPLETED"):
                        completed_count += complete_tree(child)
                return completed_count

            total_completed = 0
            for task in tasks:
                total_completed += complete_tree(task)

            # Check orders for completion
            for task in tasks:
                if task.created_from_order:
                    order = task.created_from_order
                    if (
                        not order.production_tasks.exclude(status="COMPLETED").exists()
                        and order.status != "READY"
                    ):
                        order.status = "READY"
                        order.save()
                        notify_order_ready(order)

            messages.success(
                request,
                f"Successfully marked {total_completed} tasks (including sub-tasks) as completed.",
            )
        else:
            messages.error(
                request, _("No valid tasks selected or they are already completed.")
            )

    return redirect("industry_reforged:industrialist_dashboard")


@login_required
@permission_required("industry_reforged.basic_access")
def industrialist_leaderboard(request: WSGIRequest) -> HttpResponse:
    """Leaderboard and History view"""
    # Django
    from django.db.models import Count, Sum

    # Leaderboard by points (gamification_value)
    leaderboard_isk = (
        ProductionTask.objects.filter(status="COMPLETED")
        .values("assigned_to__character_name")
        .annotate(total_isk=Sum("gamification_value"), tasks=Count("id"))
        .order_by("-total_isk")[:25]
    )

    # Leaderboard by volume
    leaderboard_vol = (
        ProductionTask.objects.filter(status="COMPLETED")
        .values("assigned_to__character_name")
        .annotate(total_isk=Sum("gamification_value"), tasks=Count("id"))
        .order_by("-tasks")[:25]
    )

    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    personal_history = ProductionTask.objects.filter(
        status="COMPLETED", assigned_to_id__in=user_characters
    ).order_by("-completed_at")

    context = {
        "title": "Industrialist Leaderboards",
        "leaderboard_isk": leaderboard_isk,
        "leaderboard_vol": leaderboard_vol,
        "personal_history": personal_history,
    }
    return render(request, "industry_reforged/industrialist_leaderboard.html", context)


# ==============================================================================
# Domain 3: Director Control Panel
# ==============================================================================


@login_required
@permission_required("industry_reforged.corp_access")
def trigger_inventory_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger Corporate Inventory sync"""

    task_sync_corp_inventory.delay()
    messages.success(
        request,
        _(
            "Corporate Inventory sync has been queued in the background. Please refresh in a few minutes."
        ),
    )
    return redirect("industry_reforged:director_inventory")


@login_required
@permission_required("industry_reforged.corp_access")
def director_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main dashboard for Directors to manage orders and jobs."""
    # Django
    from django.db.models import Count, Sum

    from .models import BuilderPayoutBatch

    # We show orders for characters in the director's corps
    all_orders = MemberOrder.objects.filter(parent_order__isnull=True).order_by(
        "-created_at"
    )
    all_tasks = ProductionTask.objects.all().order_by("-created_at")

    payout_tasks = (
        ProductionTask.objects.filter(
            status="COMPLETED", builder_reward__gt=0, payout_batch__isnull=True
        )
        .select_related("assigned_to", "item_type")
        .order_by("-completed_at")[:200]
    )

    payout_summary = (
        ProductionTask.objects.filter(
            status="COMPLETED", builder_reward__gt=0, payout_batch__isnull=True
        )
        .values("assigned_to__id", "assigned_to__character_name")
        .annotate(total_reward=Sum("builder_reward"), task_count=Count("id"))
        .order_by("-total_reward")
    )

    payout_batches = BuilderPayoutBatch.objects.all().order_by("-created_at")

    context = {
        "title": "Director Control Panel",
        "all_orders": all_orders,
        "all_tasks": all_tasks,
        "payout_tasks": payout_tasks,
        "payout_summary": payout_summary,
        "payout_batches": payout_batches,
    }
    return render(request, "industry_reforged/director_dashboard.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def mark_order_delivered(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Mark an order as DELIVERED and notify the buyer."""
    if request.method == "POST":
        order = get_object_or_404(MemberOrder, id=order_id)
        if order.status == "READY":
            order.status = "DELIVERED"
            order.save()
            messages.success(request, f"Order #{order.id} marked as DELIVERED.")

            # Notify the buyer
            # Alliance Auth
            from allianceauth.notifications.models import Notification

            user = None
            try:
                user = order.character.character_ownership.user
            except Exception:
                pass

            if user:
                Notification.objects.notify_user(
                    user=user,
                    title=f"Order #{order.id} Delivered!",
                    message=f"Your order #{order.id} for {order.total_price} ISK has been contracted to you in-game.",
                    level="success",
                )
        else:
            messages.error(request, "Order must be in READY state to be delivered.")
    return redirect(reverse("industry_reforged:director_dashboard") + "#orders-pane")


@login_required
@permission_required("industry_reforged.corp_access")
def mark_order_paid(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Manually process payment (partial or full) and optional notes."""
    if request.method == "POST":
        order = get_object_or_404(MemberOrder, id=order_id)
        if not order.is_paid:
            amount_str = request.POST.get("amount")
            note_str = request.POST.get("note", "").strip()

            # Standard Library
            from decimal import Decimal

            # Django
            from django.utils import timezone

            try:
                if amount_str:
                    amount = Decimal(amount_str.replace(",", "."))
                else:
                    # Default to remaining if not provided
                    amount = order.total_price - order.amount_paid
            except (ValueError, TypeError, ArithmeticError):
                messages.error(request, "Invalid amount provided.")
                return redirect(
                    reverse("industry_reforged:director_dashboard") + "#orders-pane"
                )

            if amount > 0:
                order.amount_paid += amount

            if note_str or amount > 0:
                ts = timezone.now().strftime("%Y-%m-%d %H:%M")
                log_note = f"[{ts}] Manual Entry: "
                if amount > 0:
                    log_note += f"Processed {amount:,.2f} ISK. "
                if note_str:
                    log_note += f"Note: {note_str}"

                if order.notes:
                    order.notes += f"\n{log_note}"
                else:
                    order.notes = log_note

            if order.amount_paid >= order.total_price:
                order.is_paid = True

            order.save()
            messages.success(
                request,
                f"Order #{order.id} ({order.payment_reference}) payment updated.",
            )
        else:
            messages.error(request, "Order is already fully paid.")
    return redirect(reverse("industry_reforged:director_dashboard") + "#orders-pane")


@login_required
@permission_required("industry_reforged.corp_access")
def generate_payout_batch(request: WSGIRequest) -> HttpResponse:
    """Generate a BuilderPayoutBatch for a specific builder."""
    if request.method == "POST":
        builder_id = request.POST.get("builder_id")

        # Django
        from django.db.models import Sum
        from django.utils.crypto import get_random_string

        from .models import BuilderPayoutBatch, EveCharacter

        builder = get_object_or_404(EveCharacter, id=builder_id)

        # Get tasks
        tasks = ProductionTask.objects.filter(
            status="COMPLETED",
            assigned_to=builder,
            builder_reward__gt=0,
            payout_batch__isnull=True,
        )

        if not tasks.exists():
            messages.warning(
                request, f"No pending payouts found for {builder.character_name}."
            )
            return redirect(
                reverse("industry_reforged:director_dashboard") + "#payouts-pane"
            )

        total_amount = tasks.aggregate(total=Sum("builder_reward"))["total"]

        # Generate random unique ref like PAY-ABCD-1234
        ref = "PAY-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()

        # Assuming the director's corp is paying. We'll just take the first corporation for now.
        # Ideally, it's the corp of the order or the director's corp.
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        if not corporation:
            messages.error(
                request, "You are not part of a corporation to create payouts."
            )
            return redirect(
                reverse("industry_reforged:director_dashboard") + "#payouts-pane"
            )

        batch = BuilderPayoutBatch.objects.create(
            corporation=corporation,
            builder=builder,
            total_amount=total_amount,
            payment_reference=ref,
            status="PENDING",
        )

        # Assign tasks to batch
        tasks.update(payout_batch=batch)
        messages.success(
            request,
            f"Generated Payout Batch for {builder.character_name} with reference: {ref}",
        )

    return redirect(reverse("industry_reforged:director_dashboard") + "#payouts-pane")


@login_required
@permission_required("industry_reforged.corp_access")
def mark_payout_batch_paid(request: WSGIRequest, batch_id: int) -> HttpResponse:
    """Manually mark a BuilderPayoutBatch as paid."""
    from .models import BuilderPayoutBatch

    if request.method == "POST":
        batch = get_object_or_404(BuilderPayoutBatch, id=batch_id)
        if batch.status == "PENDING":
            batch.status = "PAID"
            batch.paid_at = timezone.now()
            batch.save()
            messages.success(
                request, f"Payout Batch {batch.payment_reference} marked as PAID."
            )
        else:
            messages.error(request, "Batch is already paid.")
    return redirect(reverse("industry_reforged:director_dashboard") + "#payouts-pane")


@login_required
@permission_required("industry_reforged.corp_access")
def director_inventory(request: WSGIRequest) -> HttpResponse:
    """Inventory and Analytics for Directors."""
    # Django
    from django.db.models import Sum

    inventory = (
        CorpInventory.objects.filter(quantity__gt=0)
        .values("item_type__name", "item_type__id")
        .annotate(total_qty=Sum("quantity"))
    )

    configs = CorpItemConfig.objects.filter(target_threshold__gt=0)
    low_stock = []

    inv_dict = {item["item_type__id"]: item["total_qty"] for item in inventory}

    for config in configs:
        current_qty = inv_dict.get(config.item_type.id, 0)
        if current_qty < config.target_threshold:
            low_stock.append(
                {
                    "item_type": config.item_type,
                    "current_qty": current_qty,
                    "target": config.target_threshold,
                    "deficit": config.target_threshold - current_qty,
                }
            )

    from .models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)
    facility_inventories = []

    for facility in facilities:
        invs = (
            CorpInventory.objects.filter(
                location_id=facility.facility_id, quantity__gt=0
            )
            .values("item_type__name", "item_type__id")
            .annotate(total_qty=Sum("quantity"))
        )
        if invs:
            facility_inventories.append({"facility": facility, "inventory": invs})

    context = {
        "title": "Director Inventory & Analytics",
        "inventory": inventory,
        "low_stock": low_stock,
        "facility_inventories": facility_inventories,
    }
    return render(request, "industry_reforged/director_inventory.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def director_config(request: WSGIRequest) -> HttpResponse:
    """Mass edit form for Item Configurations."""

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:index")

    item_configs = CorpItemConfig.objects.all().select_related(
        "corporation", "item_type"
    )
    pricing_configs = CorpPricingConfig.objects.all().select_related("corporation")
    type_discounts = CorpTypeDiscount.objects.all().select_related(
        "config__corporation", "eve_type"
    )
    tax_configs = TaxConfig.objects.all().select_related("corporation")
    task_logs = TaskExecutionLog.objects.all().order_by("task_name")

    from .models import IndustryFacility

    facilities = IndustryFacility.objects.filter(is_production_facility=True)

    context = {
        "title": "Configurations",
        "configs": item_configs,
        "pricing_configs": pricing_configs,
        "type_discounts": type_discounts,
        "tax_configs": tax_configs,
        "task_logs": task_logs,
        "facilities": facilities,
    }
    return render(request, "industry_reforged/director_config.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_structure_toggle(
    request: WSGIRequest, facility_id: int
) -> HttpResponse:
    """Toggle the sync_inventory flag for an Industry Facility."""
    # Django
    from django.shortcuts import get_object_or_404

    from .models import IndustryFacility

    facility = get_object_or_404(IndustryFacility, facility_id=facility_id)
    facility.sync_inventory = not facility.sync_inventory
    facility.save()

    status = "enabled" if facility.sync_inventory else "disabled"
    messages.success(request, f"Inventory sync for {facility.name} has been {status}.")
    return redirect(reverse("industry_reforged:director_config") + "#facilities")


@login_required
@permission_required("industry_reforged.corp_access")
def director_wallets(request: WSGIRequest) -> HttpResponse:
    """Corporate Wallets and Transactions"""

    # We show wallets for the first configured corp for simplicity, or all user corps
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )

    divisions = CorpWalletDivision.objects.filter(
        corporation__corporation_id__in=user_corps
    ).order_by("division")

    # Filter journals (default to first division if any)
    selected_division_id = request.GET.get("division")
    if selected_division_id:
        journals = CorpWalletJournal.objects.filter(
            division_id=selected_division_id
        ).order_by("-date")[:500]
    else:
        # Just show the first division's journals by default
        first_div = divisions.first()
        if first_div:
            journals = CorpWalletJournal.objects.filter(division=first_div).order_by(
                "-date"
            )[:500]
            selected_division_id = first_div.id
        else:
            journals = []

    context = {
        "title": "Corporate Wallets",
        "divisions": divisions,
        "journals": journals,
        "selected_division_id": (
            int(selected_division_id) if selected_division_id else None
        ),
    }
    return render(request, "industry_reforged/director_wallets.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def trigger_wallet_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger Wallet sync"""

    task_sync_corp_wallets.delay()
    messages.success(
        request,
        _(
            "Corporate Wallet sync has been queued in the background. Please refresh in a few minutes."
        ),
    )
    return redirect("industry_reforged:director_wallets")


# Django


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_item_edit(
    request: WSGIRequest, config_id: int = None
) -> HttpResponse:
    from .models import CorpItemConfig

    if config_id:
        instance = get_object_or_404(CorpItemConfig, id=config_id)
    else:
        instance = CorpItemConfig()

    if request.method == "POST":
        form = CorpItemConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Item configuration saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#items")
    else:
        form = CorpItemConfigForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": (
                _("Edit Item Configuration")
                if config_id
                else _("Add Item Configuration")
            ),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#items",
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_item_delete(request: WSGIRequest, config_id: int) -> HttpResponse:
    from .models import CorpItemConfig

    config = get_object_or_404(CorpItemConfig, id=config_id)
    config.delete()
    messages.success(request, _("Item configuration deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#items")


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_pricing_edit(
    request: WSGIRequest, config_id: int = None
) -> HttpResponse:
    if config_id:
        instance = get_object_or_404(CorpPricingConfig, id=config_id)
    else:
        instance = CorpPricingConfig()

    if request.method == "POST":
        form = CorpPricingConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Global pricing configuration saved."))
            return redirect(reverse("industry_reforged:director_config") + "#pricing")
    else:
        form = CorpPricingConfigForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": (
                _("Edit Corporation Pricing")
                if config_id
                else _("Add Corporation Pricing")
            ),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#pricing",
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_discount_edit(
    request: WSGIRequest, discount_id: int = None
) -> HttpResponse:
    if discount_id:
        instance = get_object_or_404(CorpTypeDiscount, id=discount_id)
    else:
        instance = CorpTypeDiscount()

    if request.method == "POST":
        form = CorpTypeDiscountForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Type discount saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#discounts")
    else:
        form = CorpTypeDiscountForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": _("Edit Type Discount") if discount_id else _("Add Type Discount"),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#discounts",
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_discount_delete(
    request: WSGIRequest, discount_id: int
) -> HttpResponse:
    discount = get_object_or_404(CorpTypeDiscount, id=discount_id)
    discount.delete()
    messages.success(request, _("Type discount deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#discounts")


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_tax_edit(
    request: WSGIRequest, config_id: int = None
) -> HttpResponse:
    from .forms import TaxConfigForm
    from .models import TaxConfig

    if config_id:
        instance = get_object_or_404(TaxConfig, id=config_id)
    else:
        instance = TaxConfig()

    if request.method == "POST":
        form = TaxConfigForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("System taxes saved successfully."))
            return redirect(reverse("industry_reforged:director_config") + "#pricing")
    else:
        form = TaxConfigForm(instance=instance)

    return render(
        request,
        "industry_reforged/director_config_form.html",
        {
            "title": _("Edit System Taxes") if config_id else _("Add System Taxes"),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#pricing",
        },
    )


def get_corporate_structures_for_dropdown(corporation):
    # Third Party
    import requests

    # Alliance Auth
    from esi.models import Token

    from .models import CorporationSyncConfig

    if not corporation:
        return []

    sync_config = CorporationSyncConfig.objects.filter(corporation=corporation).first()
    if not sync_config:
        return []

    token = Token.objects.filter(
        character_id=sync_config.sync_character.character_id,
        scopes__name="esi-corporations.read_structures.v1",
    ).first()

    if not token:
        return []

    url = f"https://esi.evetech.net/latest/corporations/{corporation.corporation_id}/structures/?datasource=tranquility"
    headers = {
        "Authorization": f"Bearer {token.valid_access_token()}",
        "Accept": "application/json",
    }
    from .models import IndustryFacility

    structures = []

    production_facility_ids = set(
        IndustryFacility.objects.filter(is_production_facility=True).values_list(
            "facility_id", flat=True
        )
    )

    # First, fetch from ESI (which gives us structures the corp actually owns/rents)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            valid_types = {35825, 35826, 35827, 35832, 35833, 35835, 35836, 35834}
            for st in resp.json():
                if (
                    st.get("type_id") in valid_types
                    and st["structure_id"] not in production_facility_ids
                ):
                    structures.append(
                        {
                            "id": st["structure_id"],
                            "name": st["name"],
                            "type_id": st["type_id"],
                            "system_id": st["system_id"],
                        }
                    )
    except Exception:
        pass

    # Second, include any discovered non-production facilities
    known_facility_ids = {s["id"] for s in structures}
    for fac in IndustryFacility.objects.filter(is_production_facility=False):
        if fac.facility_id not in known_facility_ids:
            structures.append(
                {
                    "id": fac.facility_id,
                    "name": fac.name,
                    "type_id": fac.type_id or "",
                    "system_id": fac.solar_system_id or "",
                }
            )
            known_facility_ids.add(fac.facility_id)

    return structures


@login_required
@permission_required("industry_reforged.corp_access")
def add_facility(request: WSGIRequest) -> HttpResponse:
    from .forms import IndustryFacilityForm, IndustryFacilityRigFormSet

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None
    corp_structures = get_corporate_structures_for_dropdown(corporation)

    if request.method == "POST":
        # Check if the facility already exists in the database
        facility_id = request.POST.get("facility_id")
        instance = None
        if facility_id:
            from .models import IndustryFacility

            try:
                existing_facility = IndustryFacility.objects.get(pk=facility_id)
                # Only use the instance if it's NOT already a production facility
                if not existing_facility.is_production_facility:
                    instance = existing_facility
            except IndustryFacility.DoesNotExist:
                pass

        form = IndustryFacilityForm(request.POST, instance=instance)
        if form.is_valid():
            facility = form.save()
            formset = IndustryFacilityRigFormSet(request.POST, instance=facility)
            if formset.is_valid():
                formset.save()
                messages.success(request, _("Facility added successfully."))

                # Automatically sync rigs in the background
                from .tasks import sync_facility_rigs

                sync_facility_rigs.delay()

                return redirect(
                    reverse("industry_reforged:director_config") + "#facilities"
                )
            else:
                # If it was a pre-existing facility that we were updating, revert the flag.
                # If it was a completely new facility, delete it.
                if instance:
                    facility.is_production_facility = False
                    facility.save()
                else:
                    facility.delete()
        else:
            formset = IndustryFacilityRigFormSet(request.POST)
    else:
        form = IndustryFacilityForm()
        formset = IndustryFacilityRigFormSet()

    return render(
        request,
        "industry_reforged/manage_facility.html",
        {
            "form": form,
            "formset": formset,
            "corp_structures": corp_structures,
            "title": _("Add Production Facility"),
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def edit_facility(request: WSGIRequest, facility_id: int) -> HttpResponse:
    from .forms import IndustryFacilityForm, IndustryFacilityRigFormSet
    from .models import IndustryFacility

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None
    corp_structures = get_corporate_structures_for_dropdown(corporation)

    facility = get_object_or_404(IndustryFacility, pk=facility_id)
    if request.method == "POST":
        form = IndustryFacilityForm(request.POST, instance=facility)
        formset = IndustryFacilityRigFormSet(request.POST, instance=facility)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _("Facility updated successfully."))

            # Automatically sync rigs in the background
            from .tasks import sync_facility_rigs

            sync_facility_rigs.delay()

            return redirect(
                reverse("industry_reforged:director_config") + "#facilities"
            )
    else:
        form = IndustryFacilityForm(instance=facility)
        formset = IndustryFacilityRigFormSet(instance=facility)

    return render(
        request,
        "industry_reforged/manage_facility.html",
        {
            "form": form,
            "formset": formset,
            "facility": facility,
            "corp_structures": corp_structures,
            "title": _("Edit Production Facility"),
        },
    )


@login_required
@permission_required("industry_reforged.corp_access")
def delete_facility(request: WSGIRequest, facility_id: int) -> HttpResponse:
    from .models import IndustryFacility

    if request.method == "POST":
        facility = get_object_or_404(IndustryFacility, pk=facility_id)
        facility.delete()
        messages.success(request, _("Facility deleted successfully."))
    return redirect(reverse("industry_reforged:director_config") + "#facilities")
