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
from esi.models import Token

from .forms import (
    CorpItemConfigForm,
    CorpPricingConfigForm,
    CorpTypeDiscountForm,
)
from .models import (
    CharacterIndustryJob,
    CharacterPlanet,
    CorpHangarConfig,
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
    TaxConfig,
)
from .tasks import task_sync_corp_inventory, task_sync_corp_wallets, update_character_pi
from .utils.bom_engine import (
    calculate_order_bom,
    calculate_recursive_order_bom,
    calculate_tasks_bom,
    get_fuzzwork_bom,
)
from .utils.discord import send_discord_webhook
from .utils.fit_parser import parse_fit_text
from .utils.pricing_engine import calculate_quote, get_prices_with_overrides


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

    attention_chars = set()
    for planet in planets:
        if planet.has_expired_extractors:
            attention_chars.add(planet.character_id)

    for planet in planets:
        planet.character_needs_attention = planet.character_id in attention_chars

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

    orders = MemberOrder.objects.filter(character_id__in=user_characters).order_by(
        "-created_at"
    )

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

    if order_ids:
        orders = MemberOrder.objects.filter(
            id__in=order_ids, character_id__in=user_characters
        )
        for order in orders:
            order_bom = calculate_order_bom(order)
            for mat_id, data in order_bom.items():
                if mat_id in bom:
                    bom[mat_id]["quantity"] += data["quantity"]
                else:
                    bom[mat_id] = data

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

        task_bom = calculate_tasks_bom(tasks, corp_info=corp_info)
        for mat_id, data in task_bom.items():
            if mat_id in bom:
                bom[mat_id]["quantity"] += data["quantity"]
            else:
                bom[mat_id] = data

    if type_id and quantity:
        quantity = int(quantity)
        # Standard Library
        import math

        materials, yield_qty = get_fuzzwork_bom(type_id)
        runs = math.ceil(quantity / yield_qty) if yield_qty > 0 else quantity

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

    total_bom_price = 0
    sorted_bom = []
    if bom:
        mat_ids = list(bom.keys())

        corp_info = None
        main_char = request.user.profile.main_character
        if main_char and main_char.corporation:
            corp_info = main_char.corporation

        prices = get_prices_with_overrides(mat_ids, corp_info)
        for mat_id, data in bom.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]

        sorted_bom = sorted(bom.values(), key=lambda x: x["name"])

    context = {
        "title": "Consolidated Shopping List",
        "orders": orders,
        "tasks": tasks,
        "custom_item_name": item_name,
        "custom_item_quantity": quantity,
        "bom_materials": sorted_bom,
        "total_bom_price": total_bom_price,
    }
    return render(request, "industry_reforged/shopping_list.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
def create_order(request: WSGIRequest) -> HttpResponse:
    """Create a new order from EFT fit or single items"""
    if request.method == "POST":
        fit_text = request.POST.get("fit_text", "").strip()
        character_id = request.POST.get("character_id")

        if not fit_text or not character_id:
            messages.error(
                request, _("Please provide an EFT fit and select a character.")
            )
            return redirect("industry_reforged:create_order")

        character = EveCharacter.objects.filter(
            character_id=character_id, character_ownership__user=request.user
        ).first()
        if not character:
            messages.error(request, _("Invalid character selected."))
            return redirect("industry_reforged:create_order")

        parsed_items, unrecognized = parse_fit_text(fit_text)

        if unrecognized:
            messages.warning(
                request,
                f"Could not recognize the following items: {', '.join(unrecognized)}",
            )

        if not parsed_items:
            messages.error(request, _("No valid items found in the fit."))
            return redirect("industry_reforged:create_order")

        # Optional: Apply corp discount if user's main character is in a corp with config
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        total_price, item_details = calculate_quote(parsed_items, corporation)

        order = MemberOrder.objects.create(
            character=character, status="REQUESTED", total_price=total_price
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

        # Discord Webhook Notification
        if corporation:
            webhook_config = CorporationWebhookConfig.objects.filter(
                corporation=corporation
            ).first()
            if webhook_config and webhook_config.orders_webhook:
                embed = {
                    "title": f"New Quote Requested: Order #{order.id}",
                    "description": f"**{character.character_name}** has requested a quote.",
                    "color": 3447003,  # Blue
                    "fields": [
                        {
                            "name": "Total Quoted Price",
                            "value": f"{total_price:,.2f} ISK",
                            "inline": False,
                        }
                    ],
                }
                send_discord_webhook(webhook_config.orders_webhook, embed)

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
    main_char = request.user.profile.main_character
    if main_char and main_char.corporation:
        corp_info = main_char.corporation

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

        prices = get_prices_with_overrides(mat_ids, corp_info)
        for mat_id, data in bom_materials.items():
            price = prices.get(mat_id, 0)
            data["price_per_unit"] = price
            data["total_price"] = price * data["quantity"]
            total_bom_price += data["total_price"]

    # Calculate original price from items before any discounts
    original_price = sum(item.original_line_total for item in order.items.all())
    savings = float(original_price) - float(order.total_price)

    recursive_bom_tree = []
    if request.user.has_perm(
        "industry_reforged.industrialist_access"
    ) or request.user.has_perm("industry_reforged.corp_access"):
        recursive_bom_tree = calculate_recursive_order_bom(order)

    context = {
        "title": f"Order #{order.id}",
        "order": order,
        "bom_materials": bom_materials.values() if bom_materials else [],
        "total_bom_price": total_bom_price,
        "original_price": original_price,
        "savings": savings,
        "is_owner": order.character_id in user_characters,
        "recursive_bom_tree": recursive_bom_tree,
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

            order.total_price = new_total
            order.status = "QUOTED"

            order.quoted_at = timezone.now()
            order.save()

            # Optionally send a Discord webhook notification here to inform the user
            main_char = request.user.profile.main_character
            corporation = main_char.corporation if main_char else None
            if corporation:
                webhook_config = CorporationWebhookConfig.objects.filter(
                    corporation=corporation
                ).first()
                if webhook_config and webhook_config.orders_webhook:
                    embed = {
                        "title": f"Quote Provided: Order #{order.id}",
                        "description": f"A quote of **{new_total:,.2f} ISK** has been provided for your order. Please review and accept.",
                        "color": 3447003,  # Blue
                    }
                    send_discord_webhook(webhook_config.orders_webhook, embed)

            messages.success(
                request,
                _("Quote of %(total)s ISK submitted successfully.")
                % {"total": f"{new_total:,.2f}"},
            )
        except ValueError:
            messages.error(request, _("Invalid price provided."))

        return redirect("industry_reforged:view_quote", order_id=order.id)

    return redirect("industry_reforged:director_dashboard")


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
        order.status = "ACCEPTED"

        order.accepted_at = timezone.now()
        order.save()

        # Create Production Tasks
        tasks_to_create = []
        for item in order.items.all():
            tasks_to_create.append(
                ProductionTask(
                    item_type=item.item_type,
                    quantity=item.quantity,
                    status="UNCLAIMED",
                    created_from_order=order,
                    gamification_value=item.line_total,
                )
            )
        ProductionTask.objects.bulk_create(tasks_to_create)

        # Discord Webhook Notification
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None
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
        order.status = "REJECTED"
        order.save()

        # Discord Webhook Notification
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None
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
        order = MemberOrder.objects.filter(
            id=order_id, status__in=["REQUESTED", "QUOTED"]
        ).first()
    else:
        order = MemberOrder.objects.filter(
            id=order_id,
            character_id__in=user_characters,
            status__in=["REQUESTED", "QUOTED"],
        ).first()

    if order:
        order.delete()
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

    # Unclaimed tasks
    unclaimed_tasks = ProductionTask.objects.filter(status="UNCLAIMED").order_by(
        "-created_at"
    )

    # My active tasks
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    my_tasks = ProductionTask.objects.filter(
        status="IN_PRODUCTION", assigned_to_id__in=user_characters
    ).order_by("-assigned_at")

    # My completed tasks (limit to recent 10 to avoid clutter)
    my_completed_tasks = ProductionTask.objects.filter(
        status="COMPLETED", assigned_to_id__in=user_characters
    ).order_by("-completed_at")[:10]

    # Active corp jobs (from ESI sync)
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    corp_active_jobs = CorporationIndustryJob.objects.filter(
        corporation__corporation_id__in=user_corps, status="active"
    ).select_related("blueprint_type", "product_type", "installer")

    # Django
    from django.db.models import Sum

    orders_qs = MemberOrder.objects.filter(status__in=["ACCEPTED", "IN_PRODUCTION"])
    dynamic_motd_stats = {
        "orders_in_production": orders_qs.count(),
        "open_tasks": unclaimed_tasks.count(),
        "active_jobs": corp_active_jobs.count(),
        "value_in_progress": orders_qs.aggregate(total=Sum("total_price"))["total"]
        or 0.0,
    }

    context = {
        "title": "Industrialist Dashboard",
        "motd": motd,
        "dynamic_motd_stats": dynamic_motd_stats,
        "unclaimed_tasks": unclaimed_tasks,
        "my_tasks": my_tasks,
        "my_completed_tasks": my_completed_tasks,
        "corp_active_jobs": corp_active_jobs,
    }
    return render(request, "industry_reforged/industrialist_dashboard.html", context)


@login_required
@permission_required("industry_reforged.industrialist_access")
def claim_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        character_id = request.POST.get("character_id")

        character = EveCharacter.objects.filter(
            character_id=character_id, character_ownership__user=request.user
        ).first()
        if not character:
            messages.error(request, _("Invalid character selected."))
            return redirect("industry_reforged:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="UNCLAIMED").first()
        if task:
            task.status = "IN_PRODUCTION"
            task.assigned_to = character
            task.assigned_at = timezone.now()
            task.save()
            messages.success(
                request, f"Successfully claimed {task.quantity}x {task.item_type.name}."
            )
        else:
            messages.error(request, _("Task is no longer available or does not exist."))

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
            task.status = "COMPLETED"
            task.completed_at = timezone.now()
            task.save()

            # Check if all tasks for the order are completed to update MemberOrder status
            if task.created_from_order:
                order = task.created_from_order
                remaining = order.production_tasks.exclude(status="COMPLETED").exists()
                if not remaining:
                    order.status = "READY"
                    order.save()

            messages.success(
                request, f"Marked {task.quantity}x {task.item_type.name} as completed!"
            )
        else:
            messages.error(request, _("Task not found or not assigned to you."))

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

    # We show orders for characters in the director's corps
    all_orders = MemberOrder.objects.all().order_by("-created_at")
    all_tasks = ProductionTask.objects.all().order_by("-created_at")

    context = {
        "title": "Director Control Panel",
        "all_orders": all_orders,
        "all_tasks": all_tasks,
    }
    return render(request, "industry_reforged/director_dashboard.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def director_inventory(request: WSGIRequest) -> HttpResponse:
    """Inventory and Analytics for Directors."""
    # Django
    from django.db.models import Sum

    inventory = CorpInventory.objects.values(
        "item_type__name", "item_type__id"
    ).annotate(total_qty=Sum("quantity"))

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

    context = {
        "title": "Director Inventory & Analytics",
        "inventory": inventory,
        "low_stock": low_stock,
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

    item_configs = CorpItemConfig.objects.filter(corporation=corporation)
    pricing_config, created = CorpPricingConfig.objects.get_or_create(
        corporation=corporation
    )
    type_discounts = CorpTypeDiscount.objects.filter(config=pricing_config)
    tax_config, created_tax = TaxConfig.objects.get_or_create(corporation=corporation)

    context = {
        "title": "Configurations",
        "configs": item_configs,
        "pricing_config": pricing_config,
        "type_discounts": type_discounts,
        "tax_config": tax_config,
    }
    return render(request, "industry_reforged/director_config.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def director_discover_hangars(request: WSGIRequest) -> HttpResponse:
    """Tool to discover corporate hangars by scanning the first few pages of assets."""

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:director_config")

    if request.method == "POST":
        location_id = request.POST.get("location_id")
        flag_id = request.POST.get("flag_id")
        description = request.POST.get("description", f"Discovered Hangar {flag_id}")

        if location_id and flag_id:
            CorpHangarConfig.objects.get_or_create(
                corporation=corporation,
                location_id=int(location_id),
                flag_id=flag_id,
                defaults={"description": description},
            )
            messages.success(
                request, f"Hangar {flag_id} at {location_id} added successfully."
            )
        return redirect("industry_reforged:director_discover_hangars")

    sync_config = CorporationSyncConfig.objects.filter(corporation=corporation).first()
    if not sync_config:
        messages.warning(
            request,
            _(
                "No corporate sync configuration found. Please add a corporate token first."
            ),
        )
        return redirect("industry_reforged:director_config")

    token = (
        Token.objects.filter(
            character_id=sync_config.sync_character.character_id,
            scopes__name="esi-assets.read_corporation_assets.v1",
        )
        .filter(scopes__name="esi-corporations.read_structures.v1")
        .order_by("-pk")
        .first()
    )

    if not token:
        messages.warning(
            request,
            _(
                "Corporate sync character does not have the required asset and structure scopes. Please add a new corporate token."
            ),
        )
        return redirect("industry_reforged:director_config")

    # Standard Library
    from collections import defaultdict

    # Third Party
    import requests

    discovered_hangars = []

    try:
        hangar_counts = defaultdict(int)

        # Use direct requests to avoid django-esi HTTPNotModified cache exceptions for dynamic views
        headers = {
            "Authorization": f"Bearer {token.valid_access_token()}",
            "Accept": "application/json",
        }

        # Fetch first page to get total pages
        url = f"https://esi.evetech.net/latest/corporations/{corporation.corporation_id}/assets/?datasource=tranquility&page=1"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            pages = int(response.headers.get("X-Pages", 1))
            pages = min(pages, 50)  # Cap at 50 pages (50,000 items) to prevent timeouts

            assets = response.json()
            for asset in assets:
                loc_id = asset.get("location_id")
                flag = asset.get("location_flag", "")
                if "Corp" in flag or "Deliveries" in flag or "Hangar" in flag:
                    hangar_counts[(loc_id, flag)] += 1

            # Fetch remaining pages
            for page in range(2, pages + 1):
                page_url = f"https://esi.evetech.net/latest/corporations/{corporation.corporation_id}/assets/?datasource=tranquility&page={page}"
                page_resp = requests.get(page_url, headers=headers)
                if page_resp.status_code == 200:
                    for asset in page_resp.json():
                        loc_id = asset.get("location_id")
                        flag = asset.get("location_flag", "")
                        if "Corp" in flag or "Deliveries" in flag or "Hangar" in flag:
                            hangar_counts[(loc_id, flag)] += 1

        # Fetch Corp Structures first for quick mapping
        corp_str_map = {}
        corp_str_url = f"https://esi.evetech.net/latest/corporations/{corporation.corporation_id}/structures/?datasource=tranquility"
        corp_str_resp = requests.get(corp_str_url, headers=headers)
        if corp_str_resp.status_code == 200:
            for s in corp_str_resp.json():
                corp_str_map[s.get("structure_id")] = s.get("name")

        # Resolve names
        location_names = {}
        unique_locs = list({loc_id for loc_id, _ in hangar_counts.keys()})

        for loc_id in unique_locs:
            try:
                if loc_id < 100000000:
                    st_resp = requests.get(
                        f"https://esi.evetech.net/latest/universe/stations/{loc_id}/?datasource=tranquility"
                    )
                    if st_resp.status_code == 200:
                        location_names[loc_id] = st_resp.json().get("name", str(loc_id))
                    else:
                        location_names[loc_id] = f"Unknown Station ({loc_id})"
                else:
                    if loc_id in corp_str_map:
                        location_names[loc_id] = corp_str_map[loc_id]
                    else:
                        str_resp = requests.get(
                            f"https://esi.evetech.net/latest/universe/structures/{loc_id}/?datasource=tranquility",
                            headers=headers,
                        )
                        if str_resp.status_code == 200:
                            location_names[loc_id] = str_resp.json().get(
                                "name", str(loc_id)
                            )
                        else:
                            location_names[loc_id] = f"Unknown Structure ({loc_id})"
            except Exception:
                location_names[loc_id] = f"Unknown Location ({loc_id})"

        # Check which ones are already configured
        configured = CorpHangarConfig.objects.filter(corporation=corporation)
        configured_keys = {(c.location_id, c.flag_id) for c in configured}

        for (loc_id, flag), count in hangar_counts.items():
            discovered_hangars.append(
                {
                    "location_id": loc_id,
                    "location_name": location_names.get(loc_id, str(loc_id)),
                    "flag_id": flag,
                    "item_count": count,
                    "is_configured": (loc_id, flag) in configured_keys,
                }
            )

        discovered_hangars.sort(key=lambda x: x["item_count"], reverse=True)

    except Exception as e:
        messages.error(
            request, _("Failed to fetch assets via ESI: %(error)s") % {"error": e}
        )

    context = {"discovered_hangars": discovered_hangars}
    return render(request, "industry_reforged/director_discover_hangars.html", context)


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

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:director_config")

    if config_id:
        instance = get_object_or_404(
            CorpItemConfig, id=config_id, corporation=corporation
        )
    else:
        instance = CorpItemConfig(corporation=corporation)

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

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    config = get_object_or_404(CorpItemConfig, id=config_id, corporation=corporation)
    config.delete()
    messages.success(request, _("Item configuration deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#items")


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_pricing_edit(request: WSGIRequest) -> HttpResponse:
    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:director_config")

    instance, created = CorpPricingConfig.objects.get_or_create(corporation=corporation)

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
            "title": _("Edit Global Pricing Configuration"),
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
    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:director_config")

    pricing_config, created = CorpPricingConfig.objects.get_or_create(
        corporation=corporation
    )

    if discount_id:
        instance = get_object_or_404(
            CorpTypeDiscount, id=discount_id, config=pricing_config
        )
    else:
        instance = CorpTypeDiscount(config=pricing_config)

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
    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    pricing_config = get_object_or_404(CorpPricingConfig, corporation=corporation)
    discount = get_object_or_404(
        CorpTypeDiscount, id=discount_id, config=pricing_config
    )
    discount.delete()
    messages.success(request, _("Type discount deleted."))
    return redirect(reverse("industry_reforged:director_config") + "#discounts")


@login_required
@permission_required("industry_reforged.corp_access")
def director_config_tax_edit(request: WSGIRequest) -> HttpResponse:
    from .forms import TaxConfigForm
    from .models import TaxConfig

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, _("You are not part of a corporation."))
        return redirect("industry_reforged:director_config")

    instance, created = TaxConfig.objects.get_or_create(corporation=corporation)

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
            "title": _("Edit System Taxes"),
            "form": form,
            "back_url": "industry_reforged:director_config",
            "back_hash": "#pricing",
        },
    )
