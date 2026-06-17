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
@token_required(scopes=["esi-industry.read_corporation_jobs.v1"])
def add_corporate_token(request: WSGIRequest, token) -> HttpResponse:
    """View to request a corporate token"""
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
    # Django
    from django.db.models import Sum

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
