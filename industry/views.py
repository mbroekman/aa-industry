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
    from .models import MemberOrder

    order = MemberOrder.objects.filter(
        id=order_id, character_id__in=user_characters, status="QUOTED"
    ).first()

    if order:
        order.status = "ACCEPTED"
        order.save()
        messages.success(request, "Quote accepted! Your order is now in progress.")
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
