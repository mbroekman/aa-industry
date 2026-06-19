"""App Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render

# Alliance Auth
from esi.decorators import token_required

from .models import CharacterIndustryJob, CharacterPlanet, CorporationIndustryJob
from .tasks import update_character_pi


@login_required
@permission_required("industry.basic_access")
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view
    """
    return personal_dashboard(request)


@login_required
@permission_required("industry.basic_access")
def personal_dashboard(request: WSGIRequest) -> HttpResponse:
    """Personal Dashboard View"""
    # Fetch all jobs for the current user's characters
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    jobs = CharacterIndustryJob.objects.filter(
        character_id__in=user_characters
    ).select_related("blueprint_type", "product_type", "character")

    # Fetch PI Planets
    planets = (
        CharacterPlanet.objects.filter(character_id__in=user_characters)
        .select_related("character", "planet_type")
        .prefetch_related("pins", "pins__type", "pins__product_type")
        .order_by("character__character_name", "planet_id")
    )

    context = {"jobs": jobs, "planets": planets, "title": "Personal Industry Dashboard"}
    return render(request, "industry/personal_dashboard.html", context)


@login_required
@permission_required("industry.corp_access")
def corporate_dashboard(request: WSGIRequest) -> HttpResponse:
    """Corporate Dashboard View"""
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )
    jobs = CorporationIndustryJob.objects.filter(
        corporation__corporation_id__in=user_corps
    ).select_related("blueprint_type", "product_type", "installer", "corporation")

    context = {"jobs": jobs, "title": "Corporate Industry Dashboard"}
    return render(request, "industry/corporate_dashboard.html", context)


@login_required
@token_required(
    scopes=["esi-industry.read_character_jobs.v1", "esi-planets.manage_planets.v1"]
)
def add_personal_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a personal token"""
    return redirect("industry:personal_dashboard")


@login_required
@token_required(
    scopes=[
        "esi-industry.read_corporation_jobs.v1",
        "esi-assets.read_corporation_assets.v1",
        "esi-universe.read_structures.v1",
        "esi-corporations.read_structures.v1",
    ]
)
def add_corporate_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a corporate token"""
    # After granting, redirect back to the page the user came from or the director dashboard
    referer = request.headers.get("referer")
    if referer and "director" in referer:
        return redirect("industry:director_config")
    return redirect("industry:corporate_dashboard")


@login_required
@permission_required("industry.basic_access")
def trigger_pi_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger PI sync for all characters of the user"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character__character_id", flat=True
    )
    for char_id in user_characters:
        update_character_pi.delay(character_id=char_id)

    messages.success(
        request,
        "Planetary Interaction sync has been queued in the background. Please refresh in a few minutes.",
    )
    return redirect("industry:personal_dashboard")


@login_required
@permission_required("industry.basic_access")
def orders_dashboard(request: WSGIRequest) -> HttpResponse:
    """Member Orders Dashboard"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    from .models import MemberOrder

    orders = MemberOrder.objects.filter(character_id__in=user_characters).order_by(
        "-created_at"
    )

    context = {"orders": orders, "title": "My Orders"}
    return render(request, "industry/orders_dashboard.html", context)


@login_required
@permission_required("industry.basic_access")
def create_order(request: WSGIRequest) -> HttpResponse:
    """Create a new order from EFT fit or single items"""
    if request.method == "POST":
        fit_text = request.POST.get("fit_text", "").strip()
        character_id = request.POST.get("character_id")

        if not fit_text or not character_id:
            messages.error(request, "Please provide an EFT fit and select a character.")
            return redirect("industry:create_order")

        # Alliance Auth
        from allianceauth.eveonline.models import EveCharacter

        character = EveCharacter.objects.filter(
            character_id=character_id, character_ownership__user=request.user
        ).first()
        if not character:
            messages.error(request, "Invalid character selected.")
            return redirect("industry:create_order")

        from .models import MemberOrder, OrderFit, OrderItem
        from .utils.fit_parser import parse_fit_text
        from .utils.pricing_engine import calculate_quote

        parsed_items, unrecognized = parse_fit_text(fit_text)

        if unrecognized:
            messages.warning(
                request,
                f"Could not recognize the following items: {', '.join(unrecognized)}",
            )

        if not parsed_items:
            messages.error(request, "No valid items found in the fit.")
            return redirect("industry:create_order")

        # Optional: Apply corp discount if user's main character is in a corp with config
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        total_price, item_details = calculate_quote(parsed_items, corporation)

        order = MemberOrder.objects.create(
            character=character, status="QUOTED", total_price=total_price
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

        messages.success(request, "Order parsed and quoted successfully!")
        return redirect("industry:view_quote", order_id=order.id)

    characters = request.user.character_ownerships.all().select_related("character")
    context = {"title": "Create Order", "characters": [c.character for c in characters]}
    return render(request, "industry/create_order.html", context)


@login_required
@permission_required("industry.basic_access")
def view_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    """View details of a quote/order"""
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    from .models import MemberOrder

    order = MemberOrder.objects.filter(
        id=order_id, character_id__in=user_characters
    ).first()

    if not order:
        messages.error(request, "Order not found or access denied.")
        return redirect("industry:orders_dashboard")

    context = {"title": f"Order #{order.id}", "order": order}
    return render(request, "industry/view_quote.html", context)


@login_required
@permission_required("industry.basic_access")
def accept_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    from .models import MemberOrder, ProductionTask

    order = MemberOrder.objects.filter(
        id=order_id, character_id__in=user_characters, status="QUOTED"
    ).first()

    if order:
        order.status = "ACCEPTED"
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

        messages.success(
            request,
            "Quote accepted! Your order is now in progress and tasks have been generated for builders.",
        )
    return redirect("industry:orders_dashboard")


@login_required
@permission_required("industry.basic_access")
def reject_quote(request: WSGIRequest, order_id: int) -> HttpResponse:
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )
    from .models import MemberOrder

    order = MemberOrder.objects.filter(
        id=order_id, character_id__in=user_characters, status="QUOTED"
    ).first()

    if order:
        order.status = "REJECTED"
        order.save()
        messages.info(request, "Quote rejected and order cancelled.")
    return redirect("industry:orders_dashboard")


@login_required
@permission_required("industry.industrialist_access")
def industrialist_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main execution dashboard for industrialists"""

    from .models import CorpMOTD, CorporationIndustryJob, ProductionTask

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

    context = {
        "title": "Industrialist Dashboard",
        "motd": motd,
        "unclaimed_tasks": unclaimed_tasks,
        "my_tasks": my_tasks,
        "my_completed_tasks": my_completed_tasks,
        "corp_active_jobs": corp_active_jobs,
    }
    return render(request, "industry/industrialist_dashboard.html", context)


@login_required
@permission_required("industry.industrialist_access")
def claim_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        character_id = request.POST.get("character_id")
        # Alliance Auth
        from allianceauth.eveonline.models import EveCharacter

        from .models import ProductionTask

        character = EveCharacter.objects.filter(
            character_id=character_id, character_ownership__user=request.user
        ).first()
        if not character:
            messages.error(request, "Invalid character selected.")
            return redirect("industry:industrialist_dashboard")

        task = ProductionTask.objects.filter(id=task_id, status="UNCLAIMED").first()
        if task:
            # Django
            from django.utils import timezone

            task.status = "IN_PRODUCTION"
            task.assigned_to = character
            task.assigned_at = timezone.now()
            task.save()
            messages.success(
                request, f"Successfully claimed {task.quantity}x {task.item_type.name}."
            )
        else:
            messages.error(request, "Task is no longer available or does not exist.")

    return redirect("industry:industrialist_dashboard")


@login_required
@permission_required("industry.industrialist_access")
def complete_task(request: WSGIRequest, task_id: int) -> HttpResponse:
    if request.method == "POST":
        user_characters = request.user.character_ownerships.all().values_list(
            "character_id", flat=True
        )
        from .models import ProductionTask

        task = ProductionTask.objects.filter(
            id=task_id, assigned_to_id__in=user_characters, status="IN_PRODUCTION"
        ).first()
        if task:
            # Django
            from django.utils import timezone

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
            messages.error(request, "Task not found or not assigned to you.")

    return redirect("industry:industrialist_dashboard")


@login_required
@permission_required("industry.industrialist_access")
def industrialist_leaderboard(request: WSGIRequest) -> HttpResponse:
    """Leaderboard and History view"""
    # Django
    from django.db.models import Count, Sum

    from .models import ProductionTask

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
    return render(request, "industry/industrialist_leaderboard.html", context)


# ==============================================================================
# Domain 3: Director Control Panel
# ==============================================================================


@login_required
@permission_required("industry.corp_access")
def trigger_inventory_sync(request: WSGIRequest) -> HttpResponse:
    """Manually trigger Corporate Inventory sync"""
    from .tasks import task_sync_corp_inventory

    task_sync_corp_inventory.delay()
    messages.success(
        request,
        "Corporate Inventory sync has been queued in the background. Please refresh in a few minutes.",
    )
    return redirect("industry:director_inventory")


@login_required
@permission_required("industry.corp_access")
def director_dashboard(request: WSGIRequest) -> HttpResponse:
    """Main dashboard for Directors to manage orders and jobs."""
    from .models import MemberOrder, ProductionTask

    # We show orders for characters in the director's corps
    all_orders = MemberOrder.objects.all().order_by("-created_at")
    all_tasks = ProductionTask.objects.all().order_by("-created_at")

    context = {
        "title": "Director Control Panel",
        "all_orders": all_orders,
        "all_tasks": all_tasks,
    }
    return render(request, "industry/director_dashboard.html", context)


@login_required
@permission_required("industry.corp_access")
def director_inventory(request: WSGIRequest) -> HttpResponse:
    """Inventory and Analytics for Directors."""
    # Django
    from django.db.models import Sum

    from .models import CorpInventory, CorpItemConfig

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
    return render(request, "industry/director_inventory.html", context)


@login_required
@permission_required("industry.corp_access")
def director_config(request: WSGIRequest) -> HttpResponse:
    """Mass edit form for Item Configurations."""
    from .models import CorpItemConfig

    configs = CorpItemConfig.objects.all()

    context = {"title": "Item Configurations", "configs": configs}
    return render(request, "industry/director_config.html", context)


@login_required
@permission_required("industry.corp_access")
def director_discover_hangars(request: WSGIRequest) -> HttpResponse:
    """Tool to discover corporate hangars by scanning the first few pages of assets."""
    # Alliance Auth
    from esi.models import Token

    from .models import CorpHangarConfig, CorporationSyncConfig

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None

    if not corporation:
        messages.error(request, "You are not part of a corporation.")
        return redirect("industry:director_config")

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
        return redirect("industry:director_discover_hangars")

    sync_config = CorporationSyncConfig.objects.filter(corporation=corporation).first()
    if not sync_config:
        messages.warning(
            request,
            "No corporate sync configuration found. Please add a corporate token first.",
        )
        return redirect("industry:director_config")

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
            "Corporate sync character does not have the required asset and structure scopes. Please add a new corporate token.",
        )
        return redirect("industry:director_config")

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
        messages.error(request, f"Failed to fetch assets via ESI: {e}")

    context = {"discovered_hangars": discovered_hangars}
    return render(request, "industry/director_discover_hangars.html", context)
