"""App Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from ..models import (
    CharacterIndustryJob,
    CharacterPlanet,
    CorporationIndustryJob,
    MemberOrder,
)


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
